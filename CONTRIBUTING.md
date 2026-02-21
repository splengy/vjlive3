# Contributing to VJLive3

Thank you for your interest in contributing to VJLive3! This document provides guidelines and information for contributors.

## Code of Conduct

We are committed to a welcoming and inclusive community. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

All contributors must adhere to this code. Violations may result in removal from the community.

## How to Contribute

There are many ways to contribute:

1. **Code**: Fix bugs, add features, improve performance
2. **Documentation**: Improve docs, write tutorials, fix typos
3. **Testing**: Write tests, report bugs, verify fixes
4. **Design**: Improve UI/UX, suggest features
5. **Community**: Help others, moderate discussions
6. **Financial**: Sponsor development via GitHub Sponsors

## Getting Started

### 1. Set Up Development Environment

```bash
# Clone repository
git clone <repository-url>
cd VJLive3_The_Reckoning

# Install dependencies and set up pre-commit hooks
make install

# Verify setup
make quality
```

### 2. Find Something to Work On

- **Good first issues**: Look for `good-first-issue` label
- **Bug reports**: Check existing issues before creating new
- **Feature requests**: Discuss in GitHub Discussions first
- **Documentation**: Anything unclear can be improved

### 3. Create a Branch

```bash
git checkout -b type/short-description

# Examples:
# git checkout -b feature/add-kaleidoscope-effect
# git checkout -b bugfix/fix-memory-leak
# git checkout -b docs/improve-install-guide
```

### 4. Make Changes

- Write code following our [Style Guide](STYLE_GUIDE.md)
- Write tests for new functionality
- Update documentation as needed
- Follow [Definition of Done](DEFINITION_OF_DONE.md)

### 5. Run Quality Checks

```bash
# Run all quality checks locally
make quality

# Or individually
make lint
make type-check
make test
make security
```

### 6. Commit Changes

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .
git commit -m "feat(effects): add kaleidoscope effect

- Implement kaleidoscope shader with configurable segments
- Add UI controls for segment count and rotation
- Add tests for edge cases (odd/even segment counts)

Closes #123"
```

**Commit message format**:
```
type(scope): subject

body

footer
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

### 7. Push and Create PR

```bash
git push origin type/short-description
```

Then open a Pull Request on GitHub with:

- **Clear title**: Summarize changes
- **Description**: Explain what and why
- **Linked issues**: Reference related issues (`Closes #123`)
- **Screenshots**: For UI changes
- **Checklist**: Verify DoD items

### 8. Code Review

- **Be responsive**: Address review comments promptly
- **Be respectful**: Accept constructive feedback
- **Be thorough**: Review your own code before requesting review
- **Be patient**: Reviews may take time

## Pull Request Process

### Requirements

Before PR is ready for review:

- [ ] All checks pass (CI/CD green)
- [ ] Code follows style guide
- [ ] Type hints complete and mypy passes
- [ ] Tests added/updated and passing
- [ ] Coverage requirements met
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Commit history clean (squash if needed)

### Review Process

1. **Automated checks**: CI runs lint, type-check, tests, security
2. **Code review**: At least 1 maintainer reviews
3. **Changes requested**: Address feedback, push new commits
4. **Approval**: Maintainer approves PR
5. **Squash and merge**: Clean commit history

### Rebase vs Merge

We use **squash and merge** to keep history clean:

- Each PR becomes one commit on main
- Commit message follows Conventional Commits
- Original commits preserved in PR discussion

If you need to preserve individual commits:

```bash
# Rebase interactively
git rebase -i origin/main
# Squash commits, then force push
git push -f origin feature/my-feature
```

## Branch Naming Convention

Use descriptive names with prefix:

- `feature/`: New feature
- `bugfix/`: Bug fix
- `hotfix/`: Critical production fix
- `docs/`: Documentation
- `style/`: Code style (formatting, etc.)
- `refactor/`: Code restructuring
- `perf/`: Performance improvement
- `test/`: Test-related changes
- `chore/`: Build/CI changes

Examples:
- `feature/add-ndi-support`
- `bugfix/fix-crash-on-invalid-config`
- `docs/update-readme-with-install-steps`

## Issue Reporting

### Bug Reports

Use the bug report template and include:

- **Environment**: OS, Python version, VJLive3 version
- **Steps to reproduce**: Clear, numbered steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Screenshots/logs**: Visual evidence
- **Additional context**: Anything else relevant

### Feature Requests

Use the feature request template and include:

- **Problem**: What problem does this solve?
- **Solution**: Proposed implementation
- **Alternatives**: Other approaches considered
- **Use case**: Who benefits and how?

### Questions

Use GitHub Discussions for questions:

- **Installation issues**
- **Usage questions**
- **Feature discussions**
- **General chat**

## Development Guidelines

### Code Quality

- **Follow style guide**: [STYLE_GUIDE.md](STYLE_GUIDE.md)
- **Write tests**: Aim for high coverage
- **Type hints**: Complete type annotations
- **Docstrings**: Google style for all public APIs
- **No print()**: Use logging instead
- **No eval()**: Never use these functions

### Testing

- **Unit tests**: Test individual components
- **Integration tests**: Test component interactions
- **E2E tests**: Test complete workflows
- **Performance tests**: For performance-critical code

See [TESTING_STRATEGY.md](TESTING_STRATEGY.md) for details.

### Documentation

- **README**: Keep updated for user-facing changes
- **Docstrings**: Document all public APIs
- **Examples**: Provide usage examples
- **Changelog**: Update for user-visible changes

### Architecture

- **ADR for decisions**: Document significant decisions
- **Follow patterns**: Use established patterns in codebase
- **Minimal changes**: Don't refactor unrelated code
- **Backward compatibility**: Consider impact on users

## Specialized Contributions

### Effect Development

Effects are the heart of VJLive3. To contribute a new effect:

1. Inherit from `vjlive3.effects.base.Effect`
2. Implement required methods
3. Add parameter validation
4. Write comprehensive tests
5. Document with examples
6. Consider performance implications
7. Add to effect registry

### Source Development

New video sources:

1. Inherit from `vjlive3.sources.base.Source`
2. Implement `stream()` generator
3. Handle connection lifecycle
4. Implement error recovery
5. Write tests
6. Document hardware requirements

### UI Contributions

UI changes require extra care:

1. Discuss design in issue/PR first
2. Follow existing UI patterns
3. Ensure accessibility (keyboard nav, screen readers)
4. Test on multiple platforms
5. Consider internationalization (i18n)
6. Document UI changes with screenshots

### Performance Contributions

Performance improvements:

1. Profile before and after
2. Document performance gains
3. Ensure no regressions in tests
4. Consider edge cases
5. Add performance tests if applicable

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general chat
- **Discord**: Real-time chat (link in README)
- **Mailing list**: Announcements (subscribe in README)

### Getting Help

- **Stuck?** Ask in GitHub Discussions
- **Found bug?** Search issues, then report
- **Need guidance?** Tag maintainers in PR
- **Want to chat?** Join Discord

### Code of Conduct

- **Be respectful**: Treat everyone with respect
- **Be inclusive**: Welcome all contributors
- **Be constructive**: Provide helpful feedback
- **Be patient**: Not everyone has same experience

Violations reported to security@vjlive.com will be reviewed confidentially.

## Recognition

Contributors are recognized in:

- **README**: List of contributors
- **CHANGELOG**: Contributions per release
- **GitHub**: Contribution graph
- **Website**: Contributor spotlight (optional)

## License

By contributing, you agree that your contributions will be licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Questions?

- **Code questions**: GitHub Discussions
- **Process questions**: Review this document or ask
- **Security concerns**: security@vjlive.com (private)

---

**Thank you for contributing!** Your efforts make VJLive3 better for everyone.