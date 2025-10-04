"""Main Capibara engine for orchestrating script generation and execution."""

import asyncio
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from capibara.models.requests import RunRequest
from capibara.models.responses import RunResponse, ExecutionResult
from capibara.models.security import SecurityScanResult, AuditEvent
from capibara.core.prompt_processor import PromptProcessor
from capibara.core.script_generator import ScriptGenerator
from capibara.core.cache_manager import CacheManager
from capibara.security.ast_scanner import ASTScanner
from capibara.security.policy_manager import PolicyManager
from capibara.runner.container_runner import ContainerRunner
from capibara.llm_providers.fallback_manager import FallbackManager
from capibara.utils.logging import get_logger
from capibara.utils.fingerprinting import generate_fingerprint

logger = get_logger(__name__)


class CapibaraEngine:
    """Main engine for Capibara script generation and execution."""
    
    def __init__(
        self,
        cache_manager: CacheManager,
        script_generator: ScriptGenerator,
        ast_scanner: ASTScanner,
        policy_manager: PolicyManager,
        container_runner: ContainerRunner,
        fallback_manager: FallbackManager,
    ):
        self.cache_manager = cache_manager
        self.script_generator = script_generator
        self.ast_scanner = ast_scanner
        self.policy_manager = policy_manager
        self.container_runner = container_runner
        self.fallback_manager = fallback_manager
        self.prompt_processor = PromptProcessor()
    
    async def run_script(self, request: RunRequest) -> RunResponse:
        """Generate and optionally execute a script from a natural language prompt."""
        logger.info("Starting script generation", prompt_length=len(request.prompt))
        
        # Generate fingerprint for caching
        fingerprint = generate_fingerprint(
            prompt=request.prompt,
            language=request.language,
            context=request.context or {},
            security_policy=request.security_policy,
        )
        
        # Check cache first
        cached_script = await self.cache_manager.get_script(fingerprint)
        if cached_script:
            logger.info("Script served from cache", script_id=cached_script["script_id"])
            return await self._build_response_from_cache(cached_script, request)
        
        # Process prompt
        processed_prompt = await self.prompt_processor.process(request.prompt, request.context)
        
        # Generate script using LLM
        script_code = await self.script_generator.generate(
            prompt=processed_prompt,
            language=request.language,
            provider_name=request.llm_provider,
        )
        
        # Security scanning
        security_policy = self.policy_manager.get_policy(request.security_policy)
        scan_result = await self.ast_scanner.scan(
            code=script_code,
            language=request.language,
            policy=security_policy,
        )
        
        if not scan_result.passed:
            logger.warning("Security scan failed", violations=len(scan_result.violations))
            # Log security violations
            await self._log_security_violations(scan_result, request)
            raise SecurityError("Script failed security scan", violations=scan_result.violations)
        
        # Create script entry
        script_id = self._generate_script_id()
        script_info = {
            "script_id": script_id,
            "prompt": request.prompt,
            "language": request.language,
            "code": script_code,
            "fingerprint": fingerprint,
            "security_policy": request.security_policy,
            "llm_provider": self.script_generator.last_provider_used,
            "created_at": datetime.utcnow(),
            "metadata": {
                "context": request.context,
                "processed_prompt": processed_prompt,
                "scan_result": scan_result.dict(),
            }
        }
        
        # Cache the script
        await self.cache_manager.store_script(script_info)
        
        # Execute if requested
        execution_result = None
        if hasattr(request, 'execute') and request.execute:
            execution_result = await self._execute_script(script_code, request)
        
        # Build response
        response = RunResponse(
            script_id=script_id,
            prompt=request.prompt,
            language=request.language,
            code=script_code,
            execution_result=execution_result,
            cached=False,
            security_policy=request.security_policy,
            llm_provider=self.script_generator.last_provider_used,
            fingerprint=fingerprint,
            created_at=datetime.utcnow(),
            metadata=script_info["metadata"],
        )
        
        # Log audit event
        await self._log_audit_event("script_generated", script_id, request)
        
        logger.info("Script generated successfully", script_id=script_id)
        return response
    
    async def _build_response_from_cache(self, cached_script: Dict[str, Any], request: RunRequest) -> RunResponse:
        """Build response from cached script."""
        # Update cache hit count
        await self.cache_manager.increment_cache_hit(cached_script["script_id"])
        
        # Execute if requested
        execution_result = None
        if hasattr(request, 'execute') and request.execute:
            execution_result = await self._execute_script(cached_script["code"], request)
        
        return RunResponse(
            script_id=cached_script["script_id"],
            prompt=cached_script["prompt"],
            language=cached_script["language"],
            code=cached_script["code"],
            execution_result=execution_result,
            cached=True,
            cache_hit_count=cached_script.get("cache_hit_count", 0) + 1,
            security_policy=cached_script.get("security_policy"),
            llm_provider=cached_script["llm_provider"],
            fingerprint=cached_script["fingerprint"],
            created_at=cached_script["created_at"],
            metadata=cached_script.get("metadata", {}),
        )
    
    async def _execute_script(self, code: str, request: RunRequest) -> ExecutionResult:
        """Execute script in sandboxed container."""
        logger.info("Executing script in sandbox")
        
        # Modify code to use actual inputs if provided
        modified_code = self._modify_code_for_execution(code, request)
        
        # Get security policy
        policy = self.policy_manager.get_policy(request.security_policy)
        
        # Execute in container
        result = await self.container_runner.execute(
            code=modified_code,
            language=request.language,
            resource_limits=policy.resource_limits,
            security_policy=policy,
        )
        
        # Log execution
        await self._log_audit_event("script_executed", None, request, execution_result=result)
        
        return result
    
    async def _log_security_violations(self, scan_result: SecurityScanResult, request: RunRequest) -> None:
        """Log security violations for audit."""
        for violation in scan_result.violations:
            await self._log_audit_event(
                "security_violation",
                None,
                request,
                violation=violation,
            )
    
    async def _log_audit_event(
        self,
        event_type: str,
        script_id: Optional[str],
        request: RunRequest,
        **kwargs: Any
    ) -> None:
        """Log audit event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            script_id=script_id,
            message=f"Event: {event_type}",
            details=kwargs,
        )
        # This would be sent to audit logging system
        logger.info("Audit event", **event.dict())
    
    def _generate_script_id(self) -> str:
        """Generate unique script ID."""
        return f"script_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5().hexdigest()[:8]}"
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        return f"event_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5().hexdigest()[:8]}"
    
    def _modify_code_for_execution(self, code: str, request: RunRequest) -> str:
        """Modify generated code to use actual inputs instead of hardcoded values."""
        if not request.context or 'inputs' not in request.context:
            return code
        
        inputs = request.context['inputs']
        if not isinstance(inputs, list) or len(inputs) == 0:
            return code
        
        # For Python scripts, try to replace hardcoded values in main function
        if request.language.lower() == "python":
            return self._modify_python_code(code, inputs)
        
        return code
    
    def _modify_python_code(self, code: str, inputs: List[Any]) -> str:
        """Modify Python code to use actual inputs."""
        import re
        
        # Convert inputs to appropriate Python literals
        python_inputs = []
        for input_val in inputs:
            if isinstance(input_val, str):
                # Try to convert to number if possible
                try:
                    if '.' in input_val:
                        python_inputs.append(str(float(input_val)))
                    else:
                        python_inputs.append(str(int(input_val)))
                except ValueError:
                    python_inputs.append(f'"{input_val}"')
            elif isinstance(input_val, bool):
                python_inputs.append(str(input_val))
            else:
                python_inputs.append(str(input_val))
        
        # Look for patterns like (1.0, 2.0, 3.0) or [1.0, 2.0, 3.0] in main function
        # and replace with actual inputs
        input_patterns = [
            r'\(\s*\d+\.?\d*\s*,\s*\d+\.?\d*\s*,\s*\d+\.?\d*\s*\)',  # (1.0, 2.0, 3.0)
            r'\[\s*\d+\.?\d*\s*,\s*\d+\.?\d*\s*,\s*\d+\.?\d*\s*\]',  # [1.0, 2.0, 3.0]
            r'\(\s*\d+\.?\d*\s*,\s*\d+\.?\d*\s*\)',  # (1.0, 2.0)
            r'\[\s*\d+\.?\d*\s*,\s*\d+\.?\d*\s*\]',  # [1.0, 2.0]
        ]
        
        modified_code = code
        for pattern in input_patterns:
            matches = re.findall(pattern, modified_code)
            for match in matches:
                if len(python_inputs) >= 2:  # Only replace if we have enough inputs
                    if len(python_inputs) >= 3:
                        replacement = f"({', '.join(python_inputs[:3])})"
                    else:
                        replacement = f"({', '.join(python_inputs)})"
                    modified_code = modified_code.replace(match, replacement, 1)
                    break
        
        # Also try to replace individual number literals in function calls
        # Look for patterns like function_name(1.0, 2.0, 3.0)
        function_call_pattern = r'(\w+)\s*\(\s*\d+\.?\d*\s*,\s*\d+\.?\d*\s*,\s*\d+\.?\d*\s*\)'
        matches = re.findall(function_call_pattern, modified_code)
        for func_name in matches:
            if len(python_inputs) >= 3:
                replacement = f"{func_name}({', '.join(python_inputs[:3])})"
                # Replace the first occurrence of this pattern
                pattern_to_replace = f"{func_name}(\\s*\\d+\\.?\\d*\\s*,\\s*\\d+\\.?\\d*\\s*,\\s*\\d+\\.?\\d*\\s*)"
                modified_code = re.sub(pattern_to_replace, replacement, modified_code, count=1)
        
        return modified_code


class SecurityError(Exception):
    """Raised when security scan fails."""
    
    def __init__(self, message: str, violations: List[Any]):
        super().__init__(message)
        self.violations = violations
