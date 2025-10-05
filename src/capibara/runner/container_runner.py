"""Container-based script execution with security controls."""

import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import docker
from docker.errors import DockerException

from capibara.models.manifests import SecurityPolicy, ResourceLimits
from capibara.models.responses import ExecutionResult
from capibara.models.security import SandboxConfig
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class ContainerRunner:
    """Executes scripts in secure containers with resource limits."""
    
    def __init__(self, docker_client: Optional[docker.DockerClient] = None):
        self.docker_client = docker_client or docker.from_env()
        self.active_containers: Dict[str, str] = {}  # script_id -> container_id
    
    async def execute(
        self,
        code: str,
        language: str,
        resource_limits: ResourceLimits,
        security_policy: Optional[SecurityPolicy] = None,
        **kwargs: Any
    ) -> ExecutionResult:
        """Execute script in a secure container."""
        logger.info("Starting container execution", language=language)
        
        container_id = None
        try:
            # Create temporary workspace
            workspace = await self._create_workspace(code, language)
            
            # Create container
            container_id = await self._create_container(
                workspace=workspace,
                language=language,
                resource_limits=resource_limits,
                security_policy=security_policy,
            )
            
            # Execute script
            result = await self._execute_in_container(
                container_id=container_id,
                language=language,
                resource_limits=resource_limits,
            )
            
            # Clean up
            await self._cleanup_container(container_id)
            await self._cleanup_workspace(workspace)
            
            logger.info("Container execution completed", 
                       success=result.success,
                       exit_code=result.exit_code)
            
            return result
            
        except Exception as e:
            logger.error("Container execution failed", error=str(e))
            
            # Clean up on error
            if container_id:
                await self._cleanup_container(container_id)
            
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Execution failed: {str(e)}",
                execution_time_ms=0,
                memory_used_mb=0.0,
                cpu_time_ms=0,
                security_violations=[],
                resource_limits_exceeded=[],
            )
    
    async def _create_workspace(self, code: str, language: str) -> Path:
        """Create temporary workspace with script file."""
        workspace = Path(tempfile.mkdtemp(prefix="capibara_"))
        
        # Create script file based on language
        if language.lower() == "python":
            script_file = workspace / "script.py"
        elif language.lower() == "javascript":
            script_file = workspace / "script.js"
        elif language.lower() in ["bash", "sh"]:
            script_file = workspace / "script.sh"
        elif language.lower() == "powershell":
            script_file = workspace / "script.ps1"
        else:
            script_file = workspace / "script"
        
        # Write script to file
        script_file.write_text(code)
        
        # Make executable if needed
        if language.lower() in ["bash", "sh"]:
            script_file.chmod(0o755)
        
        logger.debug("Workspace created", workspace=str(workspace), script_file=str(script_file))
        return workspace
    
    async def _create_container(
        self,
        workspace: Path,
        language: str,
        resource_limits: ResourceLimits,
        security_policy: Optional[SecurityPolicy] = None,
    ) -> str:
        """Create and start container for script execution."""
        # Determine base image
        if language.lower() == "python":
            image = "python:3.11-slim"
        elif language.lower() == "javascript":
            image = "node:18-slim"
        elif language.lower() in ["bash", "sh"]:
            image = "alpine:latest"
        elif language.lower() == "powershell":
            image = "mcr.microsoft.com/powershell:latest"
        else:
            image = "alpine:latest"
        
        # Create container configuration
        container_config = {
            "image": image,
            "working_dir": "/workspace",
            "user": "nobody",
            "environment": {
                "PYTHONUNBUFFERED": "1",
            },
            "volumes": [f"{workspace}:/workspace:ro"],
            "security_opt": [
                "no-new-privileges:true",
            ],
            "cap_drop": ["ALL"],
            "network_mode": "none",
            "read_only": True,
            "mem_limit": f"{resource_limits.memory_mb}m",
            "memswap_limit": f"{resource_limits.memory_mb}m",
            "cpu_period": 100000,
            "cpu_quota": int(resource_limits.cpu_time_seconds * 100000),
        }
        
        # Add seccomp profile if available (skip for now to avoid errors)
        # seccomp_profile = self._get_seccomp_profile(security_policy)
        # if seccomp_profile:
        #     container_config["security_opt"].append(f"seccomp={seccomp_profile}")
        
        # Create and start container
        container = self.docker_client.containers.create(
            **container_config,
            command=self._get_execution_command(language),
        )
        
        container.start()
        
        logger.debug("Container created and started", 
                    container_id=container.id,
                    image=image)
        
        return container.id
    
    async def _execute_in_container(
        self,
        container_id: str,
        language: str,
        resource_limits: ResourceLimits,
    ) -> ExecutionResult:
        """Execute script in the container and collect results."""
        container = self.docker_client.containers.get(container_id)
        
        # Wait for execution to complete
        try:
            result = container.wait(timeout=resource_limits.execution_time_seconds)
            exit_code = result["StatusCode"]
        except Exception as e:
            logger.warning("Container execution timed out", container_id=container_id, error=str(e))
            container.kill()
            exit_code = 124  # Timeout exit code
        
        # Get logs
        logs = container.logs(stdout=True, stderr=True)
        stdout, stderr = self._parse_logs(logs)
        
        # Get resource usage (simplified)
        try:
            stats = container.stats(stream=False)
            memory_used_mb = stats.get("memory_stats", {}).get("usage", 0) / (1024 * 1024)
            cpu_time_ms = self._calculate_cpu_time(stats)
        except Exception as e:
            logger.warning("Failed to get container stats", error=str(e))
            memory_used_mb = 0.0
            cpu_time_ms = 0
        
        # Check for resource limit violations
        resource_violations = self._check_resource_limits(
            memory_used_mb, cpu_time_ms, resource_limits
        )
        
        success = exit_code == 0 and len(resource_violations) == 0
        
        return ExecutionResult(
            success=success,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            execution_time_ms=0,  # Would need to track start time
            memory_used_mb=memory_used_mb,
            cpu_time_ms=cpu_time_ms,
            security_violations=[],
            resource_limits_exceeded=resource_violations,
        )
    
    def _get_execution_command(self, language: str) -> List[str]:
        """Get execution command for the language."""
        if language.lower() == "python":
            return ["python", "/workspace/script.py"]
        elif language.lower() == "javascript":
            return ["node", "/workspace/script.js"]
        elif language.lower() in ["bash", "sh"]:
            return ["/bin/sh", "/workspace/script.sh"]
        elif language.lower() == "powershell":
            return ["pwsh", "/workspace/script.ps1"]
        else:
            return ["/bin/sh", "/workspace/script"]
    
    def _get_seccomp_profile(self, security_policy: Optional[SecurityPolicy]) -> Optional[str]:
        """Get seccomp profile path for security policy."""
        if not security_policy:
            return None
        
        # Map security policy to seccomp profile
        profile_mapping = {
            "strict": "strict.json",
            "moderate": "moderate.json", 
            "permissive": "permissive.json",
        }
        
        return profile_mapping.get(security_policy.name)
    
    def _parse_logs(self, logs: bytes) -> tuple[str, str]:
        """Parse container logs into stdout and stderr."""
        log_text = logs.decode('utf-8', errors='replace')
        
        # Simple parsing - in practice, you'd need more sophisticated log parsing
        lines = log_text.split('\n')
        stdout_lines = []
        stderr_lines = []
        
        for line in lines:
            if line.startswith('STDERR:'):
                stderr_lines.append(line[7:])  # Remove 'STDERR:' prefix
            else:
                stdout_lines.append(line)
        
        return '\n'.join(stdout_lines), '\n'.join(stderr_lines)
    
    def _calculate_cpu_time(self, stats: Dict[str, Any]) -> int:
        """Calculate CPU time from container stats."""
        try:
            cpu_stats = stats["cpu_stats"]
            precpu_stats = stats["precpu_stats"]
            
            cpu_delta = cpu_stats["cpu_usage"]["total_usage"] - precpu_stats["cpu_usage"]["total_usage"]
            system_delta = cpu_stats["system_cpu_usage"] - precpu_stats["system_cpu_usage"]
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(cpu_stats["cpu_usage"]["percpu_usage"])
                return int(cpu_percent * 1000)  # Convert to milliseconds
            
        except (KeyError, ZeroDivisionError):
            pass
        
        return 0
    
    def _check_resource_limits(
        self,
        memory_used_mb: float,
        cpu_time_ms: int,
        resource_limits: ResourceLimits,
    ) -> List[str]:
        """Check if resource limits were exceeded."""
        violations = []
        
        if memory_used_mb > resource_limits.memory_mb:
            violations.append(f"Memory limit exceeded: {memory_used_mb:.1f}MB > {resource_limits.memory_mb}MB")
        
        if cpu_time_ms > resource_limits.cpu_time_seconds * 1000:
            violations.append(f"CPU time limit exceeded: {cpu_time_ms}ms > {resource_limits.cpu_time_seconds * 1000}ms")
        
        return violations
    
    async def _cleanup_container(self, container_id: str) -> None:
        """Clean up container after execution."""
        try:
            container = self.docker_client.containers.get(container_id)
            container.remove(force=True)
            logger.debug("Container cleaned up", container_id=container_id)
        except DockerException as e:
            logger.warning("Failed to clean up container", 
                          container_id=container_id, error=str(e))
    
    async def _cleanup_workspace(self, workspace: Path) -> None:
        """Clean up temporary workspace."""
        try:
            import shutil
            shutil.rmtree(workspace)
            logger.debug("Workspace cleaned up", workspace=str(workspace))
        except Exception as e:
            logger.warning("Failed to clean up workspace", 
                          workspace=str(workspace), error=str(e))
    
    async def health_check(self) -> bool:
        """Check if container runtime is healthy."""
        try:
            self.docker_client.ping()
            return True
        except Exception as e:
            logger.warning("Container runtime health check failed", error=str(e))
            return False
    
    def _parse_memory_usage(self, stats: Dict[str, Any]) -> float:
        """Parse memory usage from container stats."""
        try:
            # Docker stats format
            if "memory_stats" in stats:
                memory_stats = stats["memory_stats"]
                if "usage" in memory_stats:
                    return memory_stats["usage"] / (1024 * 1024)  # Convert bytes to MB
            
            # Alternative format
            if "memory" in stats:
                return stats["memory"] / (1024 * 1024)
            
            return 0.0
        except (KeyError, TypeError, ZeroDivisionError):
            return 0.0
    
    def _parse_cpu_usage(self, stats: Dict[str, Any]) -> int:
        """Parse CPU usage from container stats."""
        try:
            # Docker stats format
            if "cpu_stats" in stats:
                cpu_stats = stats["cpu_stats"]
                if "cpu_usage" in cpu_stats:
                    cpu_usage = cpu_stats["cpu_usage"]
                    if "total_usage" in cpu_usage:
                        return int(cpu_usage["total_usage"] / 1_000_000)  # Convert nanoseconds to milliseconds
            
            # Alternative format
            if "cpu" in stats:
                return int(stats["cpu"])
            
            return 0
        except (KeyError, TypeError, ValueError):
            return 0