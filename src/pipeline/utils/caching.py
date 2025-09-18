"""Caching utilities for pipeline optimization."""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any


class CacheManager:
    """Manages caching for pipeline stages to improve performance."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_key(self, stage_name: str, inputs: dict[str, Any]) -> str:
        """Generate a cache key for stage inputs."""
        # Create a deterministic hash of the inputs
        input_str = json.dumps(inputs, sort_keys=True, default=str)
        hash_obj = hashlib.md5(input_str.encode())
        return f"{stage_name}_{hash_obj.hexdigest()}"
    
    def get(self, cache_key: str) -> Any | None:
        """Retrieve cached result."""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if not cache_file.exists():
            return None
        
        try:
            with cache_file.open("rb") as f:
                return pickle.load(f)
        except (pickle.PickleError, EOFError):
            # Remove corrupted cache file
            cache_file.unlink(missing_ok=True)
            return None
    
    def set(self, cache_key: str, result: Any) -> None:
        """Store result in cache."""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            with cache_file.open("wb") as f:
                pickle.dump(result, f)
        except pickle.PickleError:
            # If we can't pickle it, just skip caching
            pass
    
    def clear(self) -> None:
        """Clear all cached results."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
    
    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "cache_dir": str(self.cache_dir),
            "cached_items": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024)
        }