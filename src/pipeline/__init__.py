"""Pipeline package for mcp-architecton.

This package provides a modular, reproducible pipeline framework for code quality,
security, and analysis workflows.
"""

__version__ = "0.1.0"

from .pipeline import Pipeline, PipelineResult
from .stages import SecurityStage, QualityStage, TestStage, AnalysisStage

__all__ = ["Pipeline", "PipelineResult", "SecurityStage", "QualityStage", "TestStage", "AnalysisStage"]