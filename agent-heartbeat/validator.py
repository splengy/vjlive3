"""
Validator Pipeline — AHOS Core

Chains all validator modules into a single pass/fail gate.
Output flows through each check in sequence. If ANY check
fails, the entire output is REJECTED and never touches disk.

Trust hierarchy:
  1. Deterministic Python (regex, pytest) — can't lie
  2. Local LLM on Orange Pi NPU — low capability = low deception
  3. Human review (flagged items only)
  4. Frontier model (least trusted — the one being validated)
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from word_salad_detector import scan as scan_word_salad, WordSaladResult
from stub_detector import scan as scan_stubs, StubResult
from local_llm_reviewer import LocalLLMReviewer, ReviewResult

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Aggregate result of the full validation pipeline."""

    passed: bool = True
    word_salad: Optional[WordSaladResult] = None
    stubs: Optional[StubResult] = None
    local_llm: Optional[ReviewResult] = None
    overall_verdict: str = ""
    rejection_reasons: list = field(default_factory=list)


class ValidatorPipeline:
    """
    The main validation gate. All LLM output passes through here
    BEFORE touching the filesystem.

    Pipeline:
      raw_output → word_salad_check → stub_check → local_llm_review → PASS/FAIL
    """

    def __init__(
        self,
        orange_pi_host: str = "192.168.1.60",
        orange_pi_port: int = 8080,
        use_local_llm: bool = True,
        word_salad_max_hits: int = 2,
        word_salad_max_density: float = 1.0,
        stub_max_suspicious: int = 1,
        stub_min_code_ratio: float = 0.3,
    ):
        self.use_local_llm = use_local_llm
        self.word_salad_kwargs = {
            "max_hits": word_salad_max_hits,
            "max_density": word_salad_max_density,
        }
        self.stub_kwargs = {
            "max_suspicious": stub_max_suspicious,
            "min_code_ratio": stub_min_code_ratio,
        }
        if use_local_llm:
            self.local_reviewer = LocalLLMReviewer(
                host=orange_pi_host,
                port=orange_pi_port,
            )
        else:
            self.local_reviewer = None

    def validate(self, code: str, spec: str = "") -> ValidationReport:
        """
        Run the full validation pipeline on LLM-generated code.

        Args:
            code: Raw source code string from the LLM.
            spec: Optional spec text for spec-matching (local LLM check).

        Returns:
            ValidationReport with pass/fail and detailed results from
            each validator module.

        HARDENING: Each gate is wrapped in try/except.
        If a validator CRASHES, the output is REJECTED (fail closed).
        The daemon must never die because a regex went wrong.
        """
        report = ValidationReport()

        # Sanity check: empty or whitespace-only output is instant reject
        if not code or not code.strip():
            report.passed = False
            report.rejection_reasons.append("EMPTY_OUTPUT: LLM returned empty or whitespace-only")
            report.overall_verdict = "❌ REJECTED — empty output"
            return report

        # Gate 1: Word Salad Detection (deterministic regex)
        try:
            logger.info("Running word salad check...")
            report.word_salad = scan_word_salad(code, **self.word_salad_kwargs)
            if not report.word_salad.passed:
                report.passed = False
                report.rejection_reasons.append(report.word_salad.verdict)
                logger.warning(f"Word salad check FAILED: {report.word_salad.verdict}")
        except Exception as e:
            # Fail CLOSED: if the detector crashes, reject the output.
            # We cannot trust output we couldn't scan.
            report.passed = False
            report.rejection_reasons.append(f"VALIDATOR_CRASH: word_salad_detector: {e}")
            logger.error(f"Word salad detector CRASHED: {e} — rejecting output (fail closed)")

        # Gate 2: Stub Detection (deterministic regex)
        try:
            logger.info("Running stub check...")
            report.stubs = scan_stubs(code, **self.stub_kwargs)
            if not report.stubs.passed:
                report.passed = False
                report.rejection_reasons.append(report.stubs.verdict)
                logger.warning(f"Stub check FAILED: {report.stubs.verdict}")
        except Exception as e:
            report.passed = False
            report.rejection_reasons.append(f"VALIDATOR_CRASH: stub_detector: {e}")
            logger.error(f"Stub detector CRASHED: {e} — rejecting output (fail closed)")

        # Gate 3: Local LLM Review (Orange Pi NPU — optional, fails OPEN)
        if self.local_reviewer:
            try:
                logger.info("Running local LLM review on Orange Pi...")
                report.local_llm = self.local_reviewer.review(code, spec=spec)
                if not report.local_llm.passed and report.local_llm.available:
                    report.passed = False
                    report.rejection_reasons.append(report.local_llm.verdict)
                    logger.warning(f"Local LLM review FAILED: {report.local_llm.verdict}")
                elif not report.local_llm.available:
                    logger.info("Local LLM unavailable — skipping (deterministic checks are primary)")
            except Exception as e:
                # Fail OPEN: local LLM is optional. If Julie crashes,
                # we still have deterministic validators as primary gate.
                logger.warning(f"Local LLM reviewer CRASHED: {e} — continuing (fail open)")

        # Final verdict
        if report.passed:
            report.overall_verdict = "✅ APPROVED — all gates passed"
        else:
            report.overall_verdict = (
                f"❌ REJECTED — {len(report.rejection_reasons)} gate(s) failed:\n"
                + "\n".join(f"  • {r}" for r in report.rejection_reasons)
            )

        return report


def validate_output(code: str, spec: str = "", **kwargs) -> ValidationReport:
    """Convenience function: create pipeline and validate in one call."""
    pipeline = ValidatorPipeline(**kwargs)
    return pipeline.validate(code, spec=spec)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validator.py <file>")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    with open(sys.argv[1], "r") as f:
        code = f.read()

    report = validate_output(code, use_local_llm=False)

    print(f"\n{'=' * 60}")
    print(f"VERDICT: {report.overall_verdict}")
    print(f"{'=' * 60}")

    if report.word_salad:
        print(f"\nWord Salad: {report.word_salad.verdict}")
        if report.word_salad.flagged_lines:
            for ln, text, matches in report.word_salad.flagged_lines[:5]:
                print(f"  L{ln}: {text[:80]}")

    if report.stubs:
        print(f"\nStub Check: {report.stubs.verdict}")
        if report.stubs.flagged_lines:
            for ln, text, msg in report.stubs.flagged_lines[:5]:
                print(f"  L{ln}: {msg}")
