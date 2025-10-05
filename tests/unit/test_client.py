"""Unit tests for Capibara Client."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from capibara.sdk.client import CapibaraClient
from capibara.models.requests import RunRequest
from capibara.models.responses import RunResponse, ListResponse, ShowResponse, ClearResponse


class TestCapibaraClient:
    """Test cases for CapibaraClient."""
    
    @pytest.fixture
    def mock_engine(self):
        """Create mock engine."""
        engine = Mock()
        engine.run_script = AsyncMock()
        return engine
    
    @pytest.fixture
    def mock_cache_manager(self):
        """Create mock cache manager."""
        cache_manager = Mock()
        cache_manager.list_scripts = AsyncMock()
        cache_manager.get_script = AsyncMock()
        cache_manager.clear_scripts = AsyncMock()
        cache_manager.get_cache_stats = Mock()
        return cache_manager
    
    @pytest.fixture
    def mock_fallback_manager(self):
        """Create mock fallback manager."""
        fallback_manager = Mock()
        fallback_manager.get_provider_stats = Mock()
        return fallback_manager
    
    @pytest.fixture
    def mock_script_generator(self):
        """Create mock script generator."""
        script_generator = Mock()
        script_generator.get_generation_stats = Mock()
        return script_generator
    
    @pytest.fixture
    def mock_container_runner(self):
        """Create mock container runner."""
        container_runner = Mock()
        container_runner.health_check = AsyncMock(return_value=True)
        return container_runner
    
    @patch('capibara.sdk.client.CapibaraEngine')
    @patch('capibara.sdk.client.CacheManager')
    @patch('capibara.sdk.client.ScriptGenerator')
    @patch('capibara.sdk.client.ASTScanner')
    @patch('capibara.sdk.client.PolicyManager')
    @patch('capibara.sdk.client.ContainerRunner')
    @patch('capibara.sdk.client.FallbackManager')
    @patch('capibara.sdk.client.OpenAIProvider')
    @patch('capibara.sdk.client.GroqProvider')
    def test_client_initialization(self, mock_groq, mock_openai, mock_fallback, 
                                   mock_container, mock_policy, mock_ast, 
                                   mock_script_gen, mock_cache, mock_engine):
        """Test client initialization with API keys."""
        # Arrange
        mock_openai.return_value = Mock()
        mock_groq.return_value = Mock()
        mock_fallback.return_value = Mock()
        mock_container.return_value = Mock()
        mock_policy.return_value = Mock()
        mock_ast.return_value = Mock()
        mock_script_gen.return_value = Mock()
        mock_cache.return_value = Mock()
        mock_engine.return_value = Mock()
        
        # Act
        client = CapibaraClient(
            openai_api_key="test_openai_key",
            groq_api_key="test_groq_key"
        )
        
        # Assert
        assert client is not None
        mock_openai.assert_called_once()
        mock_groq.assert_called_once()
        mock_fallback.assert_called_once()
        mock_engine.assert_called_once()
    
    @patch('capibara.sdk.client.CapibaraEngine')
    @patch('capibara.sdk.client.CacheManager')
    @patch('capibara.sdk.client.ScriptGenerator')
    @patch('capibara.sdk.client.ASTScanner')
    @patch('capibara.sdk.client.PolicyManager')
    @patch('capibara.sdk.client.ContainerRunner')
    @patch('capibara.sdk.client.FallbackManager')
    def test_client_initialization_no_api_keys(self, mock_fallback, mock_container, 
                                               mock_policy, mock_ast, mock_script_gen, 
                                               mock_cache, mock_engine):
        """Test client initialization without API keys raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="At least one LLM provider API key must be provided"):
            CapibaraClient()
    
    @pytest.mark.asyncio
    async def test_run_method(self, mock_engine, mock_cache_manager, 
                             mock_fallback_manager, mock_script_generator, 
                             mock_container_runner):
        """Test run method."""
        # Arrange
        with patch('capibara.sdk.client.CapibaraEngine', return_value=mock_engine), \
             patch('capibara.sdk.client.CacheManager', return_value=mock_cache_manager), \
             patch('capibara.sdk.client.ScriptGenerator', return_value=mock_script_generator), \
             patch('capibara.sdk.client.ASTScanner', return_value=Mock()), \
             patch('capibara.sdk.client.PolicyManager', return_value=Mock()), \
             patch('capibara.sdk.client.ContainerRunner', return_value=mock_container_runner), \
             patch('capibara.sdk.client.FallbackManager', return_value=mock_fallback_manager), \
             patch('capibara.sdk.client.OpenAIProvider'), \
             patch('capibara.sdk.client.GroqProvider'):
            
            client = CapibaraClient(openai_api_key="test_key")
            
            # Mock response
            mock_response = RunResponse(
                script_id="test_script_123",
                prompt="test prompt",
                language="python",
                code="print('Hello, World!')",
                execution_result=None,
                cached=False,
                security_policy="moderate",
                llm_provider="openai",
                fingerprint="test_fingerprint",
                created_at=datetime.utcnow(),
                metadata={}
            )
            mock_engine.run_script.return_value = mock_response
            
            # Act
            response = await client.run(
                prompt="test prompt",
                language="python",
                execute=False
            )
            
            # Assert
            assert response.script_id == "test_script_123"
            assert response.code == "print('Hello, World!')"
            mock_engine.run_script.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_scripts(self, mock_engine, mock_cache_manager, 
                               mock_fallback_manager, mock_script_generator, 
                               mock_container_runner):
        """Test list_scripts method."""
        # Arrange
        with patch('capibara.sdk.client.CapibaraEngine', return_value=mock_engine), \
             patch('capibara.sdk.client.CacheManager', return_value=mock_cache_manager), \
             patch('capibara.sdk.client.ScriptGenerator', return_value=mock_script_generator), \
             patch('capibara.sdk.client.ASTScanner', return_value=Mock()), \
             patch('capibara.sdk.client.PolicyManager', return_value=Mock()), \
             patch('capibara.sdk.client.ContainerRunner', return_value=mock_container_runner), \
             patch('capibara.sdk.client.FallbackManager', return_value=mock_fallback_manager), \
             patch('capibara.sdk.client.OpenAIProvider'), \
             patch('capibara.sdk.client.GroqProvider'):
            
            client = CapibaraClient(openai_api_key="test_key")
            
            # Mock script data
            mock_scripts = [
                {
                    "script_id": "script_1",
                    "prompt": "test prompt 1",
                    "language": "python",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "execution_count": 5,
                    "cache_hit_count": 10,
                    "llm_provider": "openai",
                    "fingerprint": "fingerprint_1",
                    "size_bytes": 1000
                },
                {
                    "script_id": "script_2", 
                    "prompt": "test prompt 2",
                    "language": "javascript",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "execution_count": 3,
                    "cache_hit_count": 7,
                    "llm_provider": "groq",
                    "fingerprint": "fingerprint_2",
                    "size_bytes": 1500
                }
            ]
            mock_cache_manager.list_scripts.return_value = mock_scripts
            
            # Act
            response = await client.list_scripts(limit=10, offset=0)
            
            # Assert
            assert len(response.scripts) == 2
            assert response.scripts[0].script_id == "script_1"
            assert response.scripts[1].script_id == "script_2"
            mock_cache_manager.list_scripts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_show_script(self, mock_engine, mock_cache_manager, 
                              mock_fallback_manager, mock_script_generator, 
                              mock_container_runner):
        """Test show_script method."""
        # Arrange
        with patch('capibara.sdk.client.CapibaraEngine', return_value=mock_engine), \
             patch('capibara.sdk.client.CacheManager', return_value=mock_cache_manager), \
             patch('capibara.sdk.client.ScriptGenerator', return_value=mock_script_generator), \
             patch('capibara.sdk.client.ASTScanner', return_value=Mock()), \
             patch('capibara.sdk.client.PolicyManager', return_value=Mock()), \
             patch('capibara.sdk.client.ContainerRunner', return_value=mock_container_runner), \
             patch('capibara.sdk.client.FallbackManager', return_value=mock_fallback_manager), \
             patch('capibara.sdk.client.OpenAIProvider'), \
             patch('capibara.sdk.client.GroqProvider'):
            
            client = CapibaraClient(openai_api_key="test_key")
            
            # Mock script data
            mock_script = {
                "script_id": "test_script_123",
                "prompt": "test prompt",
                "language": "python",
                "code": "print('Hello, World!')",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "execution_count": 5,
                "cache_hit_count": 10,
                "llm_provider": "openai",
                "fingerprint": "test_fingerprint",
                "size_bytes": 1000
            }
            mock_cache_manager.get_script.return_value = mock_script
            
            # Act
            response = await client.show_script("test_script_123", include_code=True)
            
            # Assert
            assert response.script.script_id == "test_script_123"
            assert response.code == "print('Hello, World!')"
            mock_cache_manager.get_script.assert_called_once_with("test_script_123")
    
    @pytest.mark.asyncio
    async def test_show_script_not_found(self, mock_engine, mock_cache_manager, 
                                        mock_fallback_manager, mock_script_generator, 
                                        mock_container_runner):
        """Test show_script method when script not found."""
        # Arrange
        with patch('capibara.sdk.client.CapibaraEngine', return_value=mock_engine), \
             patch('capibara.sdk.client.CacheManager', return_value=mock_cache_manager), \
             patch('capibara.sdk.client.ScriptGenerator', return_value=mock_script_generator), \
             patch('capibara.sdk.client.ASTScanner', return_value=Mock()), \
             patch('capibara.sdk.client.PolicyManager', return_value=Mock()), \
             patch('capibara.sdk.client.ContainerRunner', return_value=mock_container_runner), \
             patch('capibara.sdk.client.FallbackManager', return_value=mock_fallback_manager), \
             patch('capibara.sdk.client.OpenAIProvider'), \
             patch('capibara.sdk.client.GroqProvider'):
            
            client = CapibaraClient(openai_api_key="test_key")
            
            # Mock script not found
            mock_cache_manager.get_script.return_value = None
            
            # Act & Assert
            with pytest.raises(ValueError, match="Script not found: test_script_123"):
                await client.show_script("test_script_123")
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, mock_engine, mock_cache_manager, 
                              mock_fallback_manager, mock_script_generator, 
                              mock_container_runner):
        """Test clear_cache method."""
        # Arrange
        with patch('capibara.sdk.client.CapibaraEngine', return_value=mock_engine), \
             patch('capibara.sdk.client.CacheManager', return_value=mock_cache_manager), \
             patch('capibara.sdk.client.ScriptGenerator', return_value=mock_script_generator), \
             patch('capibara.sdk.client.ASTScanner', return_value=Mock()), \
             patch('capibara.sdk.client.PolicyManager', return_value=Mock()), \
             patch('capibara.sdk.client.ContainerRunner', return_value=mock_container_runner), \
             patch('capibara.sdk.client.FallbackManager', return_value=mock_fallback_manager), \
             patch('capibara.sdk.client.OpenAIProvider'), \
             patch('capibara.sdk.client.GroqProvider'):
            
            client = CapibaraClient(openai_api_key="test_key")
            
            # Mock cache clearing
            mock_cache_manager.clear_scripts.return_value = 5
            
            # Act
            response = await client.clear_cache(
                script_ids=["script_1", "script_2"],
                language="python"
            )
            
            # Assert
            assert response.cleared_count == 5
            assert len(response.cleared_script_ids) == 2
            mock_cache_manager.clear_scripts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_engine, mock_cache_manager, 
                               mock_fallback_manager, mock_script_generator, 
                               mock_container_runner):
        """Test health_check method."""
        # Arrange
        with patch('capibara.sdk.client.CapibaraEngine', return_value=mock_engine), \
             patch('capibara.sdk.client.CacheManager', return_value=mock_cache_manager), \
             patch('capibara.sdk.client.ScriptGenerator', return_value=mock_script_generator), \
             patch('capibara.sdk.client.ASTScanner', return_value=Mock()), \
             patch('capibara.sdk.client.PolicyManager', return_value=Mock()), \
             patch('capibara.sdk.client.ContainerRunner', return_value=mock_container_runner), \
             patch('capibara.sdk.client.FallbackManager', return_value=mock_fallback_manager), \
             patch('capibara.sdk.client.OpenAIProvider'), \
             patch('capibara.sdk.client.GroqProvider'):
            
            client = CapibaraClient(openai_api_key="test_key")
            
            # Mock health check responses
            mock_cache_manager.get_cache_stats.return_value = {"total_scripts": 10}
            mock_fallback_manager.get_provider_stats.return_value = {"total_requests": 100}
            mock_container_runner.health_check.return_value = True
            
            # Act
            health = await client.health_check()
            
            # Assert
            assert health["overall"] is True
            assert "components" in health
            assert "cache" in health["components"]
            assert "llm_providers" in health["components"]
            assert "container_runner" in health["components"]
    
    def test_get_stats(self, mock_engine, mock_cache_manager, 
                       mock_fallback_manager, mock_script_generator, 
                       mock_container_runner):
        """Test get_stats method."""
        # Arrange
        with patch('capibara.sdk.client.CapibaraEngine', return_value=mock_engine), \
             patch('capibara.sdk.client.CacheManager', return_value=mock_cache_manager), \
             patch('capibara.sdk.client.ScriptGenerator', return_value=mock_script_generator), \
             patch('capibara.sdk.client.ASTScanner', return_value=Mock()), \
             patch('capibara.sdk.client.PolicyManager', return_value=Mock()), \
             patch('capibara.sdk.client.ContainerRunner', return_value=mock_container_runner), \
             patch('capibara.sdk.client.FallbackManager', return_value=mock_fallback_manager), \
             patch('capibara.sdk.client.OpenAIProvider'), \
             patch('capibara.sdk.client.GroqProvider'):
            
            client = CapibaraClient(openai_api_key="test_key")
            
            # Mock stats
            mock_cache_manager.get_cache_stats.return_value = {"cache_stats": "data"}
            mock_fallback_manager.get_provider_stats.return_value = {"provider_stats": "data"}
            mock_script_generator.get_generation_stats.return_value = {"generation_stats": "data"}
            
            # Act
            stats = client.get_stats()
            
            # Assert
            assert "cache" in stats
            assert "llm_providers" in stats
            assert "script_generator" in stats
            assert stats["cache"] == {"cache_stats": "data"}
            assert stats["llm_providers"] == {"provider_stats": "data"}
            assert stats["script_generator"] == {"generation_stats": "data"}
