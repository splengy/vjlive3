# VJLive3 — Documentation

## Structure

```
docs/
├── decisions/       # Architecture Decision Records
├── specs/           # Module specifications (generated from legacy code)
│   ├── _TEMPLATE.md            # Plugin spec template
│   ├── _CORE_TEMPLATE.md       # Core architecture spec template
│   └── _GOLDEN_EXAMPLE_CORE.md # Filled-in example (Video Source)
└── NAME_REGISTRY.json          # Cross-spec naming consistency registry
```

## Workflow

1. **Qdrant ingests legacy code** → real v1/v2 code becomes searchable
2. **Specs generated** → batch script queries Qdrant, produces specs from templates
3. **All specs reviewed** → you review complete picture before any code starts
4. **Code written** → agents implement from verified specs

## Tools

| Script | Purpose |
|--------|---------|
| `scripts/legacy_lookup.py` | Query Qdrant for legacy code references |
| `scripts/validate_spec.py` | Check spec completeness against template |
| `scripts/check_naming.py` | Cross-reference identifiers across specs |
| `scripts/extract_tasks.py` | Parse BOARD.md for pending tasks |
| `scripts/detect_stubs.py` | Find pass-only methods in code |
| `scripts/self_check.py` | Run all checks before submitting |