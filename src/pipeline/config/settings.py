"""Pipeline configuration management."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution."""
    
    # General settings
    name: str = "mcp-architecton-pipeline"
    fail_fast: bool = True
    output_dir: Path = field(default_factory=lambda: Path("pipeline-output"))
    
    # Stage configurations
    security: dict[str, Any] = field(default_factory=dict)
    quality: dict[str, Any] = field(default_factory=dict)
    testing: dict[str, Any] = field(default_factory=dict)
    analysis: dict[str, Any] = field(default_factory=dict)
    
    # Environment settings
    python_version: str = "3.10"
    use_cache: bool = True
    cache_dir: Path = field(default_factory=lambda: Path(".pipeline-cache"))
    
    @classmethod
    def from_file(cls, config_path: Path) -> PipelineConfig:
        """Load configuration from JSON file."""
        if not config_path.exists():
            return cls()
        
        try:
            with config_path.open() as f:
                data = json.load(f)
            
            # Convert path strings to Path objects
            if "output_dir" in data:
                data["output_dir"] = Path(data["output_dir"])
            if "cache_dir" in data:
                data["cache_dir"] = Path(data["cache_dir"])
            
            return cls(**data)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid configuration file: {e}") from e
    
    def to_file(self, config_path: Path) -> None:
        """Save configuration to JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and handle Path objects
        data = {
            "name": self.name,
            "fail_fast": self.fail_fast,
            "output_dir": str(self.output_dir),
            "security": self.security,
            "quality": self.quality,
            "testing": self.testing,
            "analysis": self.analysis,
            "python_version": self.python_version,
            "use_cache": self.use_cache,
            "cache_dir": str(self.cache_dir)
        }
        
        with config_path.open("w") as f:
            json.dump(data, f, indent=2)
    
    def get_default_config() -> dict[str, Any]:
        """Get default pipeline configuration."""
        return {
            "name": "mcp-architecton-pipeline",
            "fail_fast": True,
            "output_dir": "pipeline-output",
            "security": {
                "fail_on_high": True,
                "fail_on_medium": False
            },
            "quality": {
                "fix_issues": False,
                "fail_on_errors": True
            },
            "testing": {
                "coverage_threshold": 35.0,
                "run_benchmarks": False,
                "parallel": True
            },
            "analysis": {
                "run_architecture_analysis": True,
                "run_pattern_analysis": True
            },
            "python_version": "3.10",
            "use_cache": True,
            "cache_dir": ".pipeline-cache"
        }