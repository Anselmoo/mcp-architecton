# Pre-commit Setup and Usage

## Overview

This project uses pre-commit hooks to automatically check code quality, security, and formatting before commits. The configuration includes state-of-the-art tools for comprehensive code validation.

## Quick Setup

### 1. Install Dependencies

```bash
# Install with uv (recommended)
uv sync --dev

# Or with pip
pip install pre-commit
```

### 2. Install Pre-commit Hooks

```bash
# Install the git hooks
pre-commit install

# Verify installation
pre-commit --version
```

### 3. Run Initial Check

```bash
# Run on all files (first time setup)
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

## What Gets Checked

### File Hygiene
- **Large files**: Prevents accidentally committing large files
- **Syntax**: Validates Python AST, YAML, TOML, JSON
- **Formatting**: Fixes trailing whitespace, end-of-file formatting
- **Conflicts**: Detects merge conflicts and case conflicts
- **Security**: Detects accidentally committed private keys

### Security Scanning
- **Bandit**: Static security analysis for Python code
  - Scans for common security issues
  - Configured via `pyproject.toml`
  - Excludes test files and examples
- **Safety**: Dependency vulnerability scanning
  - Checks for known vulnerabilities in dependencies
  - JSON output for detailed reporting

### Type Checking
- **MyPy**: Static type analysis
  - Configured for gradual adoption
  - Ignores missing imports initially
  - Helps catch type-related bugs early

### Code Quality
- **Ruff**: Ultra-fast Python linter and formatter
  - Replaces flake8, black, isort, and more
  - Auto-fixes many issues automatically  
  - Comprehensive rule set configured in `pyproject.toml`
- **PyUpgrade**: Modernizes Python syntax
  - Updates to Python 3.10+ syntax automatically
  - Keeps code using latest language features

### Documentation
- **Commitizen**: Standardizes commit messages
  - Enforces conventional commit format
  - Enables automatic changelog generation
- **Markdownlint**: Lints markdown files
  - Ensures consistent documentation formatting
  - Configurable via `.markdownlint.yaml`
- **Interrogate**: Checks docstring coverage
  - Enforces minimum documentation standards
  - Configurable threshold (currently 70%)

## Configuration Files

### .pre-commit-config.yaml
Main configuration defining all hooks and their settings.

### pyproject.toml
Contains tool-specific configurations:

```toml
[tool.bandit]
exclude_dirs = ["tests", "examples"]
skips = ["B101", "B601"]  # Allow assert statements and shell=True

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Gradual adoption
ignore_missing_imports = true

[tool.commitizen]
name = "cz_conventional_commits"
version = "0.1.0"
tag_format = "v$version"
```

### .markdownlint.yaml
Configures markdown linting rules for documentation.

## Usage Scenarios

### Regular Development

Pre-commit runs automatically on `git commit`:

```bash
# Make changes
git add .

# Commit triggers pre-commit automatically
git commit -m "feat: add new feature"
```

### Manual Execution

```bash
# Run on staged files
pre-commit run

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run bandit

# Run with verbose output
pre-commit run --verbose --all-files
```

### Bypassing Hooks

For emergency commits (use sparingly):

```bash
# Skip all hooks
git commit --no-verify -m "emergency fix"

# Skip specific checks (better approach)
git commit -m "fix: emergency" && pre-commit run --all-files
```

## Troubleshooting

### Common Issues

1. **Hook Installation Fails**
   ```bash
   # Clear cache and reinstall
   pre-commit clean
   pre-commit install --install-hooks
   ```

2. **Dependency Conflicts**
   ```bash
   # Update pre-commit environment
   pre-commit autoupdate
   ```

3. **Slow Initial Run**
   ```bash
   # First run installs all tools - this is normal
   # Subsequent runs are much faster
   ```

4. **Tool Not Found Errors**
   ```bash
   # Ensure dev dependencies are installed
   uv sync --dev
   ```

### Tool-Specific Issues

**Bandit False Positives:**
- Configure exclusions in `pyproject.toml`
- Use `# nosec` comments for specific lines
- Example: `subprocess.run(cmd, shell=True)  # nosec B602`

**MyPy Type Errors:**
- Start with `ignore_missing_imports = true`
- Gradually add type annotations
- Use `# type: ignore` for complex cases

**Ruff Auto-fixes:**
- Review changes before committing
- Some fixes might change behavior
- Configure rule exclusions if needed

**Safety Vulnerabilities:**
- Review CVE details carefully
- Update dependencies when possible
- Use `--ignore` for unavoidable issues

## Integration with IDE

### VS Code
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### PyCharm
- Install Ruff plugin
- Configure external tools for pre-commit
- Set up commit hooks integration

## Customization

### Adding New Hooks

Edit `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/new-tool/pre-commit-hook
  rev: v1.0.0
  hooks:
    - id: new-tool
      args: [--config, config.yaml]
```

### Modifying Tool Behavior

Most tools are configured via `pyproject.toml`:

```toml
[tool.ruff]
# Add new rule exclusions
extend-ignore = ["E501", "D100"]

[tool.bandit]
# Exclude additional directories
exclude_dirs = ["tests", "examples", "migrations"]
```

### Performance Optimization

```yaml
# Use local environment instead of isolated
- repo: local
  hooks:
    - id: ruff
      name: ruff
      entry: ruff
      language: system
```

## Best Practices

1. **Run Regularly**: Don't let issues accumulate
2. **Understand Failures**: Read error messages carefully
3. **Gradual Adoption**: Start with warnings, then enforce
4. **Team Coordination**: Ensure all team members use same setup
5. **Keep Updated**: Regularly update hook versions
6. **Document Exceptions**: Comment any rule bypasses

## CI Integration

Pre-commit can also run in CI:

```yaml
# .github/workflows/pre-commit.yml
- uses: pre-commit/action@v3.0.1
  with:
    extra_args: --all-files --show-diff-on-failure
```

## Monitoring and Metrics

Track pre-commit effectiveness:
- Count of issues caught before CI
- Time saved by early detection
- Code quality improvements over time
- Security vulnerabilities prevented

The pre-commit system is designed to be your first line of defense for code quality, catching issues early in the development process and maintaining consistent standards across the entire codebase.