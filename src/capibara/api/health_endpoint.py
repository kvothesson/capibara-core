"""Health check endpoint for Capibara Core."""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

from capibara.utils.logging import get_logger
from capibara.utils.config import get_config

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class HealthCheck:
    """Base class for health checks."""
    
    def __init__(self, name: str, critical: bool = False):
        self.name = name
        self.critical = critical
        self.last_check: Optional[datetime] = None
        self.last_status: HealthStatus = HealthStatus.UNKNOWN
        self.last_error: Optional[str] = None
        self.check_duration_ms: Optional[float] = None
    
    async def check(self) -> Dict[str, Any]:
        """Perform the health check."""
        start_time = time.time()
        
        try:
            result = await self._perform_check()
            self.last_status = HealthStatus.HEALTHY
            self.last_error = None
        except Exception as e:
            self.last_status = HealthStatus.UNHEALTHY if self.critical else HealthStatus.DEGRADED
            self.last_error = str(e)
            result = {
                "status": self.last_status.value,
                "error": str(e)
            }
        
        self.last_check = datetime.utcnow()
        self.check_duration_ms = (time.time() - start_time) * 1000
        
        return {
            "name": self.name,
            "status": self.last_status.value,
            "critical": self.critical,
            "last_check": self.last_check.isoformat(),
            "duration_ms": self.check_duration_ms,
            **result
        }
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Override this method to implement the actual health check."""
        return {"status": "healthy"}


class DatabaseHealthCheck(HealthCheck):
    """Database connectivity health check."""
    
    def __init__(self):
        super().__init__("database", critical=True)
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check database connectivity."""
        # This would be implemented with actual database connection
        # For now, we'll simulate a check
        await asyncio.sleep(0.01)  # Simulate DB query
        
        return {
            "status": "healthy",
            "connection_pool_size": 10,
            "active_connections": 2,
            "database_url": "sqlite:///capibara.db"
        }


class CacheHealthCheck(HealthCheck):
    """Cache system health check."""
    
    def __init__(self):
        super().__init__("cache", critical=False)
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check cache system health."""
        # Simulate cache check
        await asyncio.sleep(0.005)
        
        return {
            "status": "healthy",
            "cache_dir": "~/.capibara/cache",
            "total_scripts": 42,
            "cache_size_mb": 15.6,
            "hit_rate_percent": 85.2
        }


class LLMProvidersHealthCheck(HealthCheck):
    """LLM providers health check."""
    
    def __init__(self):
        super().__init__("llm_providers", critical=True)
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check LLM providers health."""
        config = get_config()
        
        providers_status = {}
        
        # Check OpenAI
        if config.llm.openai_api_key:
            providers_status["openai"] = await self._check_openai()
        else:
            providers_status["openai"] = {"status": "not_configured"}
        
        # Check Groq
        if config.llm.groq_api_key:
            providers_status["groq"] = await self._check_groq()
        else:
            providers_status["groq"] = {"status": "not_configured"}
        
        # Determine overall status
        healthy_providers = sum(1 for p in providers_status.values() 
                              if p.get("status") == "healthy")
        total_providers = len([p for p in providers_status.values() 
                             if p.get("status") != "not_configured"])
        
        if healthy_providers == 0 and total_providers > 0:
            overall_status = "unhealthy"
        elif healthy_providers < total_providers:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "providers": providers_status,
            "healthy_providers": healthy_providers,
            "total_providers": total_providers
        }
    
    async def _check_openai(self) -> Dict[str, Any]:
        """Check OpenAI provider health."""
        try:
            # Simulate OpenAI API check
            await asyncio.sleep(0.1)
            return {
                "status": "healthy",
                "model": "gpt-3.5-turbo",
                "response_time_ms": 150
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_groq(self) -> Dict[str, Any]:
        """Check Groq provider health."""
        try:
            # Simulate Groq API check
            await asyncio.sleep(0.08)
            return {
                "status": "healthy",
                "model": "llama-3.3-70b-versatile",
                "response_time_ms": 120
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class ContainerRuntimeHealthCheck(HealthCheck):
    """Container runtime health check."""
    
    def __init__(self):
        super().__init__("container_runtime", critical=True)
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check container runtime health."""
        try:
            import docker
            client = docker.from_env()
            client.ping()
            
            # Get Docker info
            info = client.info()
            
            return {
                "status": "healthy",
                "docker_version": info.get("ServerVersion", "unknown"),
                "containers_running": info.get("ContainersRunning", 0),
                "containers_total": info.get("Containers", 0),
                "images_count": info.get("Images", 0)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class DiskSpaceHealthCheck(HealthCheck):
    """Disk space health check."""
    
    def __init__(self):
        super().__init__("disk_space", critical=False)
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check disk space availability."""
        import shutil
        
        config = get_config()
        cache_dir = config.cache.dir
        
        try:
            # Get disk usage for cache directory
            total, used, free = shutil.disk_usage(cache_dir)
            
            free_gb = free / (1024**3)
            used_percent = (used / total) * 100
            
            status = "healthy"
            if used_percent > 90:
                status = "unhealthy"
            elif used_percent > 80:
                status = "degraded"
            
            return {
                "status": status,
                "free_space_gb": round(free_gb, 2),
                "used_percent": round(used_percent, 1),
                "total_space_gb": round(total / (1024**3), 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class MemoryHealthCheck(HealthCheck):
    """Memory usage health check."""
    
    def __init__(self):
        super().__init__("memory", critical=False)
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            memory_percent = memory.percent
            swap_percent = swap.percent
            
            status = "healthy"
            if memory_percent > 90 or swap_percent > 90:
                status = "unhealthy"
            elif memory_percent > 80 or swap_percent > 80:
                status = "degraded"
            
            return {
                "status": status,
                "memory_percent": memory_percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "swap_percent": swap_percent,
                "swap_total_gb": round(swap.total / (1024**3), 2)
            }
        except ImportError:
            return {
                "status": "unknown",
                "error": "psutil not available"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class SecurityPoliciesHealthCheck(HealthCheck):
    """Security policies health check."""
    
    def __init__(self):
        super().__init__("security_policies", critical=False)
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check security policies availability."""
        config = get_config()
        policies_dir = config.security.policies_dir
        
        try:
            from pathlib import Path
            
            policies_path = Path(policies_dir).expanduser()
            
            if not policies_path.exists():
                return {
                    "status": "degraded",
                    "error": "Policies directory does not exist",
                    "policies_dir": policies_dir
                }
            
            # Count policy files
            policy_files = list(policies_path.glob("*.yaml")) + list(policies_path.glob("*.yml"))
            
            return {
                "status": "healthy",
                "policies_dir": policies_dir,
                "policy_files_count": len(policy_files),
                "default_policy": config.security.default_policy
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class HealthChecker:
    """Main health checker that manages all health checks."""
    
    def __init__(self):
        self.checks: List[HealthCheck] = [
            DatabaseHealthCheck(),
            CacheHealthCheck(),
            LLMProvidersHealthCheck(),
            ContainerRuntimeHealthCheck(),
            DiskSpaceHealthCheck(),
            MemoryHealthCheck(),
            SecurityPoliciesHealthCheck(),
        ]
        self.last_overall_check: Optional[datetime] = None
        self.overall_status: HealthStatus = HealthStatus.UNKNOWN
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status."""
        logger.debug("Running comprehensive health check")
        
        start_time = time.time()
        
        # Run all checks concurrently
        check_tasks = [check.check() for check in self.checks]
        check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results
        results = []
        critical_failures = 0
        total_checks = len(self.checks)
        
        for i, result in enumerate(check_results):
            if isinstance(result, Exception):
                check = self.checks[i]
                result = {
                    "name": check.name,
                    "status": "unhealthy",
                    "critical": check.critical,
                    "error": str(result)
                }
            
            results.append(result)
            
            if result.get("status") == "unhealthy" and result.get("critical"):
                critical_failures += 1
        
        # Determine overall status
        if critical_failures > 0:
            self.overall_status = HealthStatus.UNHEALTHY
        elif any(r.get("status") == "degraded" for r in results):
            self.overall_status = HealthStatus.DEGRADED
        else:
            self.overall_status = HealthStatus.HEALTHY
        
        self.last_overall_check = datetime.utcnow()
        total_duration_ms = (time.time() - start_time) * 1000
        
        return {
            "overall_status": self.overall_status.value,
            "timestamp": self.last_overall_check.isoformat(),
            "duration_ms": total_duration_ms,
            "checks": results,
            "summary": {
                "total_checks": total_checks,
                "healthy": len([r for r in results if r.get("status") == "healthy"]),
                "degraded": len([r for r in results if r.get("status") == "degraded"]),
                "unhealthy": len([r for r in results if r.get("status") == "unhealthy"]),
                "critical_failures": critical_failures
            }
        }
    
    async def check_quick(self) -> Dict[str, Any]:
        """Run a quick health check (only critical components)."""
        logger.debug("Running quick health check")
        
        critical_checks = [check for check in self.checks if check.critical]
        check_tasks = [check.check() for check in critical_checks]
        check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results
        results = []
        any_failures = False
        
        for i, result in enumerate(check_results):
            if isinstance(result, Exception):
                check = critical_checks[i]
                result = {
                    "name": check.name,
                    "status": "unhealthy",
                    "error": str(result)
                }
                any_failures = True
            
            results.append(result)
            
            if result.get("status") != "healthy":
                any_failures = True
        
        overall_status = "healthy" if not any_failures else "unhealthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results
        }
    
    def get_last_status(self) -> Dict[str, Any]:
        """Get the last health check status without running new checks."""
        if not self.last_overall_check:
            return {
                "overall_status": "unknown",
                "timestamp": None,
                "message": "No health checks have been run yet"
            }
        
        # Check if last check is recent (within 5 minutes)
        time_since_last = datetime.utcnow() - self.last_overall_check
        if time_since_last > timedelta(minutes=5):
            return {
                "overall_status": "unknown",
                "timestamp": self.last_overall_check.isoformat(),
                "message": "Health check data is stale"
            }
        
        return {
            "overall_status": self.overall_status.value,
            "timestamp": self.last_overall_check.isoformat(),
            "message": "Using cached health status"
        }


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


async def health_check(quick: bool = False) -> Dict[str, Any]:
    """Perform health check."""
    checker = get_health_checker()
    
    if quick:
        return await checker.check_quick()
    else:
        return await checker.check_all()


async def health_status() -> Dict[str, Any]:
    """Get current health status."""
    checker = get_health_checker()
    return checker.get_last_status()
