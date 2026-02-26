"""
Task Plate Builder — AHOS Core

"Single serving. Wash the plate."

Every task gets plated up with everything the agent needs:
  - The heartbeat compliance header (rules + tools + thank you)
  - The spec for this specific task

Pass 1 (Julie): Query Qdrant for legacy code, assemble rough spec.
Pass 2 (Deep agent): Refine with architecture decisions, edge cases.
See WORKSPACE/SPEC_PIPELINE.md for the full multi-pass process.
  - The template structure to follow
  - Relevant legacy code references
  - Knowledgebase context (if MCP is available)

After the task is done (pass or fail), the plate is washed —
fresh context, clean slate, new instance. No lingering state.
No context drift. No accumulated hallucination.
"""

import json
import os
import logging
import re
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from heartbeat_header import HEARTBEAT_HEADER, estimate_tokens

logger = logging.getLogger(__name__)


@dataclass
class TaskPlate:
    """
    A single-serving task package for a coder agent.

    Contains everything the agent needs, nothing more.
    Thrown away after use — new plate for every task.
    """

    task_id: str
    task_description: str
    prompt: str = ""           # The full assembled prompt
    spec_content: str = ""     # Raw spec file content
    template_content: str = "" # Template structure
    legacy_refs: list = field(default_factory=list)  # Paths to relevant legacy code
    legacy_snippets: dict = field(default_factory=dict)  # Extracted code snippets
    kb_context: str = ""       # Knowledgebase search results
    token_count: int = 0       # Estimated total tokens
    token_budget: int = 8000   # Max input tokens for this task


class TaskPlateBuilder:
    """
    Assembles a clean, complete task plate for each agent dispatch.

    The builder gathers all context an agent needs, assembles it into
    a single prompt, and estimates the token cost. If the plate exceeds
    the token budget, it trims the least critical content.
    """

    def __init__(
        self,
        project_root: str = "",
        legacy_root: str = "",
        specs_dir: str = "docs/specs",
        template_path: str = "docs/specs/_TEMPLATE.md",
        token_budget: int = 8000,
        qdrant_url: str = "http://192.168.1.60:6333",
        qdrant_collection: str = "vjlive_code",
    ):
        if not project_root:
            project_root = str(Path(os.path.dirname(os.path.abspath(__file__))).parent)
        if not legacy_root:
            legacy_root = str(Path(project_root).parent / "VJlive-2")
        self.project_root = Path(project_root)
        self.legacy_root = Path(legacy_root)
        self.specs_dir = self.project_root / specs_dir
        self.template_path = self.project_root / template_path
        self.token_budget = token_budget
        self.qdrant_url = qdrant_url
        self.qdrant_collection = qdrant_collection

    def _read_file_safe(self, path: Path) -> str:
        """Read a file, return empty string on error."""
        try:
            return path.read_text(encoding="utf-8")
        except (FileNotFoundError, PermissionError) as e:
            logger.warning(f"Could not read {path}: {e}")
            return ""

    def _find_spec(self, task_id: str) -> str:
        """Find and read the spec file for a task ID."""
        if not self.specs_dir.exists():
            return ""

        # Try exact match first (e.g., P3-VD26_DepthAcidFractal.md)
        for spec_file in self.specs_dir.glob(f"{task_id}*.md"):
            content = self._read_file_safe(spec_file)
            if content:
                logger.info(f"Found spec: {spec_file.name}")
                return content

        # Try fuzzy match
        task_prefix = task_id.split("_")[0]  # P3-VD26
        for spec_file in self.specs_dir.glob(f"{task_prefix}*.md"):
            content = self._read_file_safe(spec_file)
            if content:
                logger.info(f"Found spec (fuzzy): {spec_file.name}")
                return content

        logger.warning(f"No spec found for task {task_id}")
        return ""

    def _find_legacy_reference(self, task_description: str) -> dict:
        """
        Search legacy codebases for relevant reference code via Qdrant.

        Queries the 269K-point vector DB on Julie for semantically
        matching code chunks from both VJlive-1 and VJlive-2.

        NO FALLBACK. If Qdrant is down or returns nothing, the task FAILS.
        The whole horse crosses the line or we don't race.

        Returns a dict of {filename: content_snippet}.
        Raises RuntimeError if Qdrant is unreachable or returns no results.
        """
        # Qdrant is REQUIRED — no fallback, no partial specs
        snippets = self._search_qdrant(task_description)

        if not snippets:
            logger.warning(
                f"Qdrant returned 0 legacy refs for: {task_description!r}. "
                f"Proceeding without legacy context — spec will have [NEEDS RESEARCH] gaps."
            )
            return {}

        logger.info(f"Qdrant returned {len(snippets)} legacy refs")
        return snippets

    def _search_qdrant(self, query: str, limit: int = 5) -> dict:
        """
        Search Qdrant for legacy code matching the query.

        Uses Qdrant's scroll API with payload filtering on filepath.
        For semantic search, the embedding model must be available.
        """
        snippets = {}

        # Extract searchable terms from the task description
        # e.g. "depth_acid_fractal (DepthAcidFractalPlugin)" -> ["depth_acid_fractal", "DepthAcidFractal"]
        terms = []
        # Get module name (before parentheses)
        module_match = re.match(r'([\w_]+)', query)
        if module_match:
            terms.append(module_match.group(1))
        # Get class name (inside parentheses)
        class_match = re.search(r'\(([\w]+)\)', query)
        if class_match:
            terms.append(class_match.group(1))
        # Also add raw words > 4 chars
        for word in query.lower().split():
            if len(word) > 4 and word not in ('implement', 'plugin', 'effect', 'module'):
                terms.append(word)

        for term in terms[:3]:  # Max 3 searches
            payload = {
                "filter": {
                    "must": [
                        {
                            "key": "filepath",
                            "match": {"text": term}
                        }
                    ]
                },
                "limit": limit,
                "with_payload": True,
            }

            url = f"{self.qdrant_url}/collections/{self.qdrant_collection}/points/scroll"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST',
            )

            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    points = data.get('result', {}).get('points', [])
                    for point in points:
                        p = point.get('payload', {})
                        filepath = p.get('filepath', 'unknown')
                        codebase = p.get('codebase', '')
                        content = p.get('content', '')
                        start = p.get('start_line', 0)
                        end = p.get('end_line', 0)
                        key = f"{codebase}/{filepath} (L{start}-{end})"
                        if content and key not in snippets:
                            snippets[key] = content
            except (urllib.error.URLError, TimeoutError) as e:
                logger.debug(f"Qdrant request failed for term '{term}': {e}")
                continue

        return snippets

    def _search_local_legacy(self, task_description: str) -> dict:
        """Fallback: search local VJlive-2 files by keyword matching."""
        snippets = {}
        if not self.legacy_root.exists():
            logger.warning(f"Legacy root not found: {self.legacy_root}")
            return snippets

        keywords = []
        for word in task_description.lower().split():
            if len(word) > 3 and word not in ('implement', 'plugin', 'effect', 'the', 'for', 'with'):
                keywords.append(word)

        search_dirs = [
            self.legacy_root / "src",
            self.legacy_root / "core",
            self.legacy_root / "effects",
            self.legacy_root / "plugins",
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for py_file in search_dir.rglob("*.py"):
                fname = py_file.stem.lower()
                if any(kw in fname for kw in keywords):
                    content = self._read_file_safe(py_file)
                    if content and len(content) < 5000:
                        snippets[str(py_file.relative_to(self.legacy_root))] = content
                        logger.info(f"Found legacy reference: {py_file.name}")

        return snippets

    def build(self, task_id: str, task_description: str) -> TaskPlate:
        """
        Build a complete task plate — everything an agent needs,
        assembled fresh for this single task.

        Args:
            task_id: Unique task identifier (e.g., "P3-VD26")
            task_description: Human-readable task description

        Returns:
            A fully assembled TaskPlate ready for dispatch.
        """
        plate = TaskPlate(
            task_id=task_id,
            task_description=task_description,
            token_budget=self.token_budget,
        )

        # Gather ingredients
        plate.spec_content = self._find_spec(task_id)
        plate.template_content = self._read_file_safe(self.template_path)
        plate.legacy_snippets = self._find_legacy_reference(task_description)

        # Assemble the prompt — SPEC GENERATION ONLY
        # No coding. Julie writes a spec from template + legacy refs.
        parts = []

        parts.append(
            "# SPEC GENERATION — FIRST PASS\n"
            "You are writing a SPECIFICATION, not code.\n"
            "Your output is a single markdown file that follows the template below.\n"
            "Fill every section using the legacy code references provided.\n"
            "If legacy code is missing for a section, mark it [NEEDS RESEARCH].\n"
            "Do NOT generate any Python code files. Do NOT write tests.\n"
            "Do NOT hallucinate features not found in the legacy references.\n"
        )

        if plate.template_content:
            parts.append(f"\n## SPEC TEMPLATE — Follow this structure exactly\n{plate.template_content}\n")

        if plate.legacy_snippets:
            parts.append("\n## LEGACY CODE REFERENCES")
            parts.append("Use these to fill in the spec. These are the REAL implementations:")
            for fname, code in list(plate.legacy_snippets.items())[:5]:  # Max 5 refs for specs
                parts.append(f"\n### {fname}\n```python\n{code[:3000]}\n```\n")

        parts.append(f"\n## TASK\n")
        parts.append(f"Task ID: {task_id}")
        parts.append(f"Description: {task_description}")
        parts.append(
            f"\nCreate a spec file for this task. "
            f"Output ONLY the spec markdown content. "
            f"The file will be saved as docs/specs/{task_id}_<name>.md\n"
        )

        plate.prompt = "\n".join(parts)
        plate.token_count = estimate_tokens(plate.prompt)

        # Trim if over budget
        if plate.token_count > plate.token_budget:
            logger.warning(
                f"Plate for {task_id} is {plate.token_count} tokens "
                f"(budget: {plate.token_budget}). Trimming legacy refs."
            )
            # Remove legacy snippets first (least critical)
            plate.legacy_snippets = {}
            plate.prompt = self._rebuild_prompt(plate)
            plate.token_count = estimate_tokens(plate.prompt)

        logger.info(
            f"Plate built for {task_id}: "
            f"{plate.token_count} tokens "
            f"(spec: {'yes' if plate.spec_content else 'no'}, "
            f"legacy: {len(plate.legacy_snippets)} refs)"
        )

        return plate

    def _rebuild_prompt(self, plate: TaskPlate) -> str:
        """Rebuild prompt after trimming."""
        parts = [
            "# SPEC GENERATION — FIRST PASS\n"
            "You are writing a SPECIFICATION, not code.\n"
            "Fill every section of the template. Mark gaps as [NEEDS RESEARCH].\n"
        ]
        if plate.template_content:
            parts.append(f"\n## SPEC TEMPLATE\n{plate.template_content}\n")
        parts.append(f"\n## TASK\nTask ID: {plate.task_id}\n{plate.task_description}\n")
        return "\n".join(parts)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    builder = TaskPlateBuilder()

    # Example: build a plate for depth_acid_fractal
    plate = builder.build(
        task_id="P3-VD26",
        task_description=(
            "Implement the Depth Acid Fractal plugin. "
            "Port from VJlive-2 DepthAcidFractalDatamoshEffect. "
            "Must include GPU fragment shader, FBO ping-pong, "
            "and all 10 audio-reactive parameters."
        ),
    )

    print(f"{'=' * 60}")
    print(f"Task Plate for: {plate.task_id}")
    print(f"Tokens: {plate.token_count} / {plate.token_budget}")
    print(f"Spec: {'✅ found' if plate.spec_content else '❌ missing'}")
    print(f"Template: {'✅ found' if plate.template_content else '❌ missing'}")
    print(f"Legacy refs: {len(plate.legacy_snippets)}")
    print(f"{'=' * 60}")
    print(f"\nFirst 500 chars of prompt:")
    print(plate.prompt[:500])
