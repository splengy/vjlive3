# ADR-001: Initial Project Structure

## Status
Accepted

## Date
2026-02-20

## Context
We need to establish a professional project structure for VJLive3 that supports:
- Modern Python development practices
- Comprehensive testing and quality gates
- Documentation and decision tracking
- CI/CD pipeline integration
- Scalability and maintainability
- Developer experience and onboarding

## Decision
Adopt a standard Python project structure with the following key components:

1. **Source code in `src/vjlive3/`**: Standard Python packaging layout
2. **Tests in `tests/`**: Separate unit, integration, e2e, and performance test directories
3. **Documentation in `docs/`**: Including ADRs, API docs, and guides
4. **Configuration in `config/`**: YAML/JSON config files
5. **Scripts in `scripts/`**: Utility scripts for development
6. **GitHub Actions in `.github/workflows/`**: CI/CD pipeline
7. **Quality tools**: Pre-commit hooks, linters, type checkers
8. **Professional documentation**: README, CONTRIBUTING, STYLE_GUIDE, etc.

## Options Considered

### Option 1: Monolithic structure (all code in root)
- **Pros**: Simple, easy to navigate
- **Cons**: Hard to scale, no clear separation, poor packaging

### Option 2: Flat structure with src/ only
- **Pros**: Standard Python practice, good for packaging
- **Cons**: Limited organization for larger projects

### Option 3: Multi-package structure (src/vjlive3/)
- **Pros**: Clear separation, good for large projects, proper packaging
- **Cons**: Slightly more complex, requires proper imports

### Option 4: Microservices structure (multiple packages)
- **Pros**: Highly scalable, clear boundaries
- **Cons**: Overkill for initial project, complex setup

## Consequences

### Positive
- **Professional**: Follows industry best practices
- **Scalable**: Can grow with project complexity
- **Maintainable**: Clear separation of concerns
- **Testable**: Easy to write and organize tests
- **Documentable**: Clear structure for documentation
- **CI/CD friendly**: Standard structure for automation
- **Onboarding**: Easy for new developers to understand

### Negative
- **Complexity**: More files and directories to manage
- **Learning curve**: New developers need to understand structure
- **Setup time**: More initial setup required

### Neutral
- **Import paths**: Need to use proper import paths
- **Build process**: Standard Python packaging applies

## Related Decisions
- ADR-002: Testing Strategy (depends on test directory structure)
- ADR-003: Documentation Structure (depends on docs directory)
- ADR-004: CI/CD Pipeline (depends on GitHub Actions structure)

## References
- [Python Packaging User Guide](https://packaging.python.org/en/latest/)
- [Structuring Your Project](https://docs.python-guide.org/writing/structure/)
- [The Hitchhiker's Guide to Python](https://docs.python-guide.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

## Implementation Details

### Directory Structure

```
vjlive3/
├── src/vjlive3/          # Main source code
│   ├── __init__.py
│   ├── core/            # Core functionality
│   ├── effects/         # Visual effects
│   ├── sources/         # Video sources
│   └── utils/           # Utilities
├── tests/               # Test suites
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   ├── e2e/            # End-to-end tests
│   └── performance/    # Performance tests
├── docs/               # Documentation
│   ├── decisions/      # Architecture decision records
│   ├── api/            # API documentation
│   └── guides/         # User guides
├── config/             # Configuration files
├── scripts/            # Utility scripts
├── pyproject.toml      # Project configuration
├── Makefile            # Build and task automation
├── .github/workflows/  # CI/CD pipelines
└── docs/decisions/     # ADR directory
```

### Key Files Created

- `pyproject.toml`: Modern Python project configuration
- `Makefile`: Build and development automation
- `.pre-commit-config.yaml`: Quality gates
- `README.md`: Project overview and getting started
- `STYLE_GUIDE.md`: Coding standards
- `TESTING_STRATEGY.md`: Testing approach
- `ARCHITECTURE.md`: System architecture
- `MODULE_MANIFEST.md`: Module inventory
- `SECURITY.md`: Security policies
- `CONTRIBUTING.md`: Contribution guidelines
- `CHANGELOG.md`: Version history

### Quality Gates

- **Pre-commit hooks**: Black, isort, ruff, mypy, bandit
- **CI/CD**: Linting, type checking, security scanning, testing
- **Coverage**: Minimum 80% coverage requirement
- **Documentation**: Docstring and style requirements

### Development Workflow

1. **Setup**: `make install` (creates venv, installs deps, sets up hooks)
2. **Development**: Write code following style guide
3. **Testing**: `make test` (runs all tests with coverage)
4. **Quality**: `make quality` (runs all quality gates)
5. **Commit**: Pre-commit hooks run automatically
6. **PR**: CI/CD runs on every push

### ADR Integration

This ADR is documented in `docs/decisions/ADR_001_initial-project-structure.md` and referenced in:
- `ARCHITECTURE.md`
- `MODULE_MANIFEST.md`
- `CONTRIBUTING.md`
- `TESTING_STRATEGY.md`