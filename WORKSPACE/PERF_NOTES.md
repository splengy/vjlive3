# PERF_NOTES.md — Performance Optimization Registry

> **Workers: add entries here as you code.** Use the standard format below.
> Later, a dedicated optimization task will grep this file and implement the top hits.
> You can also grep the codebase directly: `grep -r "# OPTIM:" src/ --include="*.py"`

---

## How to Add an Entry

**Inline (in code):**
```python
# OPTIM: [brief description] — [why, what to try] — estimated gain: [low/medium/high]
result = [item for item in self._plugins.values()]   # current: O(n) copy every call
```

**In this file (for bigger items):**
```
### [TASK-ID] [file/module] — [title]
- **Cost:** what's being paid right now (CPU, memory, lock contention, etc.)
- **When it hurts:** frame-rate spike? startup latency? plugin-heavy session?
- **Suggestion:** concrete thing to try
- **Estimated gain:** low / medium / high
- **Status:** 📋 Noted / 🔨 In Progress / ✅ Done
```

---

## Conventions

| Comment Tag | Meaning |
|-------------|---------|
| `# OPTIM:` | General performance opportunity |
| `# OPTIM-LOCK:` | Lock contention — consider lock-free structure or finer granularity |
| `# OPTIM-ALLOC:` | Unnecessary allocation in hot path |
| `# OPTIM-IO:` | Blocking I/O that should be async |
| `# OPTIM-GPU:` | GPU/OpenGL call that could be batched or cached |

---

## Registry

### [P1-P1] `plugins/registry.py` — RLock on every list_plugins() call

- **Cost:** `threading.RLock` acquisition on `list_plugins()` and `get_plugin()` — acquired dozens of times per frame tick if nodes are querying for plugin classes.
- **When it hurts:** Node graph ticking at 60fps with 20+ plugin nodes.
- **Suggestion:** Cache `list_plugins()` result in a plain tuple, invalidated only on register/unload. Read path needs no lock for hot queries.
- **Estimated gain:** medium
- **Status:** 📋 Noted

---

### [P1-P1] `plugins/registry.py` — `get_all_modules()` rebuilds list every call

- **Cost:** Iterates all metadata and expands modules array on every call.
- **When it hurts:** Frontend polling or plugin browser refresh.
- **Suggestion:** Cache result, invalidate on any register/unload mutation.
- **Estimated gain:** low–medium
- **Status:** 📋 Noted

---

### [P1-P1] `plugins/loader.py` — `discover_plugins()` does full `rglob` every call

- **Cost:** `Path.rglob('plugin.json')` walks the whole directory tree every scan.
- **When it hurts:** Startup with a large `~/.vjlive3/plugins` directory.
- **Suggestion:** Cache `available_manifests` and only rescan paths whose mtime changed (os.stat).
- **Estimated gain:** medium (startup latency, repeated discovery calls)
- **Status:** 📋 Noted

---

### [P1-P1] `plugins/sandbox.py` — `compile()` called on every `execute()`

- **Cost:** `compile(code, filename, 'exec')` on every sandbox.execute() call.
- **When it hurts:** Hot-reloaded plugins calling execute() every frame.
- **Suggestion:** Cache compiled code objects keyed by (code_hash, filename). Only recompile when code changes.
- **Estimated gain:** medium
- **Status:** 📋 Noted

---

### [P1-P1] `plugins/validator.py` — `ast.parse()` on every validation

- **Cost:** Full AST parse per validation call.
- **When it hurts:** Large plugin with many functions validated at load time.
- **Suggestion:** Cache parse result by file hash. Reparse only when file mtime changes.
- **Estimated gain:** low (validation is one-time at load, not hot-path)
- **Status:** 📋 Noted

---

## Completed Optimizations

_(None yet — section reserved for moved entries after implementation)_
