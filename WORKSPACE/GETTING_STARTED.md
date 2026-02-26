# Getting Started with VJLive3

Welcome to VJLive3! This guide will walk you through setting up your development environment and getting started with contributing to the project.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+**: VJLive3 requires Python 3.9 or higher
- **Git**: For version control and collaboration
- **Make**: For build automation (usually pre-installed on Unix systems)
- **Virtual environment tool**: Either `venv` (built-in), `conda`, or `virtualenv`

### Recommended Tools

- **VS Code**: With Python extension for development
- **GitKraken**: For Git GUI operations
- **Docker**: For container-based development (optional)
- **GitHub CLI**: For command-line GitHub operations (optional)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd VJLive3_The_Reckoning
```

### 2. Set Up Development Environment

```bash
# Install development dependencies and set up pre-commit hooks
make install

# Verify installation
make quality
```

This will:
- Create a virtual environment
- Install all dependencies (including dev dependencies)
- Set up pre-commit hooks
- Run initial quality checks

### 3. Run the Application

```bash
# Run with default settings
make run

# Run with debug logging
make run-debug
```

### 4. Run Tests

```bash
# Run all tests with coverage
make test

# Run specific test suite
make test-unit
make test-integration
make test-e2e
make test-performance
```

### 5. Check Code Quality

```bash
# Run all quality checks
make quality

# Individual checks
make lint
make type-check
make security
make format
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Your Changes

- Write code following the [Style Guide](STYLE_GUIDE.md)
- Write tests for new functionality
- Update documentation as needed

### 3. Run Quality Checks

```bash
# Run all quality checks locally
make quality

# Or individually
make lint
make type-check
make test
make security
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature

- Description of what was added
- Why it was added
- Any breaking changes

Closes #123"
```

### 5. Push and Create PR

```bash
git push origin feature/my-feature
```

Then open a Pull Request on GitHub.

## Project Structure

```
VJLive3_The_Reckoning/
├── src/vjlive3/          # Main source code
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
│   └── api/            # API documentation
├── config/             # Configuration files
├── scripts/            # Utility scripts
├── pyproject.toml      # Project configuration
├── Makefile            # Build and task automation
└── .github/workflows/  # CI/CD pipelines
```

## Key Commands

### Development

```bash
# Install dependencies
make install

# Format code
make format

# Run quality checks
make quality

# Run tests
make test

# Run specific test suite
make test-unit
make test-integration
make test-e2e
make test-performance

# Build package
make build

# Clean build artifacts
make clean
```

### Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src/vjlive3 --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_core_pipeline.py -v

# Run with debug logging
pytest -v --log-cli-level=DEBUG

# Run performance tests
pytest tests/performance/ -v --benchmark-only
```

### Quality Gates

```bash
# Linting
ruff check src/
black --check src/
isort --check-only src/

# Type checking
mypy src/

# Security scanning
bandit -r src/
safety check

# Code formatting
black src/
isort src/
ruff check --fix src/
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Development settings
DEBUG=True
LOG_LEVEL=DEBUG

# API keys (if needed)
API_KEY=your_api_key_here

# Database (if needed)
DATABASE_URL=sqlite:///./dev.db
```

### Configuration Files

Configuration is managed through environment variables and the `config/secrets/` directory:

- `.env` file in project root for development settings
- `config/secrets/` contains sensitive credentials (db_url, jwt_secret, redis_url, etc.)
- See `pyproject.toml` for available configuration options

## Testing Strategy

### Unit Tests

- **Scope**: Single function, class, or module
- **Speed**: < 100ms per test
- **Isolation**: No external dependencies (mocked)
- **Coverage**: All business logic, edge cases, error conditions

### Integration Tests

- **Scope**: Multiple components working together
- **Speed**: < 1s per test
- **Dependencies**: Real components (database, file system, etc.)
- **Coverage**: Component interactions, API contracts

### End-to-End Tests

- **Scope**: Complete user workflows
- **Speed**: < 5s per test
- **Environment**: Near-production environment
- **Coverage**: Critical user journeys

### Performance Tests

- **Scope**: Performance characteristics
- **Speed**: Varies (benchmark mode)
- **Metrics**: Latency, throughput, memory, CPU
- **Coverage**: Performance-critical paths

## Code Quality

### Pre-commit Hooks

Pre-commit hooks run automatically on every commit:

- **Black**: Code formatting
- **isort**: Import sorting
- **ruff**: Linting
- **mypy**: Type checking
- **bandit**: Security scanning
- **pydocstyle**: Docstring checking

### Manual Quality Checks

```bash
# Check for print() statements
make check-print-statements

# Check for eval() calls
make check-eval

# Run all code quality checks
make check-all
```

## Architecture

### Core Components

- **VideoPipeline**: Main orchestrator for video processing
- **Effect**: Base class for visual effects
- **Source**: Base class for video sources
- **StateManager**: Centralized state management
- **Config**: Configuration loading and validation

### Design Patterns

- **Pipeline Pattern**: Video processing follows a pipeline
- **Strategy Pattern**: Effects and sources use interchangeable algorithms
- **Observer Pattern**: State changes notify observers
- **Factory Pattern**: Create effects and sources from configuration
- **Command Pattern**: For undo/redo functionality

## Contributing

### Before You Start

1. **Read the documentation**:
   - [README.md](README.md): Project overview
   - [STYLE_GUIDE.md](STYLE_GUIDE.md): Coding standards
   - [TESTING_STRATEGY.md](TESTING_STRATEGY.md): Testing approach
   - [CONTRIBUTING.md](CONTRIBUTING.md): Contribution guidelines

2. **Check existing issues**: Look for similar issues or features

3. **Discuss your idea**: Use GitHub Discussions for questions or ideas

### Development Process

1. **Create a feature branch**: `git checkout -b feature/my-feature`
2. **Make changes**: Follow the style guide and write tests
3. **Run quality checks**: `make quality`
4. **Commit changes**: Use Conventional Commits format
5. **Push and create PR**: Open a Pull Request
6. **Code review**: Address feedback and get approval
7. **Merge**: Clean commit history and merge

### Code Review Checklist

- [ ] Code follows style guide
- [ ] Type hints complete and mypy passes
- [ ] Tests added/updated and passing
- [ ] Coverage requirements met
- [ ] Documentation updated
- [ ] No print() statements
- [ ] No eval() calls
- [ ] Security scan passes
- [ ] Commit messages clear

## Troubleshooting

### Common Issues

#### Installation Problems

```bash
# If installation fails, try:
pip install --upgrade pip setuptools wheel
make install
```

#### Test Failures

```bash
# If tests fail, check:
pytest -v --log-cli-level=DEBUG
```

#### Quality Gate Failures

```bash
# Check specific quality gate
make lint
make type-check
make security
```

#### Git Issues

```bash
# If you have merge conflicts
git status
git add .
git commit -m "Resolve merge conflicts"
```

### Getting Help

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](<issues-url>)
- **Discussions**: [GitHub Discussions](<discussions-url>)
- **Discord**: [Join our community](<discord-url>)

## Performance Tips

### Development

- Use `make run-debug` for detailed logging
- Profile before optimizing: `pytest --benchmark-only`
- Use `make test-performance` for performance tests

### Production

- Use `make build` to create optimized packages
- Monitor performance with quality metrics
- Use appropriate hardware for video processing

## Security Best Practices

- **Never commit secrets**: Use environment variables
- **Validate all inputs**: Check external data
- **Use parameterized queries**: For database operations
- **Keep dependencies updated**: Regular security scans
- **Follow the security policy**: [SECURITY.md](SECURITY.md)

## Learning Resources

### Python

- [Python Official Documentation](https://docs.python.org/3/)
- [Real Python](https://realpython.com/)
- [Python Packaging User Guide](https://packaging.python.org/)

### Testing

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Testing in Python](https://docs.python-guide.org/writing/tests/)

### Code Quality

- [Black Documentation](https://black.readthedocs.io/)
- [ruff Documentation](https://beta.ruff.rs/)
- [mypy Documentation](https://mypy.readthedocs.io/)

### Git

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general chat
- **Discord**: Real-time chat (link in README)
- **Mailing list**: Announcements (subscribe in README)

### Getting Involved

- **Start small**: Fix documentation, add tests
- **Ask questions**: Don't hesitate to ask for help
- **Review code**: Help review others' PRs
- **Share knowledge**: Write tutorials or examples

## Next Steps

1. **Explore the codebase**: Start with `src/vjlive3/main.py`
2. **Run the demo**: `make run` to see it in action
3. **Write your first test**: Add a test to `tests/unit/`
4. **Create your first effect**: Add a new effect to `src/vjlive3/effects/`
5. **Contribute**: Open your first Pull Request

## Acknowledgments

This project was built with:
- ❤️ Love by the VJLive Team
- 📚 Best practices from the Python community
- 🔧 Modern development tools and workflows
- 🧠 Architectural patterns and design principles

---

**Remember**: Quality is built in from the start. If something is too hard to do right, do it the right way instead.

Happy coding! 🚀