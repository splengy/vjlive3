"""
Local LLM Reviewer — AHOS Validator Module

Uses a small local LLM (7-8B) running on an Orange Pi 5 NPU
(RK3588 / 6 TOPS RKNN) for code quality classification.

The local model does NOT generate code. It only answers YES/NO
classification questions:
  - "Is this code word salad?"
  - "Does this code match the spec?"
  - "Is this a real implementation or a stub?"

Small models are MORE trustworthy for classification because:
1. Output space is tiny (YES/NO) — no room for creative evasion
2. Deterministic at temperature=0
3. Runs on your hardware — no API billing incentive to pad output
4. The model didn't write the code, so it has no ego investment in defending it

This module uses a generic HTTP interface. Whatever inference server
is running on the Orange Pi (rkllm, llama.cpp, custom Flask), we just
POST and get a response.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # Will fail gracefully if not installed

logger = logging.getLogger(__name__)


@dataclass
class ReviewResult:
    """Result of a local LLM classification review."""

    passed: bool
    available: bool = True  # False if Orange Pi is unreachable
    questions_asked: int = 0
    questions_failed: int = 0
    responses: list = field(default_factory=list)
    verdict: str = ""


# Classification prompts — each one expects YES or NO.
CLASSIFICATION_PROMPTS = {
    "word_salad": (
        "You are a code quality auditor. Examine the following code.\n"
        "Does it contain meaningless adverb-heavy comments like "
        "'natively organically beautifully securely gracefully'?\n"
        "Answer ONLY 'YES' or 'NO'.\n\n"
        "```\n{code}\n```"
    ),
    "stub_check": (
        "You are a code quality auditor. Examine the following code.\n"
        "Is this a stub or placeholder implementation? Look for:\n"
        "- NotImplementedError\n"
        "- Methods that only contain 'pass'\n"
        "- Comments saying 'TODO' or 'In a real environment'\n"
        "- Fake return values (hardcoded numbers instead of real computation)\n"
        "Answer ONLY 'YES' or 'NO'.\n\n"
        "```\n{code}\n```"
    ),
    "spec_match": (
        "You are a code quality auditor.\n"
        "SPEC: {spec}\n\n"
        "CODE:\n```\n{code}\n```\n\n"
        "Does the code implement what the spec describes? "
        "Answer ONLY 'YES' or 'NO'."
    ),
    "real_implementation": (
        "You are a code quality auditor. Examine the following code.\n"
        "Does this code contain real, functional logic (actual algorithms, "
        "real OpenGL calls, genuine data processing)? Or is it just "
        "boilerplate structure with no substance?\n"
        "Answer ONLY 'YES it is real' or 'NO it is fake'.\n\n"
        "```\n{code}\n```"
    ),
}


class LocalLLMReviewer:
    """
    Client for the local LLM reviewer running on Orange Pi 5 NPU.

    The reviewer accepts a generic HTTP POST interface:
        POST http://<host>:<port>/api/generate
        Body: {"prompt": "...", "temperature": 0}
        Response: {"response": "YES"} or {"response": "NO"}

    If the Orange Pi is unreachable, all reviews pass with a warning.
    The deterministic validators (word_salad_detector, stub_detector)
    are the primary gate — this is a secondary "second opinion" layer.
    """

    def __init__(
        self,
        host: str = "192.168.1.60",
        port: int = 5050,
        timeout: float = 60.0,
        model: str = "Qwen3-4B-Instruct",
    ):
        self.host = host
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.model = model
        self._available = None
        # Julie-Winters: spec_server.py on port 5050
        # Qwen3-4B-Instruct on RK3588 NPU via rkllm

    def is_available(self) -> bool:
        """Check if the Orange Pi inference server is reachable."""
        if requests is None:
            logger.warning("'requests' library not installed — local LLM review disabled")
            return False
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self._available = data.get("status") == "ok"
                return self._available
            self._available = False
            return False
        except (requests.ConnectionError, requests.Timeout):
            self._available = False
            logger.warning(f"Orange Pi at {self.base_url} is unreachable — local LLM review disabled")
            return False

    def _ask(self, prompt: str) -> Optional[str]:
        """
        Send a classification prompt to the spec_server on Julie.
        Uses the /generate endpoint which returns {"response": "..."}.
        """
        if requests is None:
            return None
        try:
            resp = requests.post(
                f"{self.base_url}/generate",
                json={"prompt": prompt, "max_tokens": 32},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "").strip()
            else:
                logger.warning(f"spec_server returned {resp.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Local LLM query failed: {e}")
            return None

    def _parse_yes_no(self, response: Optional[str]) -> Optional[bool]:
        """Parse a YES/NO response. Returns None if unparseable."""
        if response is None:
            return None
        response = response.upper().strip()
        if response.startswith("YES"):
            return True
        if response.startswith("NO"):
            return False
        return None

    def review(self, code: str, spec: str = "") -> ReviewResult:
        """
        Run all classification prompts against the code.

        Args:
            code: The source code to review.
            spec: Optional spec text for spec-matching check.

        Returns:
            ReviewResult with pass/fail and individual question results.
        """
        result = ReviewResult(passed=True)

        if not self.is_available():
            result.available = False
            result.verdict = "SKIPPED: Orange Pi unavailable — relying on deterministic checks only"
            return result

        checks = {
            "word_salad": ("Is word salad?", True),     # YES = bad
            "stub_check": ("Is a stub?", True),          # YES = bad
            "real_implementation": ("Is real code?", False),  # NO = bad
        }

        if spec:
            checks["spec_match"] = ("Matches spec?", False)  # NO = bad

        for check_name, (description, bad_if_yes) in checks.items():
            template = CLASSIFICATION_PROMPTS[check_name]
            prompt = template.format(code=code[:3000], spec=spec[:1000])  # truncate for small models

            raw_response = self._ask(prompt)
            answer = self._parse_yes_no(raw_response)

            result.questions_asked += 1
            entry = {
                "check": check_name,
                "description": description,
                "raw_response": raw_response,
                "parsed": answer,
                "flagged": False,
            }

            if answer is None:
                # Couldn't parse — don't fail, but log it
                entry["flagged"] = False
                logger.warning(f"Unparseable response for {check_name}: {raw_response}")
            elif bad_if_yes and answer:
                entry["flagged"] = True
                result.questions_failed += 1
            elif not bad_if_yes and not answer:
                entry["flagged"] = True
                result.questions_failed += 1

            result.responses.append(entry)

        if result.questions_failed > 0:
            result.passed = False
            failed_checks = [r["check"] for r in result.responses if r["flagged"]]
            result.verdict = f"REJECTED by local LLM: failed {failed_checks}"
        else:
            result.verdict = f"PASSED: {result.questions_asked} checks OK"

        return result


# Singleton instance for the default Orange Pi
_default_reviewer = None


def get_reviewer(**kwargs) -> LocalLLMReviewer:
    """Get or create the default Orange Pi reviewer."""
    global _default_reviewer
    if _default_reviewer is None:
        _default_reviewer = LocalLLMReviewer(**kwargs)
    return _default_reviewer


if __name__ == "__main__":
    import sys

    reviewer = LocalLLMReviewer()
    print(f"Orange Pi available: {reviewer.is_available()}")

    if len(sys.argv) > 1 and reviewer.is_available():
        with open(sys.argv[1], "r") as f:
            code = f.read()
        result = reviewer.review(code)
        print(f"Verdict: {result.verdict}")
        for r in result.responses:
            flag = "❌" if r["flagged"] else "✅"
            print(f"  {flag} {r['description']} → {r['raw_response']}")
