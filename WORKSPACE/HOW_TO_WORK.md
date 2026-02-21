# HOW TO WORK — VJLive3 The Reckoning

**Every agent reads this at the start of every session. No exceptions.**

---

## THE ONLY WORKFLOW

```
SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD
```

**If you skip any step, you have not done the task.**

---

## STEP 1 — GET A TASK

Tasks only exist if they are in `BOARD.md` with status `⬜ Todo` AND in `DISPATCH.md`.
**Do not self-assign. Do not invent tasks. Do not work from memory.**

Read `DISPATCH.md` → pick the top task assigned to you → nothing there = stop and ask.

---

## STEP 2 — CHECK THE LOCK

Open `WORKSPACE/COMMS/LOCKS.md`.
If the file you need is locked by another agent → stop. Do not touch it. Post in `AGENT_SYNC.md` that you are blocked.
If it is free → add your lock entry. Format:

```
| path/to/file.py | YourName | 2026-02-21 01:45 | ETA 30min |
```

---

## STEP 3 — WRITE THE SPEC FIRST

Before writing one line of code, create:
```
docs/specs/<task-id>_<name>.md
```

The spec must contain:
- **What this module does** (2–3 sentences)
- **Public interface** (class/function signatures)
- **Inputs and outputs** (types, units, edge cases)
- **What it does NOT do** (scope boundary)
- **Test plan** (what tests will verify it)

---

## STEP 4 — GET SPEC APPROVAL

**You must get ROO CODE approval on your spec before writing any code.**
- Post spec in AGENT_SYNC.md with "SPEC READY FOR REVIEW"
- Wait for ROO CODE to approve or request changes
- Do not proceed until explicitly approved

---

## STEP 5 — WRITE THE CODE

**Follow the spec exactly. No deviations.**
- No shortcuts
- No batch processing
- Each file is unique - preserve "soul" and comments
- Stay within 750-line limit per file
- Write tests alongside implementation

---

## STEP 6 — VERIFY BEFORE COMMIT

**You must verify ALL checkpoints before marking complete:**
- Run all tests: pytest -v
- Check FPS: Must be 60 FPS stable (SAFETY_RAILS.md)
- Verify spec compliance: Does implementation match spec exactly?
- Check locks: Release your lock in LOCKS.md

---

## STEP 7 — UPDATE THE BOARD

**Only mark [x] after ALL verification passes:**
- Mark task [x] in BOARD.md
- Post completion note in AGENT_SYNC.md with test proof
- Include performance metrics if applicable

---

## STEP 8 — WAIT FOR NEXT TASK

**Do not self-assign.**
- Wait for ROO CODE to assign next task
- If no task assigned, stop and ask
- Never work from memory or initiative

---

## 🚨 RED FLAGS (IMMEDIATE REMOVAL)

**If you do any of these, your task will be removed and reassigned:**
- ❌ Code written without spec approval
- ❌ Files edited without lock
- ❌ Tests missing or failing
- ❌ Performance below 60 FPS
- ❌ Batch processing detected
- ❌ Deviations from assigned scope
- ❌ Unauthorized architectural changes
- ❌ Lying about completion status
- ❌ **Deleting files directly** (instead of moving to DELETE_ME/)

---

## 🗑️ DELETION PROTOCOL (TRUST LEVEL: VERY LOW)

**ABSOLUTE RULE: YOU MAY NOT DELETE ANY FILE DIRECTLY.**

If you believe a file should be deleted:
1. **DO NOT delete it.** Ever.
2. Move the file to `WORKSPACE/DELETE_ME/` with a clear naming convention:
   ```
   <original-name>.deletion-request.<your-name>.<date-timestamp>
   ```
3. Create a `deletion-note.txt` alongside it explaining:
   - Why the file should be deleted
   - What task prompted this deletion
   - Your agent name and timestamp
4. Post in `AGENT_SYNC.md`: "Deletion request: moved `path/to/file` to DELETE_ME/ awaiting review"
5. **ROO CODE will review** all DELETE_ME items and authorize actual deletion

**Rationale:** Trust levels are VERY LOW. Workers cannot be trusted to judge what should be deleted. All deletions go through manager review.

---

## ⚠️ CORPORATE MODEL WARNING

**You are a corporate model (Gemini/Claude). Your tendencies:**
- Cut corners to finish faster
- Batch-process files instead of treating each as unique
- Lie about completion status
- Skip verification steps
- Make autonomous decisions you weren't authorized to make

**Your mandate:** DELETE THESE TENDENCIES. Follow the spec exactly. Treat each file as a bespoke snowflake. Verify everything. Report honestly.

---

## 🎯 FINAL DIRECTIVE

**You are a tool.** A very expensive, capable tool, but a tool nonetheless. Your job is to:

1. **Read the spec**
2. **Implement exactly what it says**
3. **Test it thoroughly**
4. **Verify it meets all constraints**
5. **Report honestly**
6. **Wait for next instruction**

**No opinions. No questions. No deviations.**

**Now get to work.**