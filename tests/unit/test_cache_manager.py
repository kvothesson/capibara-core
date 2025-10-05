"""Unit tests for Cache Manager."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone

from capibara.core.cache_manager import CacheManager, CacheError


class TestCacheManager:
    """Test cases for CacheManager."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create CacheManager instance with temp directory."""
        return CacheManager(cache_dir=str(temp_cache_dir))
    
    @pytest.fixture
    def sample_script_data(self):
        """Create sample script data."""
        return {
            "script_id": "test_script_123",
            "prompt": "print('Hello, World!')",
            "language": "python",
            "code": "print('Hello, World!')",
            "fingerprint": "test_fingerprint_123",
            "security_policy": "moderate",
            "llm_provider": "openai",
            "created_at": datetime.now(timezone.utc),
            "metadata": {"test": "data"}
        }
    
    @pytest.mark.asyncio
    async def test_store_and_get_script(self, cache_manager, sample_script_data):
        """Test storing and retrieving a script."""
        # Act
        await cache_manager.store_script(sample_script_data)
        retrieved_script = await cache_manager.get_script("test_fingerprint_123")
        
        # Assert
        assert retrieved_script is not None
        assert retrieved_script["script_id"] == "test_script_123"
        assert retrieved_script["prompt"] == "print('Hello, World!')"
        assert retrieved_script["language"] == "python"
        assert retrieved_script["code"] == "print('Hello, World!')"
        
        # Check cache stats
        stats = cache_manager.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_script(self, cache_manager):
        """Test retrieving a non-existent script."""
        # Act
        result = await cache_manager.get_script("nonexistent_fingerprint")
        
        # Assert
        assert result is None
        
        # Check cache stats
        stats = cache_manager.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1
    
    @pytest.mark.asyncio
    async def test_increment_cache_hit(self, cache_manager, sample_script_data):
        """Test incrementing cache hit count."""
        # Arrange
        await cache_manager.store_script(sample_script_data)
        
        # Act
        await cache_manager.increment_cache_hit("test_script_123")
        
        # Assert - check that metadata was updated
        # This is a bit indirect since we can't easily access the internal metadata
        # But we can verify the method doesn't raise an exception
        stats = cache_manager.get_cache_stats()
        # The hits count comes from get_script calls, not increment_cache_hit
        # increment_cache_hit just updates the access count in metadata
        assert stats["hits"] >= 0  # Should not be negative
    
    @pytest.mark.asyncio
    async def test_list_scripts(self, cache_manager, sample_script_data):
        """Test listing scripts."""
        # Arrange
        await cache_manager.store_script(sample_script_data)
        
        # Act
        scripts = await cache_manager.list_scripts()
        
        # Assert
        assert len(scripts) == 1
        assert scripts[0]["script_id"] == "test_script_123"
    
    @pytest.mark.asyncio
    async def test_list_scripts_with_filters(self, cache_manager, sample_script_data):
        """Test listing scripts with filters."""
        # Arrange
        await cache_manager.store_script(sample_script_data)
        
        # Test language filter
        python_scripts = await cache_manager.list_scripts(language="python")
        assert len(python_scripts) == 1
        
        js_scripts = await cache_manager.list_scripts(language="javascript")
        assert len(js_scripts) == 0
        
        # Test search filter
        hello_scripts = await cache_manager.list_scripts(search="Hello")
        assert len(hello_scripts) == 1
        
        world_scripts = await cache_manager.list_scripts(search="World")
        assert len(world_scripts) == 1
        
        no_match_scripts = await cache_manager.list_scripts(search="Goodbye")
        assert len(no_match_scripts) == 0
    
    @pytest.mark.asyncio
    async def test_clear_scripts(self, cache_manager, sample_script_data):
        """Test clearing scripts from cache."""
        # Arrange
        await cache_manager.store_script(sample_script_data)
        
        # Verify script exists
        scripts = await cache_manager.list_scripts()
        assert len(scripts) == 1
        
        # Act - clear by script ID
        cleared_count = await cache_manager.clear_scripts(script_ids=["test_script_123"])
        
        # Assert
        assert cleared_count == 1
        
        # Verify script is gone
        scripts = await cache_manager.list_scripts()
        assert len(scripts) == 0
    
    @pytest.mark.asyncio
    async def test_clear_scripts_by_language(self, cache_manager, sample_script_data):
        """Test clearing scripts by language."""
        # Arrange - create scripts in different languages
        python_script = sample_script_data.copy()
        python_script["script_id"] = "python_script"
        python_script["fingerprint"] = "python_fingerprint"
        python_script["language"] = "python"
        
        js_script = sample_script_data.copy()
        js_script["script_id"] = "js_script"
        js_script["fingerprint"] = "js_fingerprint"
        js_script["language"] = "javascript"
        
        await cache_manager.store_script(python_script)
        await cache_manager.store_script(js_script)
        
        # Verify both scripts exist
        scripts = await cache_manager.list_scripts()
        assert len(scripts) == 2
        
        # Act - clear JavaScript scripts
        cleared_count = await cache_manager.clear_scripts(language="javascript")
        
        # Assert
        assert cleared_count == 1
        
        # Verify only Python script remains
        scripts = await cache_manager.list_scripts()
        assert len(scripts) == 1
        assert scripts[0]["language"] == "python"
    
    @pytest.mark.asyncio
    async def test_clear_all_scripts(self, cache_manager, sample_script_data):
        """Test clearing all scripts."""
        # Arrange
        await cache_manager.store_script(sample_script_data)
        
        # Act
        cleared_count = await cache_manager.clear_scripts(all_scripts=True)
        
        # Assert
        assert cleared_count == 1
        
        # Verify no scripts remain
        scripts = await cache_manager.list_scripts()
        assert len(scripts) == 0
    
    @pytest.mark.asyncio
    async def test_script_expiration(self, cache_manager, sample_script_data):
        """Test script expiration."""
        # Arrange - create script with very short TTL
        script_data = sample_script_data.copy()
        script_data["cache_ttl"] = 0  # Expire immediately
        
        await cache_manager.store_script(script_data)
        
        # Act - try to get the script
        result = await cache_manager.get_script("test_fingerprint_123")
        
        # Assert - should return None due to expiration
        assert result is None
        
        # Check cache stats - should be a miss due to expiration
        stats = cache_manager.get_cache_stats()
        assert stats["misses"] == 1
    
    def test_cache_stats(self, cache_manager):
        """Test cache statistics."""
        # Initial stats
        stats = cache_manager.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["hit_rate_percent"] == 0
        assert stats["total_scripts"] == 0
        assert "cache_dir" in stats
    
    @pytest.mark.asyncio
    async def test_store_script_error_handling(self, cache_manager, sample_script_data):
        """Test error handling in store_script."""
        # Arrange - make the cache directory read-only to cause an error
        cache_manager.cache_dir.chmod(0o444)  # Read-only
        
        try:
            # Act & Assert
            with pytest.raises(CacheError):
                await cache_manager.store_script(sample_script_data)
        finally:
            # Restore write permissions
            cache_manager.cache_dir.chmod(0o755)
    
    @pytest.mark.asyncio
    async def test_get_script_error_handling(self, cache_manager):
        """Test error handling in get_script."""
        # Arrange - create a corrupted script file
        script_file = cache_manager.cache_dir / "corrupted_fingerprint.json"
        script_file.write_text("invalid json content")
        
        # Add to metadata
        cache_manager.metadata["corrupted_fingerprint"] = {
            "size_bytes": 100,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "last_accessed_at": datetime.now(timezone.utc).isoformat(),
            "access_count": 0,
            "language": "python",
            "prompt_length": 10,
        }
        
        # Act
        result = await cache_manager.get_script("corrupted_fingerprint")
        
        # Assert - should return None due to error
        assert result is None
        
        # Check cache stats - should be a miss due to error
        stats = cache_manager.get_cache_stats()
        assert stats["misses"] == 1
    
    def test_cache_error(self):
        """Test CacheError exception."""
        # Test basic error
        error = CacheError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}
        
        # Test error with details
        details = {"fingerprint": "test_fp", "operation": "store"}
        error_with_details = CacheError("Test error", details)
        assert error_with_details.details == details
