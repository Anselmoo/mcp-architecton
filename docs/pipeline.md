# Pipeline Documentation

## Overview

The MCP Architecton pipeline provides a comprehensive, modular, and reproducible framework for code quality, security, and analysis workflows. It's designed to be state-of-the-art with modern DevOps practices.

## Features

- **Modular Architecture**: Each stage is independent and reusable
- **Security Scanning**: Bandit for code security, Safety for dependency vulnerabilities  
- **Code Quality**: Ruff linting/formatting, MyPy type checking, complexity analysis
- **Testing**: Comprehensive test execution with coverage reporting
- **Analysis**: Architecture and design pattern detection
- **Caching**: Intelligent caching for performance optimization
- **Reporting**: JSON and HTML reports for results visualization
- **Reproducibility**: Consistent environments and deterministic execution

## Quick Start

### Using the CLI

```bash
# Run the complete pipeline
python scripts/run_pipeline.py

# Run with verbose output
python scripts/run_pipeline.py --verbose

# Run only security scanning
python scripts/run_pipeline.py --stage security

# Generate default configuration
python scripts/run_pipeline.py --generate-config

# Run with custom configuration
python scripts/run_pipeline.py --config my-config.json
```

### Using UV/Scripts

If you have the package installed:

```bash
# Run the pipeline
uv run architecton-pipeline

# Install and run
uv sync --dev
uv run scripts/run_pipeline.py
```

## Pipeline Stages

### 1. Security Stage

Scans for security vulnerabilities and unsafe code patterns.

**Tools:**
- **Bandit**: Static security analysis for Python code
- **Safety**: Dependency vulnerability scanning

**Configuration:**
```json
{
  "security": {
    "fail_on_high": true,
    "fail_on_medium": false
  }
}
```

**Outputs:**
- Security vulnerability reports
- Risk assessment summaries
- Detailed findings with severity levels

### 2. Quality Stage

Enforces code quality standards and best practices.

**Tools:**
- **Ruff**: Fast linting and formatting
- **MyPy**: Static type checking
- **Radon**: Code complexity analysis

**Configuration:**
```json
{
  "quality": {
    "fix_issues": false,
    "fail_on_errors": true
  }
}
```

**Outputs:**
- Lint error reports
- Type checking results  
- Code complexity metrics
- Formatting compliance

### 3. Testing Stage

Executes comprehensive test suites with coverage analysis.

**Tools:**
- **Pytest**: Test execution framework
- **Coverage.py**: Code coverage measurement
- **Pytest-benchmark**: Performance benchmarking (optional)

**Configuration:**
```json
{
  "testing": {
    "coverage_threshold": 35.0,
    "run_benchmarks": false,
    "parallel": true
  }
}
```

**Outputs:**
- Test execution results
- Coverage reports (XML, HTML)
- Performance benchmarks
- JUnit XML for CI integration

### 4. Analysis Stage

Performs specialized code analysis for architecture and patterns.

**Tools:**
- **MCP Architecton**: Architecture pattern detection
- **Radon**: Maintainability index calculation
- **Custom analyzers**: Design pattern recognition

**Configuration:**
```json
{
  "analysis": {
    "run_architecture_analysis": true,
    "run_pattern_analysis": true
  }
}
```

**Outputs:**
- Detected architecture patterns
- Design pattern analysis
- Maintainability metrics
- Code structure insights

## Configuration

### Default Configuration

Generate a default configuration file:

```bash
python scripts/run_pipeline.py --generate-config
```

This creates `pipeline-config.json`:

```json
{
  "name": "mcp-architecton-pipeline",
  "fail_fast": true,
  "output_dir": "pipeline-output",
  "security": {
    "fail_on_high": true,
    "fail_on_medium": false
  },
  "quality": {
    "fix_issues": false,
    "fail_on_errors": true
  },
  "testing": {
    "coverage_threshold": 35.0,
    "run_benchmarks": false,
    "parallel": true
  },
  "analysis": {
    "run_architecture_analysis": true,
    "run_pattern_analysis": true
  },
  "python_version": "3.10",
  "use_cache": true,
  "cache_dir": ".pipeline-cache"
}
```

### Customization

#### Security Configuration

```json
{
  "security": {
    "fail_on_high": true,      // Fail pipeline on high severity issues
    "fail_on_medium": false    // Continue on medium severity issues
  }
}
```

#### Quality Configuration

```json
{
  "quality": {
    "fix_issues": true,        // Auto-fix linting issues when possible
    "fail_on_errors": false    // Don't fail on type errors (warnings only)
  }
}
```

#### Testing Configuration

```json
{
  "testing": {
    "coverage_threshold": 80.0,  // Require 80% test coverage
    "run_benchmarks": true,      // Enable performance benchmarking
    "parallel": true             // Run tests in parallel
  }
}
```

## Caching

The pipeline includes intelligent caching to improve performance on repeated runs.

**Features:**
- Stage-level result caching
- Input-based cache invalidation
- Configurable cache directory
- Cache statistics and management

**Usage:**
```bash
# Disable caching
python scripts/run_pipeline.py --no-cache

# Check cache statistics (in logs)
python scripts/run_pipeline.py --verbose
```

## Reporting

### JSON Reports

Detailed machine-readable reports:
- `pipeline-summary.json`: Overall pipeline results
- `security/bandit-report.json`: Security findings
- `quality/ruff-lint-report.json`: Linting results
- `testing/coverage.xml`: Coverage data

### HTML Reports

Human-readable visualizations:
- `pipeline-report.html`: Interactive dashboard
- Color-coded stage results
- Expandable error details
- Performance metrics

## Integration

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
- name: Run Pipeline
  run: |
    uv sync --dev
    uv run scripts/run_pipeline.py --verbose
    
- name: Upload Reports
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: pipeline-reports
    path: pipeline-output/
```

### Pre-commit Integration

The pipeline stages are designed to work with pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pipeline-security
        name: Security scan
        entry: python scripts/run_pipeline.py --stage security
        language: python
        pass_filenames: false
```

## Troubleshooting

### Common Issues

1. **Module Import Errors**
   ```bash
   # Ensure proper Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

2. **Missing Dependencies**
   ```bash
   # Install all dev dependencies
   uv sync --dev
   ```

3. **Permission Errors**
   ```bash
   # Make script executable
   chmod +x scripts/run_pipeline.py
   ```

### Debug Mode

Enable verbose logging for detailed information:

```bash
python scripts/run_pipeline.py --verbose
```

### Selective Execution

Run individual stages for debugging:

```bash
# Test only security scanning
python scripts/run_pipeline.py --stage security --verbose

# Test with specific output directory
python scripts/run_pipeline.py --output-dir debug-results
```

## Best Practices

1. **Regular Execution**: Run the pipeline on every commit/PR
2. **Configuration Management**: Store configurations in version control
3. **Result Archival**: Save reports for trend analysis
4. **Threshold Tuning**: Adjust thresholds based on project maturity
5. **Cache Cleanup**: Periodically clear cache for fresh results

## API Usage

For programmatic usage:

```python
from src.pipeline import Pipeline, SecurityStage, QualityStage
from src.pipeline.config import PipelineConfig

# Create configuration
config = PipelineConfig()

# Create pipeline
pipeline = Pipeline(name="custom-pipeline")

# Add stages
pipeline.add_stage(SecurityStage(output_dir=config.output_dir / "security"))
pipeline.add_stage(QualityStage(output_dir=config.output_dir / "quality"))

# Run pipeline
results = pipeline.run()

# Process results
for result in results:
    print(f"Stage: {result.stage_name}, Success: {result.success}")
```