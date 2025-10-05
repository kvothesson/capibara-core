"""Unit tests for LLM Providers."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from capibara.llm_providers.openai_provider import OpenAIProvider, LLMProviderError
from capibara.llm_providers.groq_provider import GroqProvider
from capibara.llm_providers.fallback_manager import FallbackManager, NoAvailableProvidersError
from capibara.llm_providers.base import LLMProviderConfig, LLMResponse


class TestOpenAIProvider:
    """Test cases for OpenAIProvider."""
    
    @pytest.fixture
    def openai_config(self):
        """Create OpenAI provider config."""
        return LLMProviderConfig(
            name="openai",
            api_key="test_api_key",
            model="gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.7,
            timeout_seconds=30,
            retry_attempts=3,
        )
    
    @pytest.fixture
    def openai_provider(self, openai_config):
        """Create OpenAIProvider instance."""
        return OpenAIProvider(openai_config)
    
    @pytest.mark.asyncio
    async def test_generate_code_success(self, openai_provider):
        """Test successful code generation."""
        # Arrange
        prompt = "Create a hello world function"
        language = "python"
        
        # Mock the OpenAI client response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "def hello():\n    print('Hello, World!')"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 15
        mock_response.usage.total_tokens = 25
        mock_response.model = "gpt-3.5-turbo"
        
        with patch.object(openai_provider.client.chat.completions, 'create', 
                         new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            # Act
            result = await openai_provider.generate_code(prompt, language)
            
            # Assert
            assert result == "def hello():\n    print('Hello, World!')"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self, openai_provider):
        """Test successful text generation."""
        # Arrange
        prompt = "Explain machine learning"
        
        # Mock the OpenAI client response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Machine learning is..."
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 55
        mock_response.model = "gpt-3.5-turbo"
        
        with patch.object(openai_provider.client.chat.completions, 'create',
                         new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            # Act
            result = await openai_provider.generate_text(prompt)
            
            # Assert
            assert result == "Machine learning is..."
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, openai_provider):
        """Test successful health check."""
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello"
        
        with patch.object(openai_provider.client.chat.completions, 'create',
                         new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            # Act
            result = await openai_provider.health_check()
            
            # Assert
            assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, openai_provider):
        """Test health check failure."""
        # Mock failure
        with patch.object(openai_provider.client.chat.completions, 'create',
                         new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            # Act
            result = await openai_provider.health_check()
            
            # Assert
            assert result is False
    
    def test_llm_provider_error(self):
        """Test LLMProviderError exception."""
        # Test basic error
        error = LLMProviderError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}
        
        # Test error with details
        details = {"provider": "openai", "model": "gpt-3.5-turbo"}
        error_with_details = LLMProviderError("Test error", details)
        assert error_with_details.details == details


class TestGroqProvider:
    """Test cases for GroqProvider."""
    
    @pytest.fixture
    def groq_config(self):
        """Create Groq provider config."""
        return LLMProviderConfig(
            name="groq",
            api_key="test_api_key",
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            temperature=0.7,
            timeout_seconds=30,
            retry_attempts=3,
        )
    
    @pytest.fixture
    def groq_provider(self, groq_config):
        """Create GroqProvider instance."""
        return GroqProvider(groq_config)
    
    @pytest.mark.asyncio
    async def test_generate_code_success(self, groq_provider):
        """Test successful code generation."""
        # Arrange
        prompt = "Create a hello world function"
        language = "python"
        
        # Mock the Groq client response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "def hello():\n    print('Hello, World!')"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 15
        mock_response.usage.total_tokens = 25
        mock_response.model = "llama-3.3-70b-versatile"
        
        with patch.object(groq_provider.client.chat.completions, 'create',
                         new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            # Act
            result = await groq_provider.generate_code(prompt, language)
            
            # Assert
            assert result == "def hello():\n    print('Hello, World!')"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, groq_provider):
        """Test successful health check."""
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello"
        
        with patch.object(groq_provider.client.chat.completions, 'create',
                         new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            # Act
            result = await groq_provider.health_check()
            
            # Assert
            assert result is True


class TestFallbackManager:
    """Test cases for FallbackManager."""
    
    @pytest.fixture
    def mock_providers(self):
        """Create mock providers."""
        provider1 = Mock()
        provider1.name = "openai"
        provider1.is_enabled.return_value = True
        provider1.get_priority.return_value = 1
        provider1.health_check = AsyncMock(return_value=True)
        
        provider2 = Mock()
        provider2.name = "groq"
        provider2.is_enabled.return_value = True
        provider2.get_priority.return_value = 2
        provider2.health_check = AsyncMock(return_value=True)
        
        return [provider1, provider2]
    
    @pytest.fixture
    def fallback_manager(self, mock_providers):
        """Create FallbackManager instance."""
        return FallbackManager(mock_providers)
    
    @pytest.mark.asyncio
    async def test_get_provider_by_preference(self, fallback_manager, mock_providers):
        """Test getting provider by preference."""
        # Act
        provider = await fallback_manager.get_provider("openai")
        
        # Assert
        assert provider == mock_providers[0]
    
    @pytest.mark.asyncio
    async def test_get_provider_by_priority(self, fallback_manager, mock_providers):
        """Test getting provider by priority."""
        # Act
        provider = await fallback_manager.get_provider()
        
        # Assert - should return the provider with highest priority (lowest number)
        assert provider == mock_providers[0]  # openai has priority 1
    
    @pytest.mark.asyncio
    async def test_get_provider_fallback(self, fallback_manager, mock_providers):
        """Test provider fallback when preferred provider fails."""
        # Arrange - make first provider unhealthy
        mock_providers[0].health_check.return_value = False
        
        # Act
        provider = await fallback_manager.get_provider("openai")
        
        # Assert - should fallback to second provider
        assert provider == mock_providers[1]
    
    @pytest.mark.asyncio
    async def test_no_available_providers(self, fallback_manager, mock_providers):
        """Test when no providers are available."""
        # Arrange - make all providers unhealthy
        for provider in mock_providers:
            provider.health_check.return_value = False
        
        # Act & Assert
        with pytest.raises(NoAvailableProvidersError):
            await fallback_manager.get_provider()
    
    def test_provider_stats(self, fallback_manager):
        """Test provider statistics."""
        # Initial stats
        stats = fallback_manager.get_provider_stats()
        assert stats["total_requests"] == 0
        assert stats["total_successes"] == 0
        assert stats["total_failures"] == 0
        assert stats["success_rate"] == 0
        assert "providers" in stats
    
    def test_record_request(self, fallback_manager):
        """Test recording request results."""
        # Act
        fallback_manager.record_request("openai", True)
        fallback_manager.record_request("openai", False)
        fallback_manager.record_request("groq", True)
        
        # Assert
        stats = fallback_manager.get_provider_stats()
        assert stats["total_requests"] == 3
        assert stats["total_successes"] == 2
        assert stats["total_failures"] == 1
        assert abs(stats["success_rate"] - 66.67) < 0.01  # 2/3 * 100 with tolerance
    
    def test_provider_management(self, fallback_manager, mock_providers):
        """Test provider enable/disable functionality."""
        # Test disable
        fallback_manager.disable_provider("openai")
        mock_providers[0].enabled = False
        
        # Test enable
        fallback_manager.enable_provider("openai")
        mock_providers[0].enabled = True
        
        # Test add provider
        new_provider = Mock()
        new_provider.name = "new_provider"
        new_provider.is_enabled.return_value = True
        new_provider.get_priority.return_value = 3
        new_provider.health_check = AsyncMock(return_value=True)
        
        fallback_manager.add_provider(new_provider)
        assert "new_provider" in fallback_manager.providers
        
        # Test remove provider
        fallback_manager.remove_provider("new_provider")
        assert "new_provider" not in fallback_manager.providers
    
    def test_no_available_providers_error(self):
        """Test NoAvailableProvidersError exception."""
        # Test basic error
        error = NoAvailableProvidersError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}
        
        # Test error with details
        details = {"available_providers": [], "last_error": "All providers down"}
        error_with_details = NoAvailableProvidersError("Test error", details)
        assert error_with_details.details == details
