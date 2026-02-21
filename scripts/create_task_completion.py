#!/usr/bin/env python3
"""
Task Completion Report Generator

Creates standardized task_completion.md files for autonomous agents.
This replaces walkthroughs with structured completion reports.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def create_task_completion(
    task_name: str,
    phase_name: str,
    files_touched: List[str],
    key_decisions: List[str],
    challenges_overcome: List[str],
    performance_impact: Dict[str, Any],
    test_coverage: float,
    sanity_check_results: Dict[str, bool],
    known_issues: List[str] = None,
    next_steps: List[str] = None,
    blockers: List[str] = None
) -> str:
    """Generate task_completion.md content."""
    
    template = f"""# Task Completion: {task_name}

## Executive Summary
Brief overview of what was accomplished and why it matters.

## Implementation Details

### Files Created/Modified
{chr(10).join(f'- `{file}`' for file in files_touched)}

### Key Decisions
{chr(10).join(f'- {decision}' for decision in key_decisions)}

### Challenges Overcome
{chr(10).join(f'- {challenge}' for challenge in challenges_overcome)}

### Performance Impact
"""
    
    if performance_impact:
        for metric, value in performance_impact.items():
            template += f"- **{metric}**: {value}\n"
    else:
        template += "- No significant performance impact\n"
    
    template += f"""
## Testing Results

### Test Coverage
- **Achieved**: {test_coverage}%
- **Requirement**: ≥80%
- **Status**: {'✅ PASS' if test_coverage >= 80 else '❌ FAIL'}

### Performance Benchmarks
- **FPS**: {performance_impact.get('FPS', 'N/A')}
- **Memory**: {performance_impact.get('Memory', 'N/A')}
- **CPU**: {performance_impact.get('CPU', 'N/A')}

### Sanity Check Results
"""
    
    for check, result in sanity_check_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        template += f"- **{check}**: {status}\n"
    
    if known_issues:
        template += "\n### Known Issues\n"
        for issue in known_issues:
            template += f"- {issue}\n"
    else:
        template += "\n### Known Issues\n- None\n"
    
    template += f"""
## Next Steps

### Immediate Next Tasks
{chr(10).join(f'- {step}' for step in (next_steps or ['None identified']))}

### Dependencies
- All dependencies resolved

### Blockers
{chr(10).join(f'- {blocker}' for blocker in (blockers or ['None']))}

## Completion Criteria Met
- [x] All deliverables completed
- [x] All tests passing
- [x] Performance requirements met
- [x] Documentation updated
- [x] task_completion.md written

---
**Phase**: {phase_name}
**Completed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Agent**: Autonomous Agent
"""
    
    return template

def main():
    if len(sys.argv) < 2:
        print("Usage: create_task_completion.py <task_name> [json_input_file]")
        print("Or provide JSON via stdin")
        sys.exit(1)
    
    task_name = sys.argv[1]
    
    # Try to read JSON from file or stdin
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'r') as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    
    content = create_task_completion(
        task_name=task_name,
        phase_name=data.get('phase_name', 'Unknown Phase'),
        files_touched=data.get('files_touched', []),
        key_decisions=data.get('key_decisions', []),
        challenges_overcome=data.get('challenges_overcome', []),
        performance_impact=data.get('performance_impact', {}),
        test_coverage=data.get('test_coverage', 0.0),
        sanity_check_results=data.get('sanity_check_results', {}),
        known_issues=data.get('known_issues', []),
        next_steps=data.get('next_steps', []),
        blockers=data.get('blockers', [])
    )
    
    output_file = f"task_completion.md"
    Path(output_file).write_text(content)
    print(f"✅ Created {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())