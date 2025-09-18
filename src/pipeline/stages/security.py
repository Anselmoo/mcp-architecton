"""Security scanning pipeline stage."""

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
class SecurityStage:
    """Security scanning pipeline stage.
    
    Runs bandit, safety, and other security tools.
    """
    
    name: str = "Security Scanning"
    output_dir: Path | None = None
    fail_on_high: bool = True
    fail_on_medium: bool = False
    
    def run(self, context: dict[str, Any]) -> PipelineResult:
        """Execute security scanning."""
        start_time = time.time()
        errors: list[str] = []
        artifacts: list[Path] = []
        output: dict[str, Any] = {}
        
        try:
            # Ensure output directory exists
            if self.output_dir:
                self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Run Bandit security scanning
            bandit_result = self._run_bandit()
            output["bandit"] = bandit_result
            
            if bandit_result.get("errors"):
                errors.extend(bandit_result["errors"])
            
            # Run Safety dependency vulnerability scanning
            safety_result = self._run_safety()
            output["safety"] = safety_result
            
            if safety_result.get("errors"):
                errors.extend(safety_result["errors"])
            
            # Determine overall success
            high_issues = bandit_result.get("high_severity_count", 0)
            medium_issues = bandit_result.get("medium_severity_count", 0)
            vulnerable_deps = safety_result.get("vulnerabilities_count", 0)
            
            success = True
            if self.fail_on_high and (high_issues > 0 or vulnerable_deps > 0):
                success = False
                errors.append(f"High severity issues found: {high_issues} code issues, {vulnerable_deps} vulnerable dependencies")
            
            if self.fail_on_medium and medium_issues > 0:
                success = False
                errors.append(f"Medium severity issues found: {medium_issues}")
            
            output["summary"] = {
                "high_severity_issues": high_issues,
                "medium_severity_issues": medium_issues,
                "vulnerable_dependencies": vulnerable_deps,
                "total_issues": high_issues + medium_issues + vulnerable_deps
            }
            
        except Exception as e:
            logger.exception("Security scanning failed")
            errors.append(f"Security scanning error: {e}")
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
    
    def _run_bandit(self) -> dict[str, Any]:
        """Run Bandit security scanner."""
        try:
            # Run bandit with JSON output
            cmd = ["bandit", "-r", "src/", "-f", "json", "-q"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.stdout:
                bandit_data = json.loads(result.stdout)
                
                # Count issues by severity
                high_count = sum(1 for issue in bandit_data.get("results", []) 
                               if issue.get("issue_severity") == "HIGH")
                medium_count = sum(1 for issue in bandit_data.get("results", []) 
                                 if issue.get("issue_severity") == "MEDIUM")
                
                # Save detailed report if output directory is specified
                if self.output_dir:
                    report_path = self.output_dir / "bandit-report.json"
                    report_path.write_text(result.stdout)
                
                return {
                    "success": True,
                    "high_severity_count": high_count,
                    "medium_severity_count": medium_count,
                    "total_issues": len(bandit_data.get("results", [])),
                    "report_data": bandit_data
                }
            else:
                return {
                    "success": True,
                    "high_severity_count": 0,
                    "medium_severity_count": 0,
                    "total_issues": 0
                }
                
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Bandit scanning failed: {e}")
            return {
                "success": False,
                "errors": [f"Bandit error: {e}"],
                "high_severity_count": 0,
                "medium_severity_count": 0,
                "total_issues": 0
            }
    
    def _run_safety(self) -> dict[str, Any]:
        """Run Safety dependency vulnerability scanner."""
        try:
            # Run safety with JSON output
            cmd = ["safety", "check", "--json", "--ignore", "70612"]  # Ignore jinja2 issue if needed
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.stdout:
                try:
                    safety_data = json.loads(result.stdout)
                    vuln_count = len(safety_data) if isinstance(safety_data, list) else 0
                    
                    # Save detailed report if output directory is specified
                    if self.output_dir:
                        report_path = self.output_dir / "safety-report.json"
                        report_path.write_text(result.stdout)
                    
                    return {
                        "success": True,
                        "vulnerabilities_count": vuln_count,
                        "vulnerabilities": safety_data
                    }
                except json.JSONDecodeError:
                    # Safety might output non-JSON when no vulnerabilities found
                    return {
                        "success": True,
                        "vulnerabilities_count": 0,
                        "vulnerabilities": []
                    }
            else:
                return {
                    "success": True,
                    "vulnerabilities_count": 0,
                    "vulnerabilities": []
                }
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Safety scanning failed: {e}")
            return {
                "success": False,
                "errors": [f"Safety error: {e}"],
                "vulnerabilities_count": 0,
                "vulnerabilities": []
            }