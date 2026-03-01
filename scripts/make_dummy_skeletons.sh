#!/bin/bash
OUTPUT_DIR="docs/specs/_01_skeletons"
mkdir -p "$OUTPUT_DIR"

grep "PENDING SKELETON" BOARD.md | while read -r line ; do
    task_id=$(echo "$line" | cut -d'|' -f2 | awk '{$1=$1};1')
    raw_module=$(echo "$line" | cut -d'|' -f3 | awk '{$1=$1};1')
    
    if [[ "$raw_module" == *"("*")"* ]]; then
        module_name=$(echo "$raw_module" | cut -d'(' -f2 | cut -d')' -f1 | awk '{$1=$1};1')
    else
        module_name=$(echo "$raw_module" | awk '{$1=$1};1')
    fi
    
    filename="$OUTPUT_DIR/${task_id}_${module_name}.md"
    
    if [ ! -f "$filename" ]; then
        echo "Creating skeleton for $task_id - $module_name"
        cat << TEMPLATE > "$filename"
# Spec Template — Focus on Technical Accuracy

**File naming:** \`docs/specs/${task_id}_${module_name}.md\`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: ${task_id} — ${module_name}

**What This Module Does**

**What This Module Does NOT Do**

---

## Detailed Behavior and Parameter Interactions

---

## Public Interface

---

## Inputs and Outputs

---

## Edge Cases and Error Handling

---

## Mathematical Formulations

---

## Performance Characteristics

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with \`[Phase-3] ${task_id}: ${module_name}\` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  
TEMPLATE
    fi
done
