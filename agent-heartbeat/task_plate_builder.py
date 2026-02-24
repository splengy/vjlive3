"""
Task Plate Builder — AHOS Core

"Single serving. Wash the plate."

Every task gets plated up with everything the agent needs:
  - The heartbeat compliance header (rules + tools + thank you)
  - The spec for this specific task
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
        project_root: str = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning",
        legacy_root: str = "/home/happy/Desktop/claude projects/VJlive-2",
        specs_dir: str = "docs/specs",
        template_path: str = "docs/specs/_TEMPLATE.md",
        token_budget: int = 8000,
    ):
        self.project_root = Path(project_root)
        self.legacy_root = Path(legacy_root)
        self.specs_dir = self.project_root / specs_dir
        self.template_path = self.project_root / template_path
        self.token_budget = token_budget

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
        Search the VJlive-2 legacy codebase for relevant reference code.

        Returns a dict of {filename: content_snippet} for files that
        seem related to the task description.
        """
        snippets = {}
        if not self.legacy_root.exists():
            logger.warning(f"Legacy root not found: {self.legacy_root}")
            return snippets

        # Extract keywords from task description
        keywords = []
        for word in task_description.lower().split():
            if len(word) > 3 and word not in ("implement", "plugin", "effect", "the", "for", "with"):
                keywords.append(word)

        # Search legacy source directories
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
                    if content and len(content) < 5000:  # Don't include massive files
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

        # Assemble the prompt
        parts = [HEARTBEAT_HEADER]

        if plate.spec_content:
            parts.append(f"\n## SPECIFICATION FOR {task_id}\n{plate.spec_content}\n")

        if plate.template_content:
            parts.append(f"\n## TEMPLATE STRUCTURE\n{plate.template_content}\n")

        if plate.legacy_snippets:
            parts.append("\n## LEGACY REFERENCE CODE")
            parts.append("Study how the original VJlive-2 implementation works:")
            for fname, code in list(plate.legacy_snippets.items())[:3]:  # Max 3 refs
                parts.append(f"\n### {fname}\n```python\n{code[:2000]}\n```\n")

        if plate.kb_context:
            parts.append(f"\n## KNOWLEDGEBASE CONTEXT\n{plate.kb_context}\n")

        parts.append(f"\n## YOUR TASK\n{task_description}\n")
        parts.append(
            f"\nTask ID: {task_id}\n"
            f"Remember: ONE file only. Real code. Real tests. "
            f"Thank you for your careful work.\n"
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
        parts = [HEARTBEAT_HEADER]
        if plate.spec_content:
            parts.append(f"\n## SPECIFICATION FOR {plate.task_id}\n{plate.spec_content}\n")
        if plate.template_content:
            parts.append(f"\n## TEMPLATE STRUCTURE\n{plate.template_content}\n")
        parts.append(f"\n## YOUR TASK\n{plate.task_description}\n")
        parts.append(
            f"\nTask ID: {plate.task_id}\n"
            f"Remember: ONE file only. Real code. Real tests. "
            f"Thank you for your careful work.\n"
        )
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
