# Contributing to MCP Architecton

Thank you for your interest in contributing to MCP Architecton! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip
- Git

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Anselmoo/mcp-architecton.git
   cd mcp-architecton
   ```

2. **Set up development environment:**
   ```bash
   # Using uv (recommended)
   uv sync --dev

   # Or using pip
   pip install -e .[dev]
   ```

3. **Install pre-commit hooks:**
   ```bash
   uv run pre-commit install
   # Or: pre-commit install
   ```

## Development Workflow

### Code Quality

We use comprehensive code quality tools to maintain high standards:

- **Ruff**: For linting and formatting
- **MyPy**: For type checking
- **Bandit**: For security analysis
- **Pre-commit**: For automated checks

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/mcp_architecton

# Run specific test file
uv run pytest tests/test_specific.py
```

### Using Tox for Comprehensive Testing

We use tox to test across multiple environments:

```bash
# Run all tox environments
uv run tox

# Run specific environments
uv run tox -e lint                 # Linting only
uv run tox -e type-check          # Type checking only
uv run tox -e coverage            # Coverage report
uv run tox -e security            # Security checks
uv run tox -e py311               # Tests on Python 3.11
```

### Code Style and Linting

We follow strict code quality standards:

```bash
# Auto-fix linting issues
uv run ruff check --fix .
uv run ruff format .

# Check without fixing
uv run ruff check .
uv run ruff format --check .

# Type checking
uv run mypy src/mcp_architecton

# Security check
uv run bandit -r src/
```

### Pre-commit Hooks

All commits are automatically checked for:

- Code formatting (Ruff)
- Linting issues (Ruff)
- Type checking (MyPy)
- Security issues (Bandit)
- Import sorting and upgrades (pyupgrade)
- General file hygiene
- Secret detection

To run pre-commit manually:

```bash
uv run pre-commit run --all-files
```

## Code Standards

### Test Coverage

- Maintain minimum 65% test coverage
- Add tests for all new functionality
- Include both unit and integration tests

### Type Hints

- All public functions must have type hints
- Use `typing` module annotations for Python 3.10+ compatibility
- Run `mypy` to verify type correctness

### Security

- All code is automatically scanned with Bandit
- Follow secure coding practices
- No hardcoded secrets or credentials

### Documentation

- Add docstrings for public modules, classes, and functions
- Update README.md for user-facing changes
- Include examples in docstrings where helpful

## CI/CD Pipeline

Our comprehensive CI pipeline runs on all pull requests:

1. **Pre-commit checks**: File hygiene, formatting, basic linting
2. **Linting & Static Analysis**: Ruff, MyPy, Bandit security scan
3. **Testing & Coverage**: pytest across Python 3.10, 3.11, 3.12
4. **Quality Gate**: Comprehensive tox environment validation

## Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch from `main`
3. **Make** your changes following the code standards
4. **Test** thoroughly with `tox`
5. **Commit** using conventional commit messages
6. **Push** and create a pull request

### Conventional Commits

We use conventional commit messages:

```
feat: add new pattern detection feature
fix: resolve type hint injection bug
docs: update API documentation
test: add comprehensive coverage for metrics
chore: update dependencies
```

## Getting Help

- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Maintainers will review pull requests promptly

## Additional Resources

- [Python Style Guide](https://peps.python.org/pep-0008/)
- [Type Hints](https://docs.python.org/3/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Tox Documentation](https://tox.wiki/)

Thank you for contributing to MCP Architecton! 🚀