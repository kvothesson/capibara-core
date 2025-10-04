"""Main SDK client for Capibara Core."""

from typing import Any, Dict, List, Optional

from capibara.models.requests import RunRequest, ListRequest, ShowRequest, ClearRequest
from capibara.models.responses import RunResponse, ListResponse, ShowResponse, ClearResponse
from capibara.core.engine import CapibaraEngine
from capibara.core.cache_manager import CacheManager
from capibara.core.script_generator import ScriptGenerator
from capibara.security.ast_scanner import ASTScanner
from capibara.security.policy_manager import PolicyManager
from capibara.runner.container_runner import ContainerRunner
from capibara.llm_providers.fallback_manager import FallbackManager
from capibara.llm_providers.openai_provider import OpenAIProvider
from capibara.llm_providers.groq_provider import GroqProvider
from capibara.llm_providers.base import LLMProviderConfig
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class CapibaraClient:
    """Main client for interacting with Capibara Core."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
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
        openai_api_key: Optional[str],
        groq_api_key: Optional[str],
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
        providers = []
        
        if openai_api_key:
            openai_config = LLMProviderConfig(
                name="openai",
                api_key=openai_api_key,
                model="gpt-3.5-turbo",
            )
            providers.append(OpenAIProvider(openai_config))
        
        if groq_api_key:
            groq_config = LLMProviderConfig(
                name="groq",
                api_key=groq_api_key,
                model="llama2-70b-4096",
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
        context: Optional[Dict[str, Any]] = None,
        security_policy: Optional[str] = None,
        llm_provider: Optional[str] = None,
        execute: bool = False,
        **kwargs: Any
    ) -> RunResponse:
        """Generate and optionally execute a script from a natural language prompt."""
        logger.info("Running script generation", prompt_length=len(prompt))
        
        request = RunRequest(
            prompt=prompt,
            context=context,
            language=language,
            security_policy=security_policy,
            llm_provider=llm_provider,
            **kwargs
        )
        
        # Add execute flag to request
        request_dict = request.dict()
        request_dict["execute"] = execute
        
        # Create new request with execute flag
        request = RunRequest(**request_dict)
        
        return await self.engine.run_script(request)
    
    async def list_scripts(
        self,
        limit: int = 50,
        offset: int = 0,
        language: Optional[str] = None,
        search: Optional[str] = None,
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
        
        scripts = await self.cache_manager.list_scripts(
            limit=request.limit,
            offset=request.offset,
            language=request.language,
            search=request.search,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
        )
        
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
        
        request = ShowRequest(
            script_id=script_id,
            include_code=include_code,
            include_execution_logs=include_execution_logs,
        )
        
        # Get script from cache
        script = await self.cache_manager.get_script(script_id)
        if not script:
            raise ValueError(f"Script not found: {script_id}")
        
        return ShowResponse(
            script=script,
            code=script.get("code") if include_code else None,
            execution_logs=None,  # Would need to implement execution log storage
        )
    
    async def clear_cache(
        self,
        script_ids: Optional[List[str]] = None,
        language: Optional[str] = None,
        older_than: Optional[int] = None,
        all_scripts: bool = False,
    ) -> ClearResponse:
        """Clear cache or specific scripts."""
        logger.info("Clearing cache", 
                   script_ids=script_ids,
                   language=language,
                   all_scripts=all_scripts)
        
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
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all components."""
        health_status = {
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all components."""
        return {
            "cache": self.cache_manager.get_cache_stats(),
            "llm_providers": self.fallback_manager.get_provider_stats(),
            "script_generator": self.script_generator.get_generation_stats(),
        }
