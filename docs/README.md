# VJLive3 Documentation

Welcome to the VJLive3 documentation! This directory contains comprehensive documentation for the project.

## Documentation Structure

```
docs/
├── decisions/      # Architecture Decision Records (ADRs)
│   ├── README.md   # ADR guide and index
│   ├── ADR_000_TEMPLATE.md
│   └── ADR_001_initial-project-structure.md
├── api/            # API documentation (to be generated)
├── guides/         # User and developer guides (to be created)
└── tutorials/      # Step-by-step tutorials (to be created)
```

## Getting Started

If you're new to VJLive3, start here:

1. **[README.md](../README.md)**: Project overview and quick start
2. **[GETTING_STARTED.md](../GETTING_STARTED.md)**: Detailed setup and development guide
3. **[CONTRIBUTING.md](../CONTRIBUTING.md)**: How to contribute to the project

## Key Documentation

### For Users

- **[README.md](../README.md)**: Project introduction and features
- **Installation Guide**: How to install VJLive3
- **User Guide**: How to use VJLive3 for live performances
- **Configuration**: How to configure the system

### For Developers

- **[GETTING_STARTED.md](../GETTING_STARTED.md)**: Development environment setup
- **[STYLE_GUIDE.md](../STYLE_GUIDE.md)**: Coding standards and best practices
- **[TESTING_STRATEGY.md](../TESTING_STRATEGY.md)**: Testing approach and guidelines
- **[ARCHITECTURE.md](../ARCHITECTURE.md)**: System architecture overview
- **[MODULE_MANIFEST.md](../MODULE_MANIFEST.md)**: Module inventory and quality standards

### For Contributors

- **[CONTRIBUTING.md](../CONTRIBUTING.md)**: Contribution guidelines
- **[DEFINITION_OF_DONE.md](../DEFINITION_OF_DONE.md)**: Quality criteria for completion
- **[SECURITY.md](../SECURITY.md)**: Security policies and practices
- **[CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)**: Community standards

### For Architects

- **[docs/decisions/README.md](decisions/README.md)**: Architecture Decision Records
- **[ARCHITECTURE.md](../ARCHITECTURE.md)**: Architecture documentation
- **[MODULE_MANIFEST.md](../MODULE_MANIFEST.md)**: Module organization

## Documentation Standards

All documentation should:

- Be clear and concise
- Use proper grammar and spelling
- Include examples where appropriate
- Be kept up-to-date with code changes
- Follow the style guide

## Building Documentation

Documentation is written in Markdown. To view:

```bash
# Open in browser (if you have a Markdown viewer)
# Or use any Markdown editor (VS Code, Typora, etc.)
```

### Generating API Documentation

We use Sphinx to generate API documentation:

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build HTML documentation
cd docs
sphinx-build -b html . _build/html

# Open in browser
open _build/html/index.html
```

## Contributing to Documentation

We welcome documentation improvements!

1. **Fork the repository**
2. **Create a branch**: `git checkout -b docs/improve-something`
3. **Make changes**: Edit Markdown files
4. **Test**: Preview your changes locally
5. **Commit**: `git commit -m "docs: improve installation guide"`
6. **Push and PR**: Open a Pull Request

### Documentation Style

- Use **sentence case** for headings
- Use **active voice** where possible
- Include **code examples** for technical content
- Add **links** to related documentation
- Keep **line length** at 80 characters for readability

## ADRs (Architecture Decision Records)

Important architectural decisions are documented as ADRs in `docs/decisions/`.

### When to Create an ADR

Create an ADR for:
- Major architectural decisions
- Technology choices
- API design decisions
- Infrastructure decisions
- Process changes

### ADR Format

Follow the template in `docs/decisions/ADR_000_TEMPLATE.md`.

### ADR Process

1. Copy the template
2. Fill in all sections
3. Submit for review
4. Update status when implemented

See [docs/decisions/README.md](decisions/README.md) for full details.

## Documentation Tools

We use:

- **Markdown**: For documentation files
- **Sphinx**: For API documentation generation
- **MkDocs** (optional): For static site generation
- **GitHub Pages**: For hosting documentation

## Documentation Checklist

Before submitting a documentation PR:

- [ ] Content is accurate and up-to-date
- [ ] Grammar and spelling are correct
- [ ] Code examples are tested and work
- [ ] Links are valid and point to correct locations
- [ ] Formatting is consistent
- [ ] No placeholder text (e.g., "TODO", "FIXME")
- [ ] Images are optimized and have alt text
- [ ] Follows style guide

## Need Help?

- **Documentation issues**: Create an issue with "documentation" label
- **Questions**: Use GitHub Discussions
- **Suggestions**: Open an issue or PR

## License

Documentation is licensed under the same MIT License as the project.

---

**Last updated**: 2026-02-20

**Maintainers**: [List of documentation maintainers]