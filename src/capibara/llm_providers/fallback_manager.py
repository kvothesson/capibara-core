"""Fallback manager for LLM providers."""

from typing import Any, Dict, List, Optional

from capibara.llm_providers.base import LLMProvider, LLMProviderConfig
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class FallbackManager:
    """Manages multiple LLM providers with fallback support."""
    
    def __init__(self, providers: List[LLMProvider]):
        self.providers = {provider.name: provider for provider in providers}
        self.provider_stats = {
            name: {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "last_used": None,
                "health_status": True,
            }
            for name in self.providers.keys()
        }
    
    async def get_provider(self, preferred_provider: Optional[str] = None) -> LLMProvider:
        """Get the best available provider."""
        # If a specific provider is requested and available, use it
        if preferred_provider and preferred_provider in self.providers:
            provider = self.providers[preferred_provider]
            if provider.is_enabled() and await self._is_provider_healthy(provider):
                logger.debug("Using preferred provider", provider=preferred_provider)
                return provider
        
        # Get available providers sorted by priority
        available_providers = [
            provider for provider in self.providers.values()
            if provider.is_enabled() and self.provider_stats[provider.name]["health_status"]
        ]
        
        if not available_providers:
            raise NoAvailableProvidersError("No healthy providers available")
        
        # Sort by priority (lower number = higher priority)
        available_providers.sort(key=lambda p: p.get_priority())
        
        # Try providers in order
        for provider in available_providers:
            try:
                if await self._is_provider_healthy(provider):
                    logger.debug("Using provider", provider=provider.name)
                    return provider
            except Exception as e:
                logger.warning("Provider health check failed", 
                             provider=provider.name, error=str(e))
                self.provider_stats[provider.name]["health_status"] = False
        
        raise NoAvailableProvidersError("No healthy providers available")
    
    async def _is_provider_healthy(self, provider: LLMProvider) -> bool:
        """Check if a provider is healthy."""
        try:
            is_healthy = await provider.health_check()
            self.provider_stats[provider.name]["health_status"] = is_healthy
            return is_healthy
        except Exception as e:
            logger.warning("Provider health check failed", 
                         provider=provider.name, error=str(e))
            self.provider_stats[provider.name]["health_status"] = False
            return False
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics for all providers."""
        total_requests = sum(stats["requests"] for stats in self.provider_stats.values())
        total_successes = sum(stats["successes"] for stats in self.provider_stats.values())
        total_failures = sum(stats["failures"] for stats in self.provider_stats.values())
        
        return {
            "total_requests": total_requests,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "success_rate": (total_successes / total_requests * 100) if total_requests > 0 else 0,
            "providers": {
                name: {
                    **stats,
                    "success_rate": (stats["successes"] / stats["requests"] * 100) 
                                   if stats["requests"] > 0 else 0,
                }
                for name, stats in self.provider_stats.items()
            }
        }
    
    def record_request(self, provider_name: str, success: bool) -> None:
        """Record a request result for a provider."""
        if provider_name in self.provider_stats:
            self.provider_stats[provider_name]["requests"] += 1
            if success:
                self.provider_stats[provider_name]["successes"] += 1
            else:
                self.provider_stats[provider_name]["failures"] += 1
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return [
            name for name, provider in self.providers.items()
            if provider.is_enabled() and self.provider_stats[name]["health_status"]
        ]
    
    def disable_provider(self, provider_name: str) -> None:
        """Disable a provider."""
        if provider_name in self.providers:
            self.providers[provider_name].enabled = False
            logger.info("Provider disabled", provider=provider_name)
    
    def enable_provider(self, provider_name: str) -> None:
        """Enable a provider."""
        if provider_name in self.providers:
            self.providers[provider_name].enabled = True
            logger.info("Provider enabled", provider=provider_name)
    
    def add_provider(self, provider: LLMProvider) -> None:
        """Add a new provider."""
        self.providers[provider.name] = provider
        self.provider_stats[provider.name] = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "last_used": None,
            "health_status": True,
        }
        logger.info("Provider added", provider=provider.name)
    
    def remove_provider(self, provider_name: str) -> None:
        """Remove a provider."""
        if provider_name in self.providers:
            del self.providers[provider_name]
            del self.provider_stats[provider_name]
            logger.info("Provider removed", provider=provider_name)


class NoAvailableProvidersError(Exception):
    """Raised when no providers are available."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
