"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class LLMProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    name: str = Field(..., description="Provider name")
    api_key: str | None = Field(None, description="API key")
    base_url: str | None = Field(None, description="Base URL")
    model: str = Field(..., description="Model name")
    max_tokens: int = Field(4000, description="Maximum tokens")
    temperature: float = Field(0.7, description="Temperature")
    timeout_seconds: int = Field(30, description="Timeout in seconds")
    retry_attempts: int = Field(3, description="Retry attempts")
    priority: int = Field(1, description="Priority (lower = higher)")
    enabled: bool = Field(True, description="Whether enabled")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional config"
    )


class LLMResponse(BaseModel):
    """Response from LLM provider."""

    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used")
    provider: str = Field(..., description="Provider name")
    usage: dict[str, Any] = Field(default_factory=dict, description="Usage statistics")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class LLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, config: LLMProviderConfig):
        self.config = config
        self.name = config.name
        self.model = config.model
        self.enabled = config.enabled

    @abstractmethod
    async def generate_code(self, prompt: str, language: str, **kwargs: Any) -> str:
        """Generate code from a prompt."""
        pass

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from a prompt."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        pass

    def get_config(self) -> LLMProviderConfig:
        """Get provider configuration."""
        return self.config

    def is_enabled(self) -> bool:
        """Check if provider is enabled."""
        return self.enabled

    def get_priority(self) -> int:
        """Get provider priority."""
        return self.config.priority
