# Evolution Rules — VJLive3 Iterative Development

> "More parameters. Wider ranges. Every knob is a dramatic expression."

These rules govern how code evolves after initial implementation.
They apply to ALL agents (worker, manager, performer) at ALL times.

---

## The Rules

### 1. Improve Without Breaking
You may improve any implementation — better math, faster rendering,
cleaner code — as long as existing functionality is preserved.
**If it worked before your change, it must work after.**

### 2. Parameters Are Append-Only
- ✅ **ADD** new parameters where the plugin can benefit
- ✅ **WIDEN** parameter ranges (e.g., 0-5 → 0-10)
- ✅ **ADD** default values to new parameters so existing patches survive
- ❌ **NEVER REMOVE** an existing parameter
- ❌ **NEVER RENAME** an existing parameter ID
- ❌ **NEVER NARROW** a parameter range

A performer (human or agent) may have saved a patch using that parameter.
Removing it breaks their work. Renaming it breaks their muscle memory.

### 3. Log Breaking Suggestions
If you believe a change would improve the architecture but requires
breaking existing interfaces, **do not make the change**. Instead,
log it in `WORKSPACE/COMMS/BREAKING_SUGGESTIONS.md` with:
- What you'd change
- Why it would be better
- What it would break
- How many files are affected

The User reviews these and decides when/if to act on them.

### 4. Every Knob Is a Dramatic Expression
Parameters are not technical controls. They are performance instruments.
Design them for dramatic range:
- `0.0` should be "completely off" or "minimum effect"
- `10.0` should be "maximum intensity" or "overwhelming"
- The middle range (3-7) should be where most performance happens
- The extremes (0-1 and 9-10) should produce dramatic results

**Bad parameter:** `blur_kernel_size` (0.0 = 1px, 10.0 = 3px)
**Good parameter:** `blur_intensity` (0.0 = crystal clear, 10.0 = total smear)

### 5. Maximum Agent Explorability
Design every plugin so an agent performer can discover its capabilities
through its metadata alone:
- `METADATA` dict must describe every parameter with `id`, `name`, `min`, `max`, `default`
- Parameter names should be human-readable (not `p1`, `val_a`)
- Group related parameters logically
- Include `description` fields that explain what the parameter FEELS like, not just what it does

An agent should be able to read the metadata and say:
*"If I set `feedback_amount` to 8 and `decay` to 2, I'll get intense
trails that linger. Let me try that."*

### 6. Carbon-Silicon Parity
Every parameter exposed to an agent performer MUST be equally accessible
to a human performer, and vice versa. There is no agent-only API.
There is no human-only control panel. The control surface is shared.

The 0-10 float range is the common language. Both species speak it.

### 7. Easter Eggs Welcome
If you discover an interesting parameter combination during development,
document it as a hidden feature or preset. Easter eggs for:
- **Performers** — parameter combos that unlock unexpected visuals
- **Programmers** — clever code comments, elegant solutions
- **Agents** — metadata hints, explorability shortcuts

---

## When to Apply These Rules

| Phase | Apply? |
|-------|--------|
| Writing specs | ✅ Specs should define parameters as append-only |
| Initial implementation | ✅ Design for dramatic range from day one |
| Iterative improvement | ✅ THIS IS THE PRIMARY USE CASE |
| Bug fixes | ✅ Fix without removing parameters |
| Refactoring | ✅ Internal changes only, interface stays stable |
| Architecture changes | ⚠️ Log in BREAKING_SUGGESTIONS.md |

---

*These rules are enforced by code review and the AHOS validator pipeline.*
*Last updated: 2026-02-24*
