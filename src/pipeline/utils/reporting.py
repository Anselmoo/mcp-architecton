"""Report generation utilities for pipeline results."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..pipeline import PipelineResult


class ReportGenerator:
    """Generates comprehensive reports from pipeline results."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_summary_report(self, results: list[PipelineResult]) -> Path:
        """Generate a summary report of all pipeline stages."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "pipeline_summary": {
                "total_stages": len(results),
                "successful_stages": sum(1 for r in results if r.success),
                "failed_stages": sum(1 for r in results if not r.success),
                "total_duration": sum(r.duration for r in results),
                "total_artifacts": sum(len(r.artifacts) for r in results)
            },
            "stage_results": []
        }
        
        for result in results:
            stage_data = {
                "name": result.stage_name,
                "success": result.success,
                "duration": result.duration,
                "error_count": len(result.errors),
                "artifact_count": len(result.artifacts),
                "summary": result.output.get("summary", {})
            }
            
            if result.errors:
                stage_data["errors"] = result.errors[:5]  # Limit to first 5 errors
            
            report["stage_results"].append(stage_data)
        
        report_path = self.output_dir / "pipeline-summary.json"
        with report_path.open("w") as f:
            json.dump(report, f, indent=2)
        
        return report_path
    
    def generate_html_report(self, results: list[PipelineResult]) -> Path:
        """Generate an HTML report for better visualization."""
        html_content = self._create_html_template()
        
        # Create stage sections
        stages_html = ""
        for result in results:
            status_class = "success" if result.success else "failure"
            status_text = "✓ PASSED" if result.success else "✗ FAILED"
            
            stage_html = f"""
            <div class="stage {status_class}">
                <h3>{result.stage_name} <span class="status">{status_text}</span></h3>
                <p><strong>Duration:</strong> {result.duration:.2f}s</p>
                <p><strong>Artifacts:</strong> {len(result.artifacts)}</p>
                
                {self._format_stage_summary(result.output.get('summary', {}))}
                
                {self._format_errors(result.errors) if result.errors else ''}
            </div>
            """
            stages_html += stage_html
        
        # Generate overall statistics
        total_stages = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total_stages - successful
        total_duration = sum(r.duration for r in results)
        
        stats_html = f"""
        <div class="stats">
            <h2>Pipeline Statistics</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <span class="stat-number">{total_stages}</span>
                    <span class="stat-label">Total Stages</span>
                </div>
                <div class="stat-item success">
                    <span class="stat-number">{successful}</span>
                    <span class="stat-label">Successful</span>
                </div>
                <div class="stat-item {'failure' if failed > 0 else ''}">
                    <span class="stat-number">{failed}</span>
                    <span class="stat-label">Failed</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{total_duration:.1f}s</span>
                    <span class="stat-label">Total Duration</span>
                </div>
            </div>
        </div>
        """
        
        # Replace placeholders in template
        html_content = html_content.replace("{{STATS}}", stats_html)
        html_content = html_content.replace("{{STAGES}}", stages_html)
        html_content = html_content.replace("{{TIMESTAMP}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        report_path = self.output_dir / "pipeline-report.html"
        report_path.write_text(html_content)
        
        return report_path
    
    def _format_stage_summary(self, summary: dict[str, Any]) -> str:
        """Format stage summary as HTML."""
        if not summary:
            return ""
        
        html = "<div class='summary'><h4>Summary</h4><ul>"
        for key, value in summary.items():
            formatted_key = key.replace("_", " ").title()
            html += f"<li><strong>{formatted_key}:</strong> {value}</li>"
        html += "</ul></div>"
        
        return html
    
    def _format_errors(self, errors: list[str]) -> str:
        """Format errors as HTML."""
        if not errors:
            return ""
        
        html = "<div class='errors'><h4>Errors</h4><ul>"
        for error in errors[:10]:  # Limit to first 10 errors
            html += f"<li>{error}</li>"
        html += "</ul></div>"
        
        return html
    
    def _create_html_template(self) -> str:
        """Create the HTML template for reports."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>MCP Architecton Pipeline Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        h1, h2, h3 { color: #333; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stats { margin-bottom: 30px; padding: 20px; background: #f8f9fa; border-radius: 6px; }
        .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin-top: 15px; }
        .stat-item { text-align: center; padding: 15px; background: white; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .stat-number { display: block; font-size: 2em; font-weight: bold; color: #333; }
        .stat-label { display: block; font-size: 0.9em; color: #666; margin-top: 5px; }
        .stage { margin: 20px 0; padding: 20px; border-radius: 6px; border-left: 4px solid; }
        .stage.success { background: #f8fff8; border-left-color: #28a745; }
        .stage.failure { background: #fff8f8; border-left-color: #dc3545; }
        .status { float: right; font-weight: bold; }
        .success .status { color: #28a745; }
        .failure .status { color: #dc3545; }
        .success.stat-item { border-left: 3px solid #28a745; }
        .failure.stat-item { border-left: 3px solid #dc3545; }
        .summary, .errors { margin-top: 15px; }
        .summary h4, .errors h4 { margin-bottom: 10px; color: #555; }
        .errors { color: #d63384; }
        ul { margin: 0; padding-left: 20px; }
        .timestamp { text-align: right; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>MCP Architecton Pipeline Report</h1>
        <p class="timestamp">Generated: {{TIMESTAMP}}</p>
        
        {{STATS}}
        
        <h2>Stage Details</h2>
        {{STAGES}}
    </div>
</body>
</html>
        """.strip()