"""Analysis pipeline stage."""

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
class AnalysisStage:
    """Code analysis pipeline stage.
    
    Runs specialized analysis tools for architecture and patterns.
    """
    
    name: str = "Code Analysis"
    output_dir: Path | None = None
    run_architecture_analysis: bool = True
    run_pattern_analysis: bool = True
    
    def run(self, context: dict[str, Any]) -> PipelineResult:
        """Execute code analysis."""
        start_time = time.time()
        errors: list[str] = []
        artifacts: list[Path] = []
        output: dict[str, Any] = {}
        
        try:
            # Ensure output directory exists
            if self.output_dir:
                self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Run mcp-architecton analysis if available
            if self.run_architecture_analysis:
                arch_result = self._run_architecture_analysis()
                output["architecture"] = arch_result
                
                if not arch_result.get("success", True):
                    errors.extend(arch_result.get("errors", []))
            
            # Run pattern analysis
            if self.run_pattern_analysis:
                pattern_result = self._run_pattern_analysis()
                output["patterns"] = pattern_result
                
                if not pattern_result.get("success", True):
                    errors.extend(pattern_result.get("errors", []))
            
            # Run additional static analysis
            maintenance_result = self._run_maintenance_analysis()
            output["maintenance"] = maintenance_result
            
            success = len(errors) == 0
            
            output["summary"] = {
                "architecture_patterns_detected": len(arch_result.get("patterns", [])) if self.run_architecture_analysis else 0,
                "design_patterns_detected": len(pattern_result.get("patterns", [])) if self.run_pattern_analysis else 0,
                "maintainability_index": maintenance_result.get("maintainability_index", 0)
            }
            
        except Exception as e:
            logger.exception("Code analysis failed")
            errors.append(f"Analysis error: {e}")
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
    
    def _run_architecture_analysis(self) -> dict[str, Any]:
        """Run architecture pattern analysis."""
        try:
            # This would use the mcp-architecton tools directly
            # For now, simulate with a basic file structure analysis
            
            src_path = Path("src/mcp_architecton")
            if not src_path.exists():
                return {
                    "success": False,
                    "errors": ["Source directory not found"],
                    "patterns": []
                }
            
            # Simple analysis of directory structure for architectural patterns
            patterns = []
            
            # Check for layered architecture
            if (src_path / "services").exists():
                patterns.append({
                    "name": "Service Layer",
                    "confidence": 0.8,
                    "location": "src/mcp_architecton/services"
                })
            
            # Check for domain-driven design patterns
            if (src_path / "detectors").exists():
                patterns.append({
                    "name": "Domain Model",
                    "confidence": 0.7,
                    "location": "src/mcp_architecton/detectors"
                })
            
            # Check for generator patterns
            if (src_path / "generators").exists():
                patterns.append({
                    "name": "Factory Pattern",
                    "confidence": 0.6,
                    "location": "src/mcp_architecton/generators"
                })
            
            # Save analysis results
            if self.output_dir:
                import json
                report_path = self.output_dir / "architecture-analysis.json"
                report_path.write_text(json.dumps({"patterns": patterns}, indent=2))
            
            return {
                "success": True,
                "patterns": patterns,
                "total_patterns": len(patterns)
            }
                
        except Exception as e:
            logger.error(f"Architecture analysis failed: {e}")
            return {
                "success": False,
                "errors": [f"Architecture analysis error: {e}"],
                "patterns": []
            }
    
    def _run_pattern_analysis(self) -> dict[str, Any]:
        """Run design pattern analysis."""
        try:
            # Analyze Python files for common design patterns
            patterns = []
            
            # Look for common pattern indicators
            src_files = list(Path("src").rglob("*.py"))
            
            for file_path in src_files:
                content = file_path.read_text()
                
                # Check for Singleton pattern
                if "class " in content and "__new__" in content:
                    patterns.append({
                        "name": "Singleton",
                        "confidence": 0.6,
                        "location": str(file_path)
                    })
                
                # Check for Factory patterns
                if "create" in content.lower() and "class" in content:
                    patterns.append({
                        "name": "Factory",
                        "confidence": 0.5,
                        "location": str(file_path)
                    })
                
                # Check for Observer pattern
                if "notify" in content.lower() and "observer" in content.lower():
                    patterns.append({
                        "name": "Observer",
                        "confidence": 0.7,
                        "location": str(file_path)
                    })
            
            # Save analysis results
            if self.output_dir:
                import json
                report_path = self.output_dir / "pattern-analysis.json"
                report_path.write_text(json.dumps({"patterns": patterns}, indent=2))
            
            return {
                "success": True,
                "patterns": patterns,
                "total_patterns": len(patterns)
            }
                
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return {
                "success": False,
                "errors": [f"Pattern analysis error: {e}"],
                "patterns": []
            }
    
    def _run_maintenance_analysis(self) -> dict[str, Any]:
        """Run maintainability analysis using radon."""
        try:
            # Run radon maintainability index
            cmd = ["radon", "mi", "src/", "--json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.stdout:
                try:
                    import json
                    mi_data = json.loads(result.stdout)
                    
                    # Calculate average maintainability index
                    total_mi = 0
                    file_count = 0
                    
                    for file_data in mi_data.values():
                        if isinstance(file_data, (int, float)):
                            total_mi += file_data
                            file_count += 1
                    
                    avg_mi = total_mi / file_count if file_count > 0 else 0
                    
                    # Save detailed report if output directory is specified
                    if self.output_dir:
                        report_path = self.output_dir / "maintainability-report.json"
                        report_path.write_text(result.stdout)
                    
                    return {
                        "success": True,
                        "maintainability_index": avg_mi,
                        "file_count": file_count,
                        "data": mi_data
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "maintainability_index": 0,
                        "file_count": 0,
                        "data": {}
                    }
            else:
                return {
                    "success": True,
                    "maintainability_index": 0,
                    "file_count": 0,
                    "data": {}
                }
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Maintainability analysis failed: {e}")
            return {
                "success": False,
                "errors": [f"Radon MI error: {e}"],
                "maintainability_index": 0,
                "file_count": 0,
                "data": {}
            }