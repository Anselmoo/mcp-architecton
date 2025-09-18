#!/usr/bin/env python3
"""Pipeline CLI for mcp-architecton.

Provides a command-line interface for running the comprehensive pipeline.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add the src directory to Python path for imports
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pipeline.config import PipelineConfig
from pipeline.pipeline import Pipeline
from pipeline.stages import AnalysisStage, QualityStage, SecurityStage, TestStage
from pipeline.utils import CacheManager, ReportGenerator


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def create_pipeline(config: PipelineConfig) -> Pipeline:
    """Create a pipeline with configured stages."""
    pipeline = Pipeline(name=config.name, fail_fast=config.fail_fast)
    
    # Security stage
    security_stage = SecurityStage(
        output_dir=config.output_dir / "security",
        **config.security
    )
    pipeline.add_stage(security_stage)
    
    # Quality stage
    quality_stage = QualityStage(
        output_dir=config.output_dir / "quality",
        **config.quality
    )
    pipeline.add_stage(quality_stage)
    
    # Testing stage
    test_stage = TestStage(
        output_dir=config.output_dir / "testing",
        **config.testing
    )
    pipeline.add_stage(test_stage)
    
    # Analysis stage
    analysis_stage = AnalysisStage(
        output_dir=config.output_dir / "analysis",
        **config.analysis
    )
    pipeline.add_stage(analysis_stage)
    
    return pipeline


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run the mcp-architecton comprehensive pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run with default configuration
  %(prog)s --config custom.json      # Run with custom configuration
  %(prog)s --stage security          # Run only security stage
  %(prog)s --no-cache               # Disable caching
  %(prog)s --output-dir results      # Custom output directory
        """.strip()
    )
    
    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Path to pipeline configuration file (JSON)"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        help="Output directory for pipeline results"
    )
    
    parser.add_argument(
        "--stage",
        choices=["security", "quality", "testing", "analysis"],
        help="Run only a specific stage"
    )
    
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching"
    )
    
    parser.add_argument(
        "--no-fail-fast",
        action="store_true",
        help="Continue pipeline even if stages fail"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="Generate a default configuration file and exit"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Generate default config if requested
    if args.generate_config:
        config_path = Path("pipeline-config.json")
        default_config = PipelineConfig()
        default_config.to_file(config_path)
        print(f"Default configuration saved to {config_path}")
        return 0
    
    try:
        # Load configuration
        if args.config and args.config.exists():
            config = PipelineConfig.from_file(args.config)
            logger.info(f"Loaded configuration from {args.config}")
        else:
            config = PipelineConfig()
            logger.info("Using default configuration")
        
        # Override config with CLI arguments
        if args.output_dir:
            config.output_dir = args.output_dir
        
        if args.no_fail_fast:
            config.fail_fast = False
        
        if args.no_cache:
            config.use_cache = False
        
        # Ensure output directory exists
        config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up caching if enabled
        cache_manager = None
        if config.use_cache:
            cache_manager = CacheManager(config.cache_dir)
            logger.info(f"Caching enabled: {config.cache_dir}")
        
        # Create and configure pipeline
        pipeline = create_pipeline(config)
        
        # Filter stages if specific stage requested
        if args.stage:
            stage_map = {
                "security": SecurityStage,
                "quality": QualityStage,
                "testing": TestStage,
                "analysis": AnalysisStage
            }
            
            # Create pipeline with only the requested stage
            pipeline = Pipeline(name=f"{config.name}-{args.stage}", fail_fast=config.fail_fast)
            stage_class = stage_map[args.stage]
            
            if args.stage == "security":
                stage = SecurityStage(output_dir=config.output_dir / "security", **config.security)
            elif args.stage == "quality":
                stage = QualityStage(output_dir=config.output_dir / "quality", **config.quality)
            elif args.stage == "testing":
                stage = TestStage(output_dir=config.output_dir / "testing", **config.testing)
            elif args.stage == "analysis":
                stage = AnalysisStage(output_dir=config.output_dir / "analysis", **config.analysis)
            
            pipeline.add_stage(stage)
            logger.info(f"Running only {args.stage} stage")
        
        # Run pipeline
        logger.info("Starting pipeline execution...")
        results = pipeline.run()
        
        # Generate reports
        reporter = ReportGenerator(config.output_dir)
        
        summary_path = reporter.generate_summary_report(results)
        logger.info(f"Summary report saved to {summary_path}")
        
        html_path = reporter.generate_html_report(results)
        logger.info(f"HTML report saved to {html_path}")
        
        # Print cache statistics if caching was used
        if cache_manager:
            stats = cache_manager.get_cache_stats()
            logger.info(f"Cache: {stats['cached_items']} items, {stats['total_size_mb']:.1f} MB")
        
        # Determine exit code
        failed_stages = [r for r in results if not r.success]
        if failed_stages:
            logger.error(f"Pipeline completed with {len(failed_stages)} failed stages")
            return 1
        else:
            logger.info("Pipeline completed successfully!")
            return 0
            
    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())