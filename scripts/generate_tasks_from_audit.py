#!/usr/bin/env python3
"""
Generate BOARD.md task entries and inbox assignments from audit report.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class TaskGenerator:
    def __init__(self):
        self.workspace = Path.cwd()
        self.audit_file = self.workspace / "docs" / "audit_report_comprehensive.json"
        self.board_file = self.workspace / "BOARD.md"
        self.inbox_dir = self.workspace / "WORKSPACE" / "INBOXES"
        
        self.audit_data = None
        self.task_counter = {
            "P3-VD": 25,  # Start after existing P3-VD24
            "P4-AU": 1,
            "P5-VE": 1,
            "P5-DM": 1,
            "P5-MO": 2,  # Start after P5-M01
            "P6-GE": 5,  # Start after P6-G4
            "P6-P3": 1,  # Particle/3D
            "P6-QC": 5,  # Start after P6-Q4
            "P6-AG": 4,  # Start after P6-AG4
            "P7-VE": 0,
            "P8-OT": 1,
        }
        
    def load_audit(self):
        with open(self.audit_file) as f:
            self.audit_data = json.load(f)
            
    def get_phase_for_category(self, category: str) -> str:
        """Map category to phase number."""
        mapping = {
            "Depth": "3",
            "Audio": "4",
            "V-Effect": "5",
            "Datamosh": "5",
            "Modulator": "5",
            "Generator": "6",
            "Particle/3D": "6",
            "Quantum/AI": "6",
            "Other": "7",  # Visual effects, utilities, etc.
        }
        return mapping.get(category, "7")
    
    def get_task_id(self, category: str, plugin_name: str, class_name: str) -> str:
        """Generate unique task ID."""
        phase = self.get_phase_for_category(category)
        
        # Determine sub-phase prefix
        if category == "Depth":
            prefix = "P3-VD"
            counter_key = "P3-VD"
        elif category == "Audio":
            prefix = "P4-AU"
            counter_key = "P4-AU"
        elif category == "V-Effect":
            prefix = "P5-VE"
            counter_key = "P5-VE"
        elif category == "Datamosh":
            prefix = "P5-DM"
            counter_key = "P5-DM"
        elif category == "Modulator":
            prefix = "P5-MO"
            counter_key = "P5-MO"
        elif category == "Generator":
            prefix = "P6-GE"
            counter_key = "P6-GE"
        elif category == "Particle/3D":
            prefix = "P6-P3"
            counter_key = "P6-P3"
        elif category == "Quantum/AI":
            prefix = "P6-QC"
            counter_key = "P6-QC"
        else:  # Other
            prefix = "P7-VE"
            counter_key = "P7-VE"
            
        self.task_counter[counter_key] += 1
        return f"{prefix}{self.task_counter[counter_key]:02d}"
    
    def sanitize_name(self, name: str) -> str:
        """Convert plugin name to safe filename."""
        return name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "").replace("*", "_")
    
    def generate_task_row(self, plugin: dict) -> str:
        """Generate a markdown table row for the task."""
        task_id = self.get_task_id(plugin['category'], plugin['name'], plugin['class_name'])
        plugin_name = plugin['name']
        class_name = plugin['class_name']
        source = plugin['source']
        
        # Determine priority
        priority = "P0" if plugin['category'] in ["Depth", "Audio"] else "P1"
        
        # Create spec reference
        spec_name = f"P{self.get_phase_for_category(plugin['category'])}-{task_id}_{self.sanitize_name(plugin_name)}.md"
        spec_path = f"docs/specs/{spec_name}"
        
        row = f"| {task_id} | {plugin_name} ({class_name}) | {priority} | ⬜ Todo | {source} |\n"
        return row, task_id, spec_path
    
    def generate_spec_template(self, plugin: dict, task_id: str) -> str:
        """Generate a basic spec file template."""
        plugin_name = plugin['name']
        class_name = plugin['class_name']
        source = plugin['source']
        file_path = plugin['file_path']
        description = plugin.get('description', '')
        
        spec_content = f"""# {task_id}: {plugin_name}

> **Task ID:** `{task_id}`  
> **Priority:** P0 (Critical)  
> **Source:** {source} (`{file_path}`)  
> **Class:** `{class_name}`  
> **Phase:** Phase {self.get_phase_for_category(plugin['category'])}  
> **Status:** ⬜ Todo  

## Mission Context

Port the `{class_name}` effect from `{source}` codebase into VJLive3's clean architecture. This plugin is part of the {plugin['category']} collection and is essential for complete feature parity.

## Technical Requirements

- Implement as a VJLive3 plugin following the manifest-based registry system
- Inherit from appropriate base class (likely `Effect` or specialized depth/audio base)
- Ensure 60 FPS performance (Safety Rail 1)
- Achieve ≥80% test coverage (Safety Rail 5)
- File size ≤750 lines (Safety Rail 4)
- No silent failures, proper error handling (Safety Rail 7)

## Implementation Notes

**Original Location:** `{source}/{file_path}`  
**Description:** {description if description else 'No description available'}

### Porting Strategy

1. Study the original implementation in `{source}/{file_path}`
2. Identify dependencies and required resources (shaders, textures, etc.)
3. Adapt to VJLive3's plugin architecture (see `src/vjlive3/plugins/`)
4. Write comprehensive tests (≥80% coverage)
5. Verify against original behavior with test vectors
6. Document any deviations or improvements

## Verification Checkpoints

- [ ] Plugin loads successfully via registry
- [ ] All parameters exposed and editable
- [ ] Renders at 60 FPS minimum
- [ ] Test coverage ≥80%
- [ ] No safety rail violations
- [ ] Original functionality verified (side-by-side comparison)

## Resources

- Original source: `{source}/{file_path}`
- Audit report: `docs/audit_report_comprehensive.json`
- Plugin system spec: `docs/specs/P1-P1_plugin_registry.md` (or appropriate)
- Base classes: `src/vjlive3/plugins/`, `src/vjlive3/render/`

## Dependencies

- [ ] List any dependencies on other plugins or systems

---

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.

"""
        return spec_content
    
    def generate_inbox_assignment(self, task_id: str, plugin_name: str, spec_path: str, category: str) -> str:
        """Generate inbox assignment file content."""
        phase = self.get_phase_for_category(category)
        assignment = f"""# Task Assignment: {task_id}

> **From:** Manager (ROO CODE)
> **To:** Implementation Engineer (Alpha)
> **Task ID:** `{task_id}`
> **Plugin:** {plugin_name}
> **Spec:** `{spec_path}`
> **Priority:** P0 (Critical)
> **Phase:** Phase {phase}

## Mission

Port the `{plugin_name}` effect from the legacy codebases into VJLive3's clean architecture. This is a **bespoke** plugin port — treat it as a unique snowflake, not a batch job.

## Immediate Actions

1. Read the specification file: `{spec_path}`
2. Study the original implementation in the legacy codebase (see spec for location)
3. Create the plugin file in `src/vjlive3/plugins/`
4. Implement the effect following VJLive3 patterns
5. Write comprehensive tests in `tests/plugins/`
6. Verify 60 FPS performance and ≥80% test coverage
7. Update BOARD.md status to ✅ Done
8. Notify Manager via the Antigravity Chat

## Technical Constraints

- **60 FPS Sacred:** No frame drops
- **750-Line Limit:** Keep files concise
- **80% Coverage:** Minimum test coverage
- **Zero Silent Failures:** All errors must be explicit
- **Bespoke Treatment:** Every plugin gets individual attention

## Workflow

```
SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD
```

Do not proceed to next task until this one is complete and verified.

## Resources

- Audit report: `docs/audit_report_comprehensive.json`
- Plugin system: `src/vjlive3/plugins/`
- Examples: See existing plugins in `src/vjlive3/plugins/` (depth_*, audio_*, etc.)
- Base classes: `Effect`, `DepthEffect`, `AudioEffect` as appropriate

## Communication

- Use Antigravity Chat for questions
- Report any blockers immediately
- Document any deviations from original behavior

**Remember:** The best code is code that knows what it is and does it well.

"""
        return assignment
    
    def run(self):
        """Generate all tasks and assignments."""
        self.load_audit()
        
        # Read current BOARD.md
        board_content = self.board_file.read_text()
        
        # Find insertion point (after P0-INF2 section, before Phase 1)
        insertion_marker = "### P0-INF2: Legacy Feature Parity Analysis & Implementation Plan"
        lines = board_content.split('\n')
        
        # We'll insert new tasks in appropriate phase sections
        # For now, let's generate all task entries and write to separate files
        # Then we'll update BOARD.md by inserting into each phase section
        
        tasks_by_phase = defaultdict(list)
        
        print(f"Processing {len(self.audit_data['missing_plugins'])} missing plugins...")
        
        for plugin in self.audit_data['missing_plugins']:
            category = plugin['category']
            phase = self.get_phase_for_category(category)
            
            # Skip certain base classes and infrastructure
            if plugin['class_name'].endswith('Base'):
                print(f"  Skipping base class: {plugin['class_name']}")
                continue
                
            task_row, task_id, spec_path = self.generate_task_row(plugin)
            tasks_by_phase[phase].append({
                'task_id': task_id,
                'row': task_row,
                'spec_path': spec_path,
                'plugin': plugin
            })
            
            # Create spec file
            spec_full_path = self.workspace / spec_path
            spec_full_path.parent.mkdir(parents=True, exist_ok=True)
            spec_content = self.generate_spec_template(plugin, task_id)
            spec_full_path.write_text(spec_content)
            print(f"  Created spec: {spec_path}")
            
            # Create inbox assignment
            inbox_file = self.inbox_dir / f"inbox_{task_id.lower()}.md"
            assignment_content = self.generate_inbox_assignment(task_id, plugin['name'], spec_path, plugin['category'])
            inbox_file.write_text(assignment_content)
            print(f"  Created inbox: {inbox_file.name}")
            
        print(f"\nGenerated {sum(len(v) for v in tasks_by_phase.values())} tasks")
        
        # Now update BOARD.md by inserting tasks into appropriate phase sections
        # This is complex due to markdown table structure
        # For now, I'll create a summary report
        summary_file = self.workspace / "docs" / "task_generation_summary.md"
        with open(summary_file, 'w') as f:
            f.write("# Task Generation Summary\n\n")
            f.write(f"Generated on: {datetime.now()}\n\n")
            for phase in sorted(tasks_by_phase.keys()):
                f.write(f"## Phase {phase}\n\n")
                f.write(f"Total tasks: {len(tasks_by_phase[phase])}\n\n")
                for task in sorted(tasks_by_phase[phase], key=lambda x: x['task_id']):
                    f.write(f"- {task['task_id']}: {task['plugin']['name']} ({task['plugin']['class_name']})\n")
                f.write("\n")
        print(f"Summary written to: {summary_file}")
        
        print("\nNext steps: Manually integrate these tasks into BOARD.md table structure.")
        print("Or I can write a more sophisticated BOARD.md updater.")

if __name__ == "__main__":
    gen = TaskGenerator()
    gen.run()
