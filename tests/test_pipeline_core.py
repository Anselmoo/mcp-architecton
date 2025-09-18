"""Tests for pipeline core functionality."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from src.pipeline.pipeline import Pipeline, PipelineResult


@dataclass
class MockStage:
    """Mock pipeline stage for testing."""
    
    name: str = "MockStage"
    should_succeed: bool = True
    duration: float = 0.1
    output: dict[str, Any] | None = None
    
    def run(self, context: dict[str, Any]) -> PipelineResult:
        """Mock stage execution."""
        time.sleep(self.duration)
        
        if self.output is None:
            output = {"mock_result": True}
        else:
            output = self.output
        
        return PipelineResult(
            stage_name=self.name,
            success=self.should_succeed,
            duration=self.duration,
            output=output,
            errors=[] if self.should_succeed else ["Mock error"],
            artifacts=[]
        )


def test_pipeline_creation():
    """Test basic pipeline creation."""
    pipeline = Pipeline(name="test-pipeline")
    
    assert pipeline.name == "test-pipeline"
    assert len(pipeline.stages) == 0
    assert pipeline.fail_fast is True
    assert isinstance(pipeline.context, dict)


def test_pipeline_add_stage():
    """Test adding stages to pipeline."""
    pipeline = Pipeline(name="test-pipeline")
    stage = MockStage(name="test-stage")
    
    pipeline.add_stage(stage)
    
    assert len(pipeline.stages) == 1
    assert pipeline.stages[0] == stage


def test_pipeline_successful_execution():
    """Test successful pipeline execution."""
    pipeline = Pipeline(name="test-pipeline")
    
    stage1 = MockStage(name="stage1", should_succeed=True, duration=0.01)
    stage2 = MockStage(name="stage2", should_succeed=True, duration=0.01)
    
    pipeline.add_stage(stage1)
    pipeline.add_stage(stage2)
    
    results = pipeline.run()
    
    assert len(results) == 2
    assert all(r.success for r in results)
    assert results[0].stage_name == "stage1"
    assert results[1].stage_name == "stage2"


def test_pipeline_failed_execution_with_fail_fast():
    """Test pipeline execution with failure and fail_fast=True."""
    pipeline = Pipeline(name="test-pipeline", fail_fast=True)
    
    stage1 = MockStage(name="stage1", should_succeed=True)
    stage2 = MockStage(name="stage2", should_succeed=False)  # This will fail
    stage3 = MockStage(name="stage3", should_succeed=True)   # Should not run
    
    pipeline.add_stage(stage1)
    pipeline.add_stage(stage2)
    pipeline.add_stage(stage3)
    
    results = pipeline.run()
    
    assert len(results) == 2  # Only first two stages should run
    assert results[0].success is True
    assert results[1].success is False
    assert results[1].errors == ["Mock error"]


def test_pipeline_failed_execution_without_fail_fast():
    """Test pipeline execution with failure and fail_fast=False."""
    pipeline = Pipeline(name="test-pipeline", fail_fast=False)
    
    stage1 = MockStage(name="stage1", should_succeed=True)
    stage2 = MockStage(name="stage2", should_succeed=False)  # This will fail
    stage3 = MockStage(name="stage3", should_succeed=True)   # Should still run
    
    pipeline.add_stage(stage1)
    pipeline.add_stage(stage2)
    pipeline.add_stage(stage3)
    
    results = pipeline.run()
    
    assert len(results) == 3  # All stages should run
    assert results[0].success is True
    assert results[1].success is False
    assert results[2].success is True


def test_pipeline_context_propagation():
    """Test that context is propagated between stages."""
    pipeline = Pipeline(name="test-pipeline")
    
    # Stage 1 outputs data
    stage1 = MockStage(
        name="stage1", 
        should_succeed=True, 
        output={"shared_data": "test_value"}
    )
    
    # Stage 2 should receive the context (though mock doesn't use it)
    stage2 = MockStage(name="stage2", should_succeed=True)
    
    pipeline.add_stage(stage1)
    pipeline.add_stage(stage2)
    
    results = pipeline.run()
    
    assert len(results) == 2
    assert all(r.success for r in results)
    
    # Check that context was updated
    assert "shared_data" in pipeline.context
    assert pipeline.context["shared_data"] == "test_value"


def test_pipeline_get_artifacts():
    """Test artifact collection from pipeline results."""
    pipeline = Pipeline(name="test-pipeline")
    
    # Create mock artifacts
    artifact1 = Path("/tmp/artifact1.txt")
    artifact2 = Path("/tmp/artifact2.json")
    
    # Mock results with artifacts
    results = [
        PipelineResult(
            stage_name="stage1",
            success=True,
            duration=0.1,
            artifacts=[artifact1]
        ),
        PipelineResult(
            stage_name="stage2", 
            success=True,
            duration=0.1,
            artifacts=[artifact2]
        )
    ]
    
    artifacts = pipeline.get_artifacts(results)
    
    assert len(artifacts) == 2
    assert artifact1 in artifacts
    assert artifact2 in artifacts


def test_pipeline_result_creation():
    """Test PipelineResult creation and properties."""
    result = PipelineResult(
        stage_name="test-stage",
        success=True,
        duration=1.5,
        output={"key": "value"},
        errors=["error1", "error2"],
        artifacts=[Path("/tmp/artifact.txt")]
    )
    
    assert result.stage_name == "test-stage"
    assert result.success is True
    assert result.duration == 1.5
    assert result.output == {"key": "value"}
    assert result.errors == ["error1", "error2"]
    assert len(result.artifacts) == 1


def test_pipeline_empty_execution():
    """Test pipeline execution with no stages."""
    pipeline = Pipeline(name="empty-pipeline")
    
    results = pipeline.run()
    
    assert len(results) == 0
    assert isinstance(results, list)


def test_pipeline_stage_exception_handling():
    """Test pipeline handling of stage exceptions."""
    
    @dataclass
    class FailingStage:
        """Stage that raises an exception."""
        
        name: str = "FailingStage"
        
        def run(self, context: dict[str, Any]) -> PipelineResult:
            raise ValueError("Test exception")
    
    pipeline = Pipeline(name="test-pipeline", fail_fast=True)
    pipeline.add_stage(FailingStage())
    
    results = pipeline.run()
    
    assert len(results) == 1
    assert results[0].success is False
    assert "Test exception" in results[0].errors[0]


@pytest.mark.parametrize("fail_fast,expected_stages", [
    (True, 1),   # Should stop after first failure
    (False, 3)   # Should run all stages
])
def test_pipeline_fail_fast_behavior(fail_fast: bool, expected_stages: int):
    """Test pipeline fail_fast behavior with parametrized test."""
    pipeline = Pipeline(name="test-pipeline", fail_fast=fail_fast)
    
    pipeline.add_stage(MockStage(name="stage1", should_succeed=False))  # Fails
    pipeline.add_stage(MockStage(name="stage2", should_succeed=True))
    pipeline.add_stage(MockStage(name="stage3", should_succeed=True))
    
    results = pipeline.run()
    
    assert len(results) == expected_stages