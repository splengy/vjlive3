# Definition of Done (DoD)

This document defines the quality criteria that must be met before any work is considered complete and ready for merge into the main branch.

## General Principles

- **No compromises on quality**: Every item in this DoD must be satisfied.
- **Automation first**: Manual checks should be automated where possible.
- **Continuous improvement**: The DoD may evolve as the project matures.

## Code Quality Criteria

### 1. Code Implementation

- [ ] **No print() statements**: All debugging output must use the logging system
- [ ] **No eval() or exec()**: These are strictly forbidden for security reasons
- [ ] **Type hints complete**: All function signatures have proper type annotations
- [ ] **No type errors**: `mypy` passes with 0 errors
- [ ] **No lint errors**: `ruff` passes with 0 errors
- [ ] **Formatted correctly**: `black` formatting applied
- [ ] **Imports organized**: `isort` has been run
- [ ] **No security vulnerabilities**: `bandit` scan passes
- [ ] **No known vulnerabilities**: `safety check` passes

### 2. Testing

- [ ] **Tests written**: New functionality has corresponding tests
- [ ] **Tests pass**: All tests pass locally (`pytest` returns 0)
- [ ] **Coverage maintained**: Overall coverage ≥ 80%
- [ ] **Coverage not decreased**: New code coverage ≥ 80% (or same as baseline)
- [ ] **Unit tests**: All business logic has unit tests
- [ ] **Integration tests**: Component interactions tested
- [ ] **E2E tests**: Critical user journeys covered
- [ ] **Performance tests**: Performance-critical code has benchmarks

### 3. Documentation

- [ ] **Code documented**: All public APIs have docstrings (Google style)
- [ ] **Docstrings valid**: `pydocstyle` passes
- [ ] **README updated**: User-facing changes reflected in README
- [ ] **Architecture updated**: Significant architectural changes documented in ARCHITECTURE.md
- [ ] **ADR created**: Architectural decisions recorded in docs/decisions/
- [ ] **Changelog updated**: Entry added to CHANGELOG.md

### 4. Git & Workflow

- [ ] **Branch naming**: Branch follows convention (feature/, bugfix/, hotfix/, etc.)
- [ ] **Atomic commits**: Each commit is a logical, complete unit
- [ ] **Commit messages**: Follow Conventional Commits format
- [ ] **No merge commits**: Use rebase and squash
- [ ] **Pre-commit hooks pass**: All hooks pass automatically
- [ ] **No WIP commits**: No "WIP" or incomplete commits

### 5. Security

- [ ] **Secrets not committed**: No API keys, passwords, or tokens in code
- [ ] **Dependencies scanned**: No known vulnerabilities in dependencies
- [ ] **Input validated**: All external inputs validated
- [ ] **Error handling**: Errors handled gracefully, no information leakage
- [ ] **Authentication/Authorization**: Properly implemented if applicable

### 6. Performance

- [ ] **No performance regressions**: Benchmarks show no degradation
- [ ] **Memory usage acceptable**: No memory leaks detected
- [ ] **CPU usage reasonable**: No unnecessary CPU consumption
- [ ] **Async where appropriate**: I/O operations use async/await

### 7. User Experience

- [ ] **Error messages clear**: Users understand what went wrong
- [ ] **Logging appropriate**: Log levels used correctly (DEBUG, INFO, WARNING, ERROR)
- [ ] **Configuration validated**: Invalid config rejected with clear errors
- [ ] **Graceful degradation**: System handles missing dependencies/resources

## Checklist for Pull Requests

Before creating a PR, verify all items:

```bash
# Run all quality checks
make quality

# Check for print/eval
make check-all

# Run full test suite
make test

# Verify formatting
black --check src/
isort --check-only src/
```

## Exceptions

Rarely, an exception may be needed (e.g., critical security fix). In such cases:

1. Document the exception in the PR description
2. Get explicit approval from at least 2 maintainers
3. Create a follow-up ticket to address the gap
4. Update the DoD if the exception reveals a systemic issue

## Enforcement

- **CI/CD pipeline**: All checks run automatically on PR
- **Branch protection**: Main branch requires passing CI and review
- **Manual review**: Code reviewers verify DoD compliance
- **Merge blocking**: Any failed check blocks merge

## Continuous Improvement

The DoD should be reviewed quarterly. Suggestions for improvement can be submitted as issues or PRs.

---

**Remember**: Quality is not an afterthought—it's built in from the start. If something is too hard to do right, do it the right way instead.