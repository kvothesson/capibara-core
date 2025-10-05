"""Groq LLM provider implementation."""

import asyncio
from typing import Any

from groq import AsyncGroq

from capibara.llm_providers.base import LLMProvider, LLMProviderConfig, LLMResponse
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class GroqProvider(LLMProvider):
    """Groq LLM provider."""

    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        self.client = AsyncGroq(
            api_key=config.api_key,
            base_url=config.base_url,
        )

    async def generate_code(self, prompt: str, language: str, **kwargs: Any) -> str:
        """Generate code using Groq API."""
        logger.debug("Generating code with Groq", model=self.model, language=language)

        try:
            response = await self._make_request(
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert {language} developer. Generate clean, production-ready code.",
                    },
                    {"role": "user", "content": prompt},
                ],
                **kwargs,
            )

            return response.content

        except Exception as e:
            logger.error("Groq code generation failed", error=str(e), model=self.model)
            raise LLMProviderError(f"Groq code generation failed: {str(e)}") from e

    async def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using Groq API."""
        logger.debug("Generating text with Groq", model=self.model)

        try:
            response = await self._make_request(
                messages=[{"role": "user", "content": prompt}], **kwargs
            )

            return response.content

        except Exception as e:
            logger.error("Groq text generation failed", error=str(e), model=self.model)
            raise LLMProviderError(f"Groq text generation failed: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check if Groq API is accessible."""
        try:
            # Simple health check with minimal request
            await self._make_request(
                messages=[{"role": "user", "content": "Hello"}], max_tokens=1
            )
            return True
        except Exception as e:
            logger.warning("Groq health check failed", error=str(e))
            return False

    async def _make_request(self, messages: list, **kwargs: Any) -> LLMResponse:
        """Make a request to Groq API with retry logic."""
        max_retries = self.config.retry_attempts
        timeout = self.config.timeout_seconds

        for attempt in range(max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                        temperature=kwargs.get("temperature", self.config.temperature),
                        **{
                            k: v
                            for k, v in kwargs.items()
                            if k not in ["max_tokens", "temperature"]
                        },
                    ),
                    timeout=timeout,
                )

                return LLMResponse(
                    content=response.choices[0].message.content,
                    model=self.model,
                    provider=self.name,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                    metadata={
                        "finish_reason": response.choices[0].finish_reason,
                        "model": response.model,
                    },
                )

            except TimeoutError as e:
                logger.warning(
                    "Groq request timeout", attempt=attempt + 1, max_retries=max_retries
                )
                if attempt == max_retries:
                    raise LLMProviderError("Groq request timed out") from e

            except Exception as e:
                if "rate_limit" in str(e).lower():
                    logger.warning("Groq rate limit", attempt=attempt + 1, error=str(e))
                    if attempt == max_retries:
                        raise LLMProviderError(
                            f"Groq rate limit exceeded: {str(e)}"
                        ) from e
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    logger.error("Groq API error", attempt=attempt + 1, error=str(e))
                    if attempt == max_retries:
                        raise LLMProviderError(f"Groq API error: {str(e)}") from e
                    await asyncio.sleep(1)

        raise LLMProviderError("Max retries exceeded")


class LLMProviderError(Exception):
    """Raised when LLM provider operations fail."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
