"""Code quality pipeline stage."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..pipeline import PipelineResult

logger = logging.getLogger(__name__)


@dataclass
class QualityStage:
    """Code quality pipeline stage.
    
    Runs linting, formatting checks, and code quality metrics.
    """
    
    name: str = "Code Quality"
    output_dir: Path | None = None
    fix_issues: bool = False
    fail_on_errors: bool = True
    
    def run(self, context: dict[str, Any]) -> PipelineResult:
        """Execute code quality checks."""
        start_time = time.time()
        errors: list[str] = []
        artifacts: list[Path] = []
        output: dict[str, Any] = {}
        
        try:
            # Ensure output directory exists
            if self.output_dir:
                self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Run Ruff linting
            ruff_result = self._run_ruff_check()
            output["ruff_lint"] = ruff_result
            
            # Run Ruff formatting check
            format_result = self._run_ruff_format()
            output["ruff_format"] = format_result
            
            # Run MyPy type checking
            mypy_result = self._run_mypy()
            output["mypy"] = mypy_result
            
            # Run code complexity analysis
            complexity_result = self._run_complexity_analysis()
            output["complexity"] = complexity_result
            
            # Determine overall success
            success = True
            total_errors = 0
            
            if not ruff_result.get("success", True):
                success = False
                total_errors += ruff_result.get("error_count", 0)
                errors.extend(ruff_result.get("errors", []))
            
            if not format_result.get("success", True):
                success = False
                errors.extend(format_result.get("errors", []))
            
            if not mypy_result.get("success", True):
                # MyPy errors are often not blocking initially
                if self.fail_on_errors:
                    success = False
                errors.extend(mypy_result.get("errors", []))
            
            output["summary"] = {
                "total_lint_errors": total_errors,
                "format_issues": not format_result.get("success", True),
                "type_errors": mypy_result.get("error_count", 0),
                "complexity_violations": complexity_result.get("violations", 0)
            }
            
        except Exception as e:
            logger.exception("Code quality checking failed")
            errors.append(f"Quality checking error: {e}")
            success = False
        
        duration = time.time() - start_time
        
        return PipelineResult(
            stage_name=self.name,
            success=success,
            duration=duration,
            output=output,
            errors=errors,
            artifacts=artifacts
        )
    
    def _run_ruff_check(self) -> dict[str, Any]:
        """Run Ruff linting."""
        try:
            # Run ruff check with JSON output
            cmd = ["ruff", "check", ".", "--output-format", "json"]
            if self.fix_issues:
                cmd.extend(["--fix", "--unsafe-fixes"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.stdout:
                try:
                    ruff_data = json.loads(result.stdout)
                    error_count = len(ruff_data)
                    
                    # Save detailed report if output directory is specified
                    if self.output_dir:
                        report_path = self.output_dir / "ruff-lint-report.json"
                        report_path.write_text(result.stdout)
                    
                    return {
                        "success": error_count == 0,
                        "error_count": error_count,
                        "issues": ruff_data,
                        "errors": [f"Ruff found {error_count} issues"] if error_count > 0 else []
                    }
                except json.JSONDecodeError:
                    # No JSON output usually means no issues
                    return {
                        "success": True,
                        "error_count": 0,
                        "issues": []
                    }
            else:
                return {
                    "success": True,
                    "error_count": 0,
                    "issues": []
                }
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Ruff linting failed: {e}")
            return {
                "success": False,
                "errors": [f"Ruff error: {e}"],
                "error_count": 0,
                "issues": []
            }
    
    def _run_ruff_format(self) -> dict[str, Any]:
        """Run Ruff formatting check."""
        try:
            # Run ruff format in check mode
            cmd = ["ruff", "format", ".", "--check"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "All files are properly formatted"
                }
            else:
                # Files need formatting
                unformatted_files = result.stdout.strip().split('\n') if result.stdout else []
                return {
                    "success": False,
                    "errors": [f"Files need formatting: {len(unformatted_files)} files"],
                    "unformatted_files": unformatted_files
                }
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Ruff formatting check failed: {e}")
            return {
                "success": False,
                "errors": [f"Ruff format error: {e}"]
            }
    
    def _run_mypy(self) -> dict[str, Any]:
        """Run MyPy type checking."""
        try:
            # Run mypy with error output
            cmd = ["mypy", "src/", "--ignore-missing-imports", "--no-strict-optional"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "error_count": 0,
                    "message": "No type errors found"
                }
            else:
                errors = result.stdout.strip().split('\n') if result.stdout else []
                error_count = len([e for e in errors if e.strip() and not e.startswith('Found')])
                
                # Save detailed report if output directory is specified
                if self.output_dir:
                    report_path = self.output_dir / "mypy-report.txt"
                    report_path.write_text(result.stdout)
                
                return {
                    "success": False,
                    "error_count": error_count,
                    "errors": [f"MyPy found {error_count} type errors"],
                    "details": errors
                }
                
        except subprocess.CalledProcessError as e:
            logger.error(f"MyPy type checking failed: {e}")
            return {
                "success": False,
                "errors": [f"MyPy error: {e}"],
                "error_count": 0
            }
    
    def _run_complexity_analysis(self) -> dict[str, Any]:
        """Run code complexity analysis using radon."""
        try:
            # Run radon cyclomatic complexity
            cmd = ["radon", "cc", "src/", "--json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.stdout:
                try:
                    complexity_data = json.loads(result.stdout)
                    
                    # Count high complexity functions (> 10)
                    violations = 0
                    for file_data in complexity_data.values():
                        for item in file_data:
                            if item.get('complexity', 0) > 10:
                                violations += 1
                    
                    # Save detailed report if output directory is specified
                    if self.output_dir:
                        report_path = self.output_dir / "complexity-report.json"
                        report_path.write_text(result.stdout)
                    
                    return {
                        "success": violations == 0,
                        "violations": violations,
                        "data": complexity_data
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "violations": 0,
                        "data": {}
                    }
            else:
                return {
                    "success": True,
                    "violations": 0,
                    "data": {}
                }
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Complexity analysis failed: {e}")
            return {
                "success": False,
                "errors": [f"Radon error: {e}"],
                "violations": 0,
                "data": {}
            }