"""Core pipeline orchestration module.

Provides the main Pipeline class for running modular, reproducible stages.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of a pipeline stage execution."""
    
    stage_name: str
    success: bool
    duration: float
    output: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    artifacts: list[Path] = field(default_factory=list)


class PipelineStage(Protocol):
    """Protocol for pipeline stages."""
    
    def run(self, context: dict[str, Any]) -> PipelineResult:
        """Execute the pipeline stage."""
        ...


@dataclass
class Pipeline:
    """Main pipeline orchestrator.
    
    Executes stages in sequence, collecting results and maintaining context.
    """
    
    name: str
    stages: list[PipelineStage] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    fail_fast: bool = True
    
    def add_stage(self, stage: PipelineStage) -> None:
        """Add a stage to the pipeline."""
        self.stages.append(stage)
    
    def run(self) -> list[PipelineResult]:
        """Execute all pipeline stages."""
        results: list[PipelineResult] = []
        
        logger.info(f"Starting pipeline: {self.name}")
        pipeline_start = time.time()
        
        for i, stage in enumerate(self.stages, 1):
            stage_name = getattr(stage, 'name', f'Stage {i}')
            logger.info(f"Executing stage {i}/{len(self.stages)}: {stage_name}")
            
            try:
                result = stage.run(self.context.copy())
                results.append(result)
                
                # Update context with stage outputs
                if result.success and result.output:
                    self.context.update(result.output)
                
                # Handle failures
                if not result.success:
                    logger.error(f"Stage {stage_name} failed: {result.errors}")
                    if self.fail_fast:
                        logger.error("Stopping pipeline due to failure (fail_fast=True)")
                        break
                else:
                    logger.info(f"Stage {stage_name} completed successfully in {result.duration:.2f}s")
                    
            except Exception as e:
                error_result = PipelineResult(
                    stage_name=stage_name,
                    success=False,
                    duration=0.0,
                    errors=[str(e)]
                )
                results.append(error_result)
                logger.exception(f"Unexpected error in stage {stage_name}")
                
                if self.fail_fast:
                    break
        
        pipeline_duration = time.time() - pipeline_start
        successful_stages = sum(1 for r in results if r.success)
        
        logger.info(
            f"Pipeline {self.name} completed: {successful_stages}/{len(results)} stages successful "
            f"in {pipeline_duration:.2f}s"
        )
        
        return results
    
    def get_artifacts(self, results: list[PipelineResult]) -> list[Path]:
        """Collect all artifacts from pipeline results."""
        artifacts: list[Path] = []
        for result in results:
            artifacts.extend(result.artifacts)
        return artifacts