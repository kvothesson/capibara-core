"""Main SDK client for Capibara Core."""

from typing import Any

from capibara.core.cache_manager import CacheManager
from capibara.core.engine import CapibaraEngine
from capibara.core.script_generator import ScriptGenerator
from capibara.llm_providers.base import LLMProvider, LLMProviderConfig
from capibara.llm_providers.fallback_manager import FallbackManager
from capibara.llm_providers.groq_provider import GroqProvider
from capibara.llm_providers.openai_provider import OpenAIProvider
from capibara.models.requests import ClearRequest, ListRequest, RunRequest
from capibara.models.responses import (
    ClearResponse,
    ListResponse,
    RunResponse,
    ScriptInfo,
    ShowResponse,
)
from capibara.runner.container_runner import ContainerRunner
from capibara.security.ast_scanner import ASTScanner
from capibara.security.policy_manager import PolicyManager
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class CapibaraClient:
    """Main client for interacting with Capibara Core."""

    def __init__(
        self,
        openai_api_key: str | None = None,
        groq_api_key: str | None = None,
        cache_dir: str = "~/.capibara/cache",
        policies_dir: str = "config/security-policies",
    ):
        self.cache_dir = cache_dir
        self.policies_dir = policies_dir

        # Initialize components
        self._initialize_components(openai_api_key, groq_api_key)

        logger.info("Capibara client initialized")

    def _initialize_components(
        self,
        openai_api_key: str | None,
        groq_api_key: str | None,
    ) -> None:
        """Initialize all Capibara components."""
        # Cache manager
        self.cache_manager = CacheManager(cache_dir=self.cache_dir)

        # Security components
        self.ast_scanner = ASTScanner()
        self.policy_manager = PolicyManager(policies_dir=self.policies_dir)

        # Container runner
        self.container_runner = ContainerRunner()

        # LLM providers
        providers: list[LLMProvider] = []

        if openai_api_key:
            openai_config = LLMProviderConfig(
                name="openai",
                api_key=openai_api_key,
                base_url=None,
                model="gpt-3.5-turbo",
                max_tokens=4000,
                temperature=0.7,
                timeout_seconds=30,
                retry_attempts=3,
                priority=1,
                enabled=True,
            )
            providers.append(OpenAIProvider(openai_config))

        if groq_api_key:
            groq_config = LLMProviderConfig(
                name="groq",
                api_key=groq_api_key,
                base_url=None,
                model="llama-3.3-70b-versatile",
                max_tokens=4000,
                temperature=0.7,
                timeout_seconds=30,
                retry_attempts=3,
                priority=1,
                enabled=True,
            )
            providers.append(GroqProvider(groq_config))

        if not providers:
            raise ValueError("At least one LLM provider API key must be provided")

        self.fallback_manager = FallbackManager(providers)

        # Script generator
        self.script_generator = ScriptGenerator(self.fallback_manager)

        # Main engine
        self.engine = CapibaraEngine(
            cache_manager=self.cache_manager,
            script_generator=self.script_generator,
            ast_scanner=self.ast_scanner,
            policy_manager=self.policy_manager,
            container_runner=self.container_runner,
            fallback_manager=self.fallback_manager,
        )

    async def run(
        self,
        prompt: str,
        language: str = "python",
        context: dict[str, Any] | None = None,
        security_policy: str | None = None,
        llm_provider: str | None = None,
        execute: bool = False,
        **kwargs: Any,
    ) -> RunResponse:
        """Generate and optionally execute a script from a natural language prompt."""
        logger.info("Running script generation", prompt_length=len(prompt))

        request = RunRequest(
            prompt=prompt,
            context=context,
            language=language,
            security_policy=security_policy,
            llm_provider=llm_provider,
            execute=execute,
            **kwargs,
        )

        return await self.engine.run_script(request)

    async def list_scripts(
        self,
        limit: int = 50,
        offset: int = 0,
        language: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> ListResponse:
        """List cached scripts."""
        logger.info("Listing scripts", limit=limit, offset=offset)

        request = ListRequest(
            limit=limit,
            offset=offset,
            language=language,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Get scripts from cache manager
        scripts_data = await self.cache_manager.list_scripts(
            limit=limit,
            offset=offset,
            language=language,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Convert script data to ScriptInfo objects
        scripts: list[ScriptInfo] = []
        for script_data in scripts_data:
            script = ScriptInfo(
                script_id=script_data["script_id"],
                prompt=script_data["prompt"],
                language=script_data["language"],
                created_at=script_data["created_at"],
                updated_at=script_data["updated_at"],
                execution_count=script_data.get("execution_count", 0),
                last_executed_at=script_data.get("last_executed_at"),
                cache_hit_count=script_data.get("cache_hit_count", 0),
                security_policy=script_data.get("security_policy"),
                llm_provider=script_data.get("llm_provider", "unknown"),
                fingerprint=script_data.get("fingerprint", ""),
                size_bytes=script_data.get("size_bytes", 0),
                metadata=script_data.get("metadata", {}),
            )
            scripts.append(script)

        return ListResponse(
            scripts=scripts,
            total_count=len(scripts),  # Simplified - would need proper counting
            limit=request.limit,
            offset=request.offset,
            has_more=len(scripts) == request.limit,
        )

    async def show_script(
        self,
        script_id: str,
        include_code: bool = True,
        include_execution_logs: bool = False,
    ) -> ShowResponse:
        """Show details of a specific script."""
        logger.info("Showing script", script_id=script_id)

        # Get script from cache manager
        script_data = await self.cache_manager.get_script(script_id)

        if script_data is None:
            raise ValueError(f"Script not found: {script_id}")

        # Convert script data to ScriptInfo object
        script = ScriptInfo(
            script_id=script_data["script_id"],
            prompt=script_data["prompt"],
            language=script_data["language"],
            created_at=script_data["created_at"],
            updated_at=script_data["updated_at"],
            execution_count=script_data.get("execution_count", 0),
            last_executed_at=script_data.get("last_executed_at"),
            cache_hit_count=script_data.get("cache_hit_count", 0),
            security_policy=script_data.get("security_policy"),
            llm_provider=script_data.get("llm_provider", "unknown"),
            fingerprint=script_data.get("fingerprint", ""),
            size_bytes=script_data.get("size_bytes", 0),
            metadata=script_data.get("metadata", {}),
        )

        return ShowResponse(
            script=script,
            code=script_data.get("code") if include_code else None,
            execution_logs=None,  # Would need to implement execution log storage
        )

    async def clear_cache(
        self,
        script_ids: list[str] | None = None,
        language: str | None = None,
        older_than: int | None = None,
        all_scripts: bool = False,
    ) -> ClearResponse:
        """Clear cache or specific scripts."""
        logger.info(
            "Clearing cache",
            script_ids=script_ids,
            language=language,
            all_scripts=all_scripts,
        )

        request = ClearRequest(
            script_ids=script_ids,
            language=language,
            older_than=older_than,
            all=all_scripts,
        )

        cleared_count = await self.cache_manager.clear_scripts(
            script_ids=request.script_ids,
            language=request.language,
            older_than=request.older_than,
            all_scripts=request.all,
        )

        return ClearResponse(
            cleared_count=cleared_count,
            cleared_script_ids=script_ids or [],
            total_size_freed_bytes=0,  # Would need to calculate
        )

    async def health_check(self) -> dict[str, Any]:
        """Check health of all components."""
        health_status: dict[str, Any] = {
            "overall": True,
            "components": {},
        }

        # Check cache manager
        try:
            cache_stats = self.cache_manager.get_cache_stats()
            health_status["components"]["cache"] = {
                "healthy": True,
                "stats": cache_stats,
            }
        except Exception as e:
            health_status["components"]["cache"] = {
                "healthy": False,
                "error": str(e),
            }
            health_status["overall"] = False

        # Check LLM providers
        try:
            provider_stats = self.fallback_manager.get_provider_stats()
            health_status["components"]["llm_providers"] = {
                "healthy": True,
                "stats": provider_stats,
            }
        except Exception as e:
            health_status["components"]["llm_providers"] = {
                "healthy": False,
                "error": str(e),
            }
            health_status["overall"] = False

        # Check container runner
        try:
            container_healthy = await self.container_runner.health_check()
            health_status["components"]["container_runner"] = {
                "healthy": container_healthy,
            }
        except Exception as e:
            health_status["components"]["container_runner"] = {
                "healthy": False,
                "error": str(e),
            }
            health_status["overall"] = False

        return health_status

    def get_stats(self) -> dict[str, Any]:
        """Get statistics for all components."""
        return {
            "cache": self.cache_manager.get_cache_stats(),
            "llm_providers": self.fallback_manager.get_provider_stats(),
            "script_generator": self.script_generator.get_generation_stats(),
        }
