"""Content-addressable cache management for generated scripts."""

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Manages content-addressable caching of generated scripts."""
    
    def __init__(self, cache_dir: str = "~/.capibara/cache"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache metadata
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_size_bytes": 0,
        }
    
    async def get_script(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """Retrieve a script from cache by fingerprint."""
        script_file = self.cache_dir / f"{fingerprint}.json"
        
        if not script_file.exists():
            self.stats["misses"] += 1
            logger.debug("Cache miss", fingerprint=fingerprint)
            return None
        
        try:
            with open(script_file, 'r') as f:
                script_data = json.load(f)
            
            # Check if script is expired
            if self._is_expired(script_data):
                await self._evict_script(fingerprint)
                self.stats["misses"] += 1
                return None
            
            # Update access time
            script_data["last_accessed_at"] = datetime.utcnow().isoformat()
            await self._update_script_metadata(fingerprint, script_data)
            
            self.stats["hits"] += 1
            logger.debug("Cache hit", fingerprint=fingerprint)
            return script_data
            
        except Exception as e:
            logger.error("Error reading cached script", fingerprint=fingerprint, error=str(e))
            self.stats["misses"] += 1
            return None
    
    async def store_script(self, script_data: Dict[str, Any]) -> None:
        """Store a script in cache."""
        fingerprint = script_data["fingerprint"]
        script_file = self.cache_dir / f"{fingerprint}.json"
        
        try:
            # Add cache metadata
            script_data["cached_at"] = datetime.utcnow().isoformat()
            script_data["last_accessed_at"] = datetime.utcnow().isoformat()
            script_data["access_count"] = 0
            script_data["cache_hit_count"] = 0
            
            # Write script to file
            with open(script_file, 'w') as f:
                json.dump(script_data, f, indent=2, default=str)
            
            # Update metadata
            self.metadata[fingerprint] = {
                "size_bytes": len(json.dumps(script_data)),
                "cached_at": script_data["cached_at"],
                "last_accessed_at": script_data["last_accessed_at"],
                "access_count": 0,
                "language": script_data["language"],
                "prompt_length": len(script_data["prompt"]),
            }
            
            self._save_metadata()
            self.stats["total_size_bytes"] += self.metadata[fingerprint]["size_bytes"]
            
            logger.debug("Script cached", fingerprint=fingerprint)
            
        except Exception as e:
            logger.error("Error caching script", fingerprint=fingerprint, error=str(e))
            raise CacheError(f"Failed to cache script: {str(e)}") from e
    
    async def increment_cache_hit(self, script_id: str) -> None:
        """Increment cache hit count for a script."""
        # Find script by ID in metadata
        fingerprint = None
        for fp, meta in self.metadata.items():
            if meta.get("script_id") == script_id:
                fingerprint = fp
                break
        
        if fingerprint:
            self.metadata[fingerprint]["access_count"] += 1
            self.metadata[fingerprint]["last_accessed_at"] = datetime.utcnow().isoformat()
            self._save_metadata()
    
    async def list_scripts(
        self,
        limit: int = 50,
        offset: int = 0,
        language: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "cached_at",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """List cached scripts with filtering and sorting."""
        scripts = []
        
        for fingerprint, meta in self.metadata.items():
            script_file = self.cache_dir / f"{fingerprint}.json"
            if not script_file.exists():
                continue
            
            try:
                with open(script_file, 'r') as f:
                    script_data = json.load(f)
                
                # Apply filters
                if language and script_data.get("language") != language:
                    continue
                
                if search and search.lower() not in script_data.get("prompt", "").lower():
                    continue
                
                scripts.append(script_data)
                
            except Exception as e:
                logger.warning("Error reading script for listing", fingerprint=fingerprint, error=str(e))
                continue
        
        # Sort scripts
        reverse = sort_order.lower() == "desc"
        if sort_by == "cached_at":
            scripts.sort(key=lambda x: x.get("cached_at", ""), reverse=reverse)
        elif sort_by == "last_accessed_at":
            scripts.sort(key=lambda x: x.get("last_accessed_at", ""), reverse=reverse)
        elif sort_by == "access_count":
            scripts.sort(key=lambda x: x.get("access_count", 0), reverse=reverse)
        
        # Apply pagination
        return scripts[offset:offset + limit]
    
    async def clear_scripts(
        self,
        script_ids: Optional[List[str]] = None,
        language: Optional[str] = None,
        older_than: Optional[int] = None,
        all_scripts: bool = False
    ) -> int:
        """Clear scripts from cache based on criteria."""
        cleared_count = 0
        fingerprints_to_remove = []
        
        if all_scripts:
            fingerprints_to_remove = list(self.metadata.keys())
        else:
            for fingerprint, meta in self.metadata.items():
                script_file = self.cache_dir / f"{fingerprint}.json"
                if not script_file.exists():
                    continue
                
                try:
                    with open(script_file, 'r') as f:
                        script_data = json.load(f)
                    
                    # Check criteria
                    should_remove = False
                    
                    if script_ids and script_data.get("script_id") in script_ids:
                        should_remove = True
                    elif language and script_data.get("language") == language:
                        should_remove = True
                    elif older_than:
                        cached_at = datetime.fromisoformat(script_data.get("cached_at", ""))
                        if datetime.utcnow() - cached_at > timedelta(seconds=older_than):
                            should_remove = True
                    
                    if should_remove:
                        fingerprints_to_remove.append(fingerprint)
                
                except Exception as e:
                    logger.warning("Error reading script for clearing", fingerprint=fingerprint, error=str(e))
                    continue
        
        # Remove scripts
        for fingerprint in fingerprints_to_remove:
            try:
                script_file = self.cache_dir / f"{fingerprint}.json"
                if script_file.exists():
                    script_file.unlink()
                
                if fingerprint in self.metadata:
                    self.stats["total_size_bytes"] -= self.metadata[fingerprint]["size_bytes"]
                    del self.metadata[fingerprint]
                
                cleared_count += 1
                self.stats["evictions"] += 1
                
            except Exception as e:
                logger.error("Error removing script", fingerprint=fingerprint, error=str(e))
        
        self._save_metadata()
        logger.info("Scripts cleared from cache", count=cleared_count)
        return cleared_count
    
    async def _evict_script(self, fingerprint: str) -> None:
        """Evict a script from cache."""
        try:
            script_file = self.cache_dir / f"{fingerprint}.json"
            if script_file.exists():
                script_file.unlink()
            
            if fingerprint in self.metadata:
                self.stats["total_size_bytes"] -= self.metadata[fingerprint]["size_bytes"]
                del self.metadata[fingerprint]
            
            self.stats["evictions"] += 1
            logger.debug("Script evicted", fingerprint=fingerprint)
            
        except Exception as e:
            logger.error("Error evicting script", fingerprint=fingerprint, error=str(e))
    
    async def _update_script_metadata(self, fingerprint: str, script_data: Dict[str, Any]) -> None:
        """Update script metadata."""
        if fingerprint in self.metadata:
            self.metadata[fingerprint]["last_accessed_at"] = script_data["last_accessed_at"]
            self.metadata[fingerprint]["access_count"] = script_data.get("access_count", 0)
            self._save_metadata()
    
    def _is_expired(self, script_data: Dict[str, Any]) -> bool:
        """Check if a script has expired."""
        cached_at = datetime.fromisoformat(script_data.get("cached_at", ""))
        ttl_seconds = script_data.get("cache_ttl", 3600)  # Default 1 hour
        
        return datetime.utcnow() - cached_at > timedelta(seconds=ttl_seconds)
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Error loading cache metadata", error=str(e))
        
        return {}
    
    def _save_metadata(self) -> None:
        """Save cache metadata to file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error("Error saving cache metadata", error=str(e))
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate_percent": round(hit_rate, 2),
            "total_scripts": len(self.metadata),
            "cache_dir": str(self.cache_dir),
        }


class CacheError(Exception):
    """Raised when cache operations fail."""
    pass
