"""Integration tests for Capibara Client."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from capibara.sdk.client import CapibaraClient
from capibara.models.requests import RunRequest
from capibara.models.responses import RunResponse


class TestCapibaraClientIntegration:
    """Integration tests for CapibaraClient."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def mock_client_components(self, temp_cache_dir):
        """Create mock client with all components."""
        with patch('capibara.sdk.client.CapibaraClient._initialize_components') as mock_init:
            client = CapibaraClient(
                openai_api_key="test_openai_key",
                groq_api_key="test_groq_key",
                cache_dir=str(temp_cache_dir)
            )
            
            # Mock all components
            client.cache_manager = Mock()
            client.cache_manager.get_script = AsyncMock(return_value=None)
            client.cache_manager.store_script = AsyncMock()
            client.cache_manager.list_scripts = AsyncMock(return_value=[])
            client.cache_manager.clear_scripts = AsyncMock(return_value=0)
            client.cache_manager.get_cache_stats = Mock(return_value={
                "hits": 0, "misses": 0, "evictions": 0, "total_size_bytes": 0,
                "hit_rate_percent": 0, "total_scripts": 0, "cache_dir": str(temp_cache_dir)
            })
            
            client.ast_scanner = Mock()
            client.policy_manager = Mock()
            client.container_runner = Mock()
            client.fallback_manager = Mock()
            client.script_generator = Mock()
            client.engine = Mock()
            
            return client
    
    @pytest.fixture
    def sample_run_response(self):
        """Create sample run response."""
        from datetime import datetime, timezone
        return RunResponse(
            script_id="test_script_123",
            prompt="print('Hello, World!')",
            language="python",
            code="print('Hello, World!')",
            execution_result=None,
            cached=False,
            security_policy="moderate",
            llm_provider="openai",
            fingerprint="test_fingerprint_123",
            created_at=datetime.now(timezone.utc),
            metadata={}
        )
    
    @pytest.mark.asyncio
    async def test_run_script_generation(self, mock_client_components, sample_run_response):
        """Test script generation through client."""
        # Arrange
        mock_client_components.engine.run_script = AsyncMock(return_value=sample_run_response)
        
        # Act
        response = await mock_client_components.run(
            prompt="print('Hello, World!')",
            language="python",
            execute=False
        )
        
        # Assert
        assert isinstance(response, RunResponse)
        assert response.script_id == "test_script_123"
        assert response.prompt == "print('Hello, World!')"
        assert response.language == "python"
        assert response.code == "print('Hello, World!')"
        assert response.cached is False
        assert response.llm_provider == "openai"
        
        # Verify engine was called
        mock_client_components.engine.run_script.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_script_with_execution(self, mock_client_components, sample_run_response):
        """Test script generation with execution."""
        # Arrange
        from capibara.models.responses import ExecutionResult
        execution_result = ExecutionResult(
            success=True,
            exit_code=0,
            stdout="Hello, World!",
            stderr="",
            execution_time_ms=100,
            memory_used_mb=50.0
        )
        sample_run_response.execution_result = execution_result
        mock_client_components.engine.run_script = AsyncMock(return_value=sample_run_response)
        
        # Act
        response = await mock_client_components.run(
            prompt="print('Hello, World!')",
            language="python",
            execute=True
        )
        
        # Assert
        assert response.execution_result is not None
        assert response.execution_result.success is True
        assert response.execution_result.stdout == "Hello, World!"
        assert response.execution_result.exit_code == 0
    
    @pytest.mark.asyncio
    async def test_run_script_with_context(self, mock_client_components, sample_run_response):
        """Test script generation with context."""
        # Arrange
        context = {"inputs": [1, 2, 3], "output_format": "json"}
        mock_client_components.engine.run_script = AsyncMock(return_value=sample_run_response)
        
        # Act
        response = await mock_client_components.run(
            prompt="Process these numbers",
            language="python",
            context=context
        )
        
        # Assert
        assert response.script_id == "test_script_123"
        
        # Verify engine was called with context
        call_args = mock_client_components.engine.run_script.call_args[0][0]
        assert isinstance(call_args, RunRequest)
        assert call_args.context == context
    
    @pytest.mark.asyncio
    async def test_run_script_with_security_policy(self, mock_client_components, sample_run_response):
        """Test script generation with security policy."""
        # Arrange
        mock_client_components.engine.run_script = AsyncMock(return_value=sample_run_response)
        
        # Act
        response = await mock_client_components.run(
            prompt="print('Hello, World!')",
            language="python",
            security_policy="strict"
        )
        
        # Assert
        assert response.security_policy == "moderate"  # From sample response
        
        # Verify engine was called with security policy
        call_args = mock_client_components.engine.run_script.call_args[0][0]
        assert call_args.security_policy == "strict"
    
    @pytest.mark.asyncio
    async def test_run_script_with_provider_preference(self, mock_client_components, sample_run_response):
        """Test script generation with provider preference."""
        # Arrange
        mock_client_components.engine.run_script = AsyncMock(return_value=sample_run_response)
        
        # Act
        response = await mock_client_components.run(
            prompt="print('Hello, World!')",
            language="python",
            llm_provider="groq"
        )
        
        # Assert
        assert response.llm_provider == "openai"  # From sample response
        
        # Verify engine was called with provider preference
        call_args = mock_client_components.engine.run_script.call_args[0][0]
        assert call_args.llm_provider == "groq"
    
    @pytest.mark.asyncio
    async def test_list_scripts(self, mock_client_components):
        """Test listing scripts through client."""
        # Arrange
        from datetime import datetime, timezone
        mock_scripts = [
            {
                "script_id": "script_1",
                "language": "python",
                "prompt": "Hello world",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "execution_count": 1,
                "cache_hit_count": 5,
                "llm_provider": "openai",
                "fingerprint": "fp1",
                "size_bytes": 100
            },
            {
                "script_id": "script_2",
                "language": "javascript",
                "prompt": "Console log",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "execution_count": 2,
                "cache_hit_count": 3,
                "llm_provider": "groq",
                "fingerprint": "fp2",
                "size_bytes": 150
            }
        ]
        mock_client_components.cache_manager.list_scripts = AsyncMock(return_value=mock_scripts)
        
        # Act
        response = await mock_client_components.list_scripts(
            limit=10,
            offset=0,
            language="python"
        )
        
        # Assert
        assert len(response.scripts) == 2
        assert response.scripts[0].script_id == "script_1"
        assert response.scripts[1].script_id == "script_2"
        assert response.total_count == 2
        assert response.limit == 10
        assert response.offset == 0
        
        # Verify cache manager was called
        mock_client_components.cache_manager.list_scripts.assert_called_once_with(
            limit=10,
            offset=0,
            language="python",
            search=None,
            sort_by="created_at",
            sort_order="desc"
        )
    
    @pytest.mark.asyncio
    async def test_show_script(self, mock_client_components):
        """Test showing script details through client."""
        # Arrange
        from datetime import datetime, timezone
        mock_script = {
            "script_id": "script_123",
            "language": "python",
            "prompt": "Hello world",
            "code": "print('Hello, World!')",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "execution_count": 1,
            "cache_hit_count": 5,
            "llm_provider": "openai",
            "fingerprint": "fp123",
            "size_bytes": 200
        }
        mock_client_components.cache_manager.get_script = AsyncMock(return_value=mock_script)
        
        # Act
        response = await mock_client_components.show_script(
            script_id="script_123",
            include_code=True
        )
        
        # Assert
        assert response.script.script_id == "script_123"
        assert response.code == "print('Hello, World!')"
        assert response.execution_logs is None
        
        # Verify cache manager was called
        mock_client_components.cache_manager.get_script.assert_called_once_with("script_123")
    
    @pytest.mark.asyncio
    async def test_show_script_not_found(self, mock_client_components):
        """Test showing non-existent script."""
        # Arrange
        mock_client_components.cache_manager.get_script = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await mock_client_components.show_script("nonexistent_script")
        
        assert "Script not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, mock_client_components):
        """Test clearing cache through client."""
        # Arrange
        mock_client_components.cache_manager.clear_scripts = AsyncMock(return_value=3)
        
        # Act
        response = await mock_client_components.clear_cache(
            script_ids=["script_1", "script_2"],
            language="python"
        )
        
        # Assert
        assert response.cleared_count == 3
        assert response.cleared_script_ids == ["script_1", "script_2"]
        assert response.total_size_freed_bytes == 0
        
        # Verify cache manager was called
        mock_client_components.cache_manager.clear_scripts.assert_called_once_with(
            script_ids=["script_1", "script_2"],
            language="python",
            older_than=None,
            all_scripts=False
        )
    
    @pytest.mark.asyncio
    async def test_clear_cache_all(self, mock_client_components):
        """Test clearing all cache through client."""
        # Arrange
        mock_client_components.cache_manager.clear_scripts = AsyncMock(return_value=10)
        
        # Act
        response = await mock_client_components.clear_cache(all_scripts=True)
        
        # Assert
        assert response.cleared_count == 10
        assert response.cleared_script_ids == []
        
        # Verify cache manager was called
        mock_client_components.cache_manager.clear_scripts.assert_called_once_with(
            script_ids=None,
            language=None,
            older_than=None,
            all_scripts=True
        )
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_client_components):
        """Test health check through client."""
        # Arrange
        mock_client_components.container_runner.health_check = AsyncMock(return_value=True)
        mock_client_components.fallback_manager.get_provider_stats = Mock(return_value={
            "total_requests": 10,
            "total_successes": 9,
            "total_failures": 1,
            "success_rate": 90.0,
            "providers": {}
        })
        
        # Act
        health = await mock_client_components.health_check()
        
        # Assert
        assert health["overall"] is True
        assert "components" in health
        
        # Check cache component
        assert "cache" in health["components"]
        assert health["components"]["cache"]["healthy"] is True
        
        # Check LLM providers component
        assert "llm_providers" in health["components"]
        assert health["components"]["llm_providers"]["healthy"] is True
        
        # Check container runner component
        assert "container_runner" in health["components"]
        assert health["components"]["container_runner"]["healthy"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_client_components):
        """Test health check with component failure."""
        # Arrange
        mock_client_components.cache_manager.get_cache_stats.side_effect = Exception("Cache error")
        mock_client_components.container_runner.health_check = AsyncMock(return_value=True)
        mock_client_components.fallback_manager.get_provider_stats = Mock(return_value={})
        
        # Act
        health = await mock_client_components.health_check()
        
        # Assert
        assert health["overall"] is False
        
        # Check cache component failure
        assert health["components"]["cache"]["healthy"] is False
        assert "error" in health["components"]["cache"]
        assert "Cache error" in health["components"]["cache"]["error"]
    
    def test_get_stats(self, mock_client_components):
        """Test getting statistics through client."""
        # Arrange
        mock_client_components.fallback_manager.get_provider_stats = Mock(return_value={
            "total_requests": 10,
            "success_rate": 90.0,
            "providers": {}
        })
        mock_client_components.script_generator.get_generation_stats = Mock(return_value={
            "total_generations": 5,
            "success_rate_percent": 80.0
        })
        
        # Act
        stats = mock_client_components.get_stats()
        
        # Assert
        assert "cache" in stats
        assert "llm_providers" in stats
        assert "script_generator" in stats
        
        # Verify individual components were called
        mock_client_components.cache_manager.get_cache_stats.assert_called_once()
        mock_client_components.fallback_manager.get_provider_stats.assert_called_once()
        mock_client_components.script_generator.get_generation_stats.assert_called_once()
