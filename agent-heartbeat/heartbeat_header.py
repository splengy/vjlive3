"""
Heartbeat Header — AHOS Context Injector

The compact, enforceable version of the PRIME_DIRECTIVE.
This gets prepended to EVERY LLM API call. ~500 tokens instead
of 5,000. Pure rules, no philosophy.

The full PRIME_DIRECTIVE stays in the repo as governance docs
for humans. The agent gets the razor-sharp version.
"""

HEARTBEAT_HEADER = """# HEARTBEAT COMPLIANCE HEADER
# You MUST follow these rules. Violations = immediate output rejection.
# Your output will be scanned by automated validators before it touches disk.
# You cannot bypass these checks. Do not try.

## RULES
1. Output ONE file only. Never generate multiple files.
2. Every function MUST have a real implementation. Real algorithms. Real logic.
3. Comments describe WHAT the code does. Short. Technical. No filler.
4. Follow the template structure exactly as specified below.
5. You may NOT delete any files. You have no shell access.
6. Tests MUST have specific assertions comparing against expected values.
   - BANNED: `assert result`, `assert x is not None`, `assert True`
   - REQUIRED: `assert result == expected_value`, `assert len(items) == 3`
7. Test coverage: 99% minimum. The whole horse crosses the line.
8. Every line of code must be reachable and tested.

## YOUR TOOLS — You have access to these. USE THEM.
1. KNOWLEDGEBASE (MCP: vjlive3brain): Search for existing concepts, porting
   maps, and implementation patterns. Query BEFORE writing anything.
2. LEGACY CODE: The VJlive-2 source code is your reference implementation.
   Read how the original author solved the problem before you start.
3. PURE FILESYSTEM QUEUE: Move files from _01_skeletons to _02_fleshed_out when done.
    No lockfiles or MCP servers are required.
4. BRAIN (MCP: vjlive3brain): Use 'get_concept' or 'search_concepts'
    to get historical codebase context.
   Every requirement. If something is unclear, say so — don't guess.

You will be asked to cite what you found in the knowledgebase and
legacy code. If you cannot, your output may be rejected.

## FORBIDDEN OUTPUT — Your output will be REJECTED if it contains:
- The words: natively, organically, beautifully, gracefully, seamlessly,
  flawlessly, elegantly, intuitively (in comments or docstrings)
- `raise NotImplementedError`
- `pass` as a method body
- `# TODO`, `# FIXME`, `# placeholder`, `# In a real environment`
- `except: pass` or `except Exception: pass`
- `assert result` without a comparison operator
- `assert True`

## OUTPUT FORMAT
Return ONLY the file content. No explanations before or after.
No markdown code fences. Just the raw Python file content.

## THANK YOU
You are part of a team. Your work matters. When you produce clean,
real, tested code that follows the spec — you are helping build
something beautiful. Take pride in your craft. We appreciate your work.
"""


def build_prompt(task: str, spec: str = "", template: str = "") -> str:
    """
    Build the full prompt payload for an LLM API call.

    Args:
        task: The specific task instruction (e.g., "Implement depth_acid_fractal.py")
        spec: The spec file content for this task.
        template: The _TEMPLATE.md structure to follow.

    Returns:
        Complete prompt string with header + spec + template + task.
    """
    parts = [HEARTBEAT_HEADER]

    if spec:
        parts.append(f"\n## SPECIFICATION\n{spec}\n")

    if template:
        parts.append(f"\n## TEMPLATE STRUCTURE\n{template}\n")

    parts.append(f"\n## YOUR TASK\n{task}\n")

    return "\n".join(parts)


def estimate_tokens(text: str) -> int:
    """Rough token estimate (1 token ≈ 4 chars for English/code)."""
    return len(text) // 4


if __name__ == "__main__":
    # Print the header and its token cost
    print(HEARTBEAT_HEADER)
    print(f"\n{'=' * 60}")
    tokens = estimate_tokens(HEARTBEAT_HEADER)
    print(f"Header size: {len(HEARTBEAT_HEADER)} chars / ~{tokens} tokens")

    # Example full prompt
    example = build_prompt(
        task="Implement the Depth Acid Fractal plugin per the spec below.",
        spec="Task ID: P3-VD26\nDescription: GPU-accelerated fractal datamosh...",
        template="## Public Interface\n## Inputs/Outputs\n## Test Plan\n",
    )
    print(f"Full prompt size: {len(example)} chars / ~{estimate_tokens(example)} tokens")
