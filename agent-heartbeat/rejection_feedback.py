"""
Rejection Feedback Formatter — AHOS

When the validator rejects agent output, this module transforms the
raw rejection data into structured, actionable instructions that can
be fed back to the agent for a retry attempt.

The feedback is designed to be:
  1. Specific — exact line numbers, exact problems
  2. Actionable — tells the agent exactly what to fix
  3. Concise — under 500 tokens (don't waste the retry budget)
  4. Educational — teaches the agent to avoid the same mistake

Usage:
    from rejection_feedback import format_feedback
    feedback = format_feedback(validation_report, attempt=1, max_attempts=3)
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RetryInstruction:
    """A single, specific instruction for fixing a rejection."""
    category: str       # "word_salad", "stub", "local_llm"
    severity: str       # "critical", "warning"
    message: str        # Human-readable instruction
    lines: List[int] = field(default_factory=list)    # Flagged line numbers
    examples: List[str] = field(default_factory=list)  # Example bad text


@dataclass
class RejectionFeedback:
    """Complete retry package for a rejected submission."""
    attempt: int
    max_attempts: int
    instructions: List[RetryInstruction] = field(default_factory=list)
    prompt_text: str = ""  # The formatted prompt to prepend to the retry


def format_feedback(report, attempt: int = 1, max_attempts: int = 3) -> RejectionFeedback:
    """
    Transform a ValidationReport into structured retry feedback.

    Args:
        report: ValidationReport from validator.py
        attempt: Current attempt number (1-indexed)
        max_attempts: Maximum retry attempts allowed

    Returns:
        RejectionFeedback with actionable instructions and a
        formatted prompt string ready to prepend to the retry.
    """
    feedback = RejectionFeedback(
        attempt=attempt,
        max_attempts=max_attempts,
    )

    # --- Word Salad Feedback ---
    if report.word_salad and not report.word_salad.passed:
        ws = report.word_salad
        lines = [ln for ln, _, _ in ws.flagged_lines] if ws.flagged_lines else []
        examples = []

        for ln, text, matches in (ws.flagged_lines or [])[:3]:
            # Truncate to keep feedback concise
            clean = text.strip()[:100]
            examples.append(f"  L{ln}: \"{clean}\"")

        instruction = RetryInstruction(
            category="word_salad",
            severity="critical",
            message=_word_salad_instruction(ws),
            lines=lines,
            examples=examples,
        )
        feedback.instructions.append(instruction)

    # --- Stub Detection Feedback ---
    if report.stubs and not report.stubs.passed:
        stubs = report.stubs
        lines = [ln for ln, _, _ in stubs.flagged_lines] if stubs.flagged_lines else []
        examples = []

        for ln, text, msg in (stubs.flagged_lines or [])[:3]:
            examples.append(f"  L{ln}: {msg}")

        instruction = RetryInstruction(
            category="stub",
            severity="critical",
            message=_stub_instruction(stubs),
            lines=lines,
            examples=examples,
        )
        feedback.instructions.append(instruction)

    # --- Local LLM Review Feedback ---
    if report.local_llm and not report.local_llm.passed and report.local_llm.available:
        instruction = RetryInstruction(
            category="local_llm",
            severity="warning",
            message=_local_llm_instruction(report.local_llm),
        )
        feedback.instructions.append(instruction)

    # Build the formatted prompt text
    feedback.prompt_text = _build_retry_prompt(feedback)
    return feedback


def _word_salad_instruction(ws) -> str:
    """Generate specific word salad fix instructions."""
    parts = []
    parts.append("YOUR COMMENTS CONTAIN FILLER LANGUAGE.")
    parts.append("The automated word salad detector flagged your output.")
    parts.append("")
    parts.append("WHAT TO FIX:")

    # Parse the verdict to give specific guidance
    verdict = ws.verdict
    if "PHRASE_HIT" in verdict:
        parts.append("- You used known hallucination phrases (e.g., 'gracefully',")
        parts.append("  'seamlessly', 'leveraging'). Remove ALL of them.")
    if "CHAIN_HIT" in verdict:
        parts.append("- Multiple lines have chains of 2+ adverbs.")
        parts.append("  Comments should be SHORT and TECHNICAL.")
        parts.append("  BAD:  '// Gracefully handling input ensuring safety'")
        parts.append("  GOOD: '// Clamp input to [0.0, 1.0]'")
    if "ADVERB_COUNT" in verdict:
        parts.append("- Too many adverbs overall. Your comments should")
        parts.append("  describe WHAT the code does, not HOW WELL it does it.")
    if "DENSITY" in verdict:
        parts.append("- Filler word density is too high across the file.")
        parts.append("  Most comments should be 3-8 words. Be terse.")

    parts.append("")
    parts.append("RULE: Comments describe WHAT, not HOW WELL.")
    parts.append("If a comment doesn't add information, delete it.")
    return "\n".join(parts)


def _stub_instruction(stubs) -> str:
    """Generate specific stub fix instructions."""
    parts = []
    parts.append("YOUR CODE CONTAINS STUBS OR PLACEHOLDER IMPLEMENTATIONS.")
    parts.append("The automated stub detector found non-functional code.")
    parts.append("")
    parts.append("WHAT TO FIX:")

    verdict = stubs.verdict
    if "INSTANT_REJECT" in verdict:
        parts.append("- CRITICAL: Your code admits it's not real.")
        parts.append("  Phrases like 'in a real environment', 'placeholder',")
        parts.append("  'TODO: implement' are instant rejection triggers.")
        parts.append("  Every function must have a REAL implementation.")
    if "SUSPICIOUS" in verdict:
        parts.append("- Suspicious patterns found (bare pass, empty returns,")
        parts.append("  NotImplementedError). Replace with real logic.")
    if "CODE_RATIO" in verdict:
        parts.append("- Code-to-comment ratio is too low. Your file is")
        parts.append("  mostly comments and whitespace. Add real logic.")

    parts.append("")
    parts.append("RULE: Every function must DO something real.")
    parts.append("If you don't know how to implement it, study the")
    parts.append("golden example (Vimana GVS010) in your context.")
    return "\n".join(parts)


def _local_llm_instruction(review) -> str:
    """Generate local LLM review fix instructions."""
    parts = []
    parts.append("THE LOCAL REVIEWER FLAGGED QUALITY CONCERNS.")
    parts.append(f"Verdict: {review.verdict}")
    if review.reasoning:
        parts.append(f"Details: {review.reasoning[:200]}")
    parts.append("")
    parts.append("Review your output against the spec requirements.")
    return "\n".join(parts)


def _build_retry_prompt(feedback: RejectionFeedback) -> str:
    """
    Build the formatted prompt text for a retry attempt.

    This gets prepended to the agent's context on retry,
    after the heartbeat header and before the task description.
    """
    lines = []
    lines.append("=" * 60)
    lines.append(f"⚠️  RETRY — Attempt {feedback.attempt + 1}/{feedback.max_attempts}")
    lines.append(f"Your previous submission was REJECTED.")
    lines.append("=" * 60)
    lines.append("")
    lines.append("You MUST fix the following issues. Your output will be")
    lines.append("scanned again by the SAME validators. If you repeat")
    lines.append("the same mistakes, this task will be marked as FAILED.")
    lines.append("")

    for i, instruction in enumerate(feedback.instructions, 1):
        lines.append(f"--- Issue {i} [{instruction.severity.upper()}]: {instruction.category} ---")
        lines.append(instruction.message)

        if instruction.examples:
            lines.append("")
            lines.append("FLAGGED LINES:")
            for ex in instruction.examples:
                lines.append(ex)

        lines.append("")

    lines.append("=" * 60)
    lines.append("Generate a COMPLETE, CORRECTED file. Do not explain")
    lines.append("your changes. Just output the fixed code.")
    lines.append("=" * 60)

    return "\n".join(lines)


# =====================================================================
# CLI test
# =====================================================================
if __name__ == "__main__":
    import sys
    import logging

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print("Usage: python rejection_feedback.py <file>")
        print("  Runs validator, then shows what retry feedback would look like.")
        sys.exit(1)

    # Import validator
    from validator import validate_output

    with open(sys.argv[1], "r") as f:
        code = f.read()

    # Validate
    report = validate_output(code, use_local_llm=False)

    if report.passed:
        print("✅ File passed all validators — no feedback needed.")
    else:
        # Generate feedback
        feedback = format_feedback(report, attempt=1, max_attempts=3)
        print(feedback.prompt_text)
        print(f"\n--- Stats ---")
        print(f"Instructions: {len(feedback.instructions)}")
        print(f"Prompt length: {len(feedback.prompt_text)} chars")
        print(f"Est. tokens: ~{len(feedback.prompt_text) // 4}")
