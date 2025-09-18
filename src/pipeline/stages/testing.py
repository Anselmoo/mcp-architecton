"""Testing pipeline stage."""

from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..pipeline import PipelineResult

logger = logging.getLogger(__name__)


@dataclass
class TestStage:
    """Testing pipeline stage.
    
    Runs tests with coverage reporting and performance benchmarks.
    """
    
    name: str = "Testing"
    output_dir: Path | None = None
    coverage_threshold: float = 35.0
    run_benchmarks: bool = False
    parallel: bool = True
    
    def run(self, context: dict[str, Any]) -> PipelineResult:
        """Execute tests."""
        start_time = time.time()
        errors: list[str] = []
        artifacts: list[Path] = []
        output: dict[str, Any] = {}
        
        try:
            # Ensure output directory exists
            if self.output_dir:
                self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Run unit tests with coverage
            test_result = self._run_tests()
            output["tests"] = test_result
            
            if not test_result.get("success", False):
                errors.extend(test_result.get("errors", []))
            
            # Check coverage threshold
            coverage = test_result.get("coverage_percent", 0)
            if coverage < self.coverage_threshold:
                errors.append(f"Coverage {coverage:.1f}% below threshold {self.coverage_threshold}%")
            
            # Run benchmarks if requested
            if self.run_benchmarks:
                benchmark_result = self._run_benchmarks()
                output["benchmarks"] = benchmark_result
                
                if not benchmark_result.get("success", True):
                    errors.extend(benchmark_result.get("errors", []))
            
            # Collect artifacts
            if self.output_dir:
                coverage_xml = self.output_dir / "coverage.xml"
                if coverage_xml.exists():
                    artifacts.append(coverage_xml)
                
                junit_xml = self.output_dir / "junit.xml"
                if junit_xml.exists():
                    artifacts.append(junit_xml)
            
            success = len(errors) == 0
            
            output["summary"] = {
                "tests_passed": test_result.get("passed", 0),
                "tests_failed": test_result.get("failed", 0),
                "coverage_percent": coverage,
                "coverage_meets_threshold": coverage >= self.coverage_threshold
            }
            
        except Exception as e:
            logger.exception("Testing failed")
            errors.append(f"Testing error: {e}")
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
    
    def _run_tests(self) -> dict[str, Any]:
        """Run pytest with coverage."""
        try:
            # Build pytest command
            cmd = ["pytest", "-v", "--cov=src/mcp_architecton", "--cov-report=xml", "--cov-report=term"]
            
            if self.parallel:
                cmd.extend(["-n", "auto"])  # Requires pytest-xdist
            
            if self.output_dir:
                junit_path = self.output_dir / "junit.xml"
                cmd.extend(["--junit-xml", str(junit_path)])
                
                coverage_xml = self.output_dir / "coverage.xml"
                cmd.extend([f"--cov-report=xml:{coverage_xml}"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            # Parse output for test results
            passed = 0
            failed = 0
            coverage_percent = 0.0
            
            for line in result.stdout.split('\n'):
                if 'passed' in line and 'failed' in line:
                    # Extract test counts from summary line
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'passed' in part and i > 0:
                            try:
                                passed = int(parts[i-1])
                            except (ValueError, IndexError):
                                pass
                        elif 'failed' in part and i > 0:
                            try:
                                failed = int(parts[i-1])
                            except (ValueError, IndexError):
                                pass
                elif 'Total coverage:' in line:
                    # Extract coverage percentage
                    try:
                        coverage_part = line.split('Total coverage:')[1].strip()
                        coverage_percent = float(coverage_part.rstrip('%'))
                    except (ValueError, IndexError):
                        pass
            
            # Save detailed output if output directory is specified
            if self.output_dir:
                output_path = self.output_dir / "pytest-output.txt"
                output_path.write_text(result.stdout + "\n" + result.stderr)
            
            success = result.returncode == 0
            errors = []
            if not success:
                errors.append(f"Tests failed with return code {result.returncode}")
            
            return {
                "success": success,
                "passed": passed,
                "failed": failed,
                "coverage_percent": coverage_percent,
                "errors": errors,
                "output": result.stdout
            }
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Test execution failed: {e}")
            return {
                "success": False,
                "errors": [f"Pytest error: {e}"],
                "passed": 0,
                "failed": 0,
                "coverage_percent": 0.0
            }
    
    def _run_benchmarks(self) -> dict[str, Any]:
        """Run performance benchmarks."""
        try:
            # Run pytest with benchmark plugin if available
            cmd = ["pytest", "--benchmark-only", "--benchmark-json=benchmark.json"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            # Check if benchmark.json was created
            benchmark_file = Path("benchmark.json")
            benchmark_data = {}
            
            if benchmark_file.exists():
                import json
                with benchmark_file.open() as f:
                    benchmark_data = json.load(f)
                
                # Move to output directory if specified
                if self.output_dir:
                    target = self.output_dir / "benchmark.json"
                    benchmark_file.rename(target)
            
            return {
                "success": result.returncode == 0,
                "data": benchmark_data,
                "errors": [] if result.returncode == 0 else [f"Benchmark failed: {result.stderr}"]
            }
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Benchmark execution failed: {e}")
            return {
                "success": False,
                "errors": [f"Benchmark error: {e}"],
                "data": {}
            }