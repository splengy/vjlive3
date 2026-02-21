# Changelog

All notable changes to VJLive3 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Core video processing pipeline
- Basic effect system
- File source for video playback
- Desktop GUI (Qt-based)
- CLI interface
- Comprehensive test suite
- CI/CD pipeline with GitHub Actions
- Documentation suite

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- N/A (initial release)

## [0.1.0] - YYYY-MM-DD (Upcoming)

### Added
- Project scaffolding with professional tooling
- pyproject.toml with comprehensive configuration
- Pre-commit hooks for quality enforcement
- GitHub Actions CI/CD pipeline
- Complete documentation suite
- Style guide and testing strategy
- Security policy
- Contributing guidelines
- Definition of Done
- Module manifest
- Architecture documentation
- ADR system with template

### Changed
- N/A (initial version)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## Versioning Scheme

- **Major** (X.0.0): Breaking changes, API incompatible
- **Minor** (0.X.0): New features, backward compatible
- **Patch** (0.0.X): Bug fixes, backward compatible

## Release Process

1. **Update CHANGELOG**: Document all changes in [Unreleased]
2. **Update version**: In `pyproject.toml` and `src/vjlive3/__init__.py`
3. **Create release tag**: `git tag -a v0.1.0 -m "Release 0.1.0"`
4. **Build packages**: `make build`
5. **Test packages**: Verify in clean environment
6. **Publish**: `make publish` (to TestPyPI first, then PyPI)
7. **GitHub release**: Create release with changelog
8. **Announce**: Blog post, social media, mailing list

## Categories of Changes

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security-related changes

## Templates

### New Feature Entry

```markdown
### Added
- Feature name: Description
  - Sub-feature 1
  - Sub-feature 2
```

### Bug Fix Entry

```markdown
### Fixed
- Issue #123: Brief description
  - Root cause: [explanation]
  - Solution: [what was changed]
```

### Breaking Change Entry

```markdown
### Changed
- **Breaking**: Description of breaking change
  - Migration guide: How to update code
  - Reason: Why this was necessary
```

## Notes

- Keep entries concise but informative
- Group related changes together
- Credit contributors if appropriate
- Link to related issues/PRs
- Include migration instructions for breaking changes

---

**Template for release notes**:

```markdown
# VJLive3 v0.1.0

## Highlights
- Major feature 1
- Major feature 2
- Major improvement 3

## New Features
- Feature 1
- Feature 2

## Improvements
- Improvement 1
- Improvement 2

## Bug Fixes
- Fix 1
- Fix 2

## Security
- Security update 1
- Security update 2

## Known Issues
- Issue 1 (to be fixed in 0.1.1)
- Issue 2 (workaround: ...)

## Upgrade Notes
- Instructions for upgrading from 0.0.x to 0.1.0
- Breaking changes and migration steps

## Full Changelog
Link to GitHub compare view: https://github.com/org/vjlive3/compare/v0.0.1...v0.1.0