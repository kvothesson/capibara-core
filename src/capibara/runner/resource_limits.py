"""Resource limits management for container execution."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ResourceLimits(BaseModel):
    """Resource limits for container execution."""
    
    cpu_time_seconds: int = Field(30, ge=1, le=300, description="Maximum CPU time in seconds")
    memory_mb: int = Field(512, ge=64, le=2048, description="Maximum memory in MB")
    execution_time_seconds: int = Field(60, ge=1, le=600, description="Maximum wall clock time in seconds")
    max_file_size_mb: int = Field(10, ge=1, le=100, description="Maximum file size for I/O operations")
    max_files: int = Field(100, ge=1, le=1000, description="Maximum number of files that can be created")
    network_access: bool = Field(False, description="Whether network access is allowed")
    allow_subprocess: bool = Field(False, description="Whether subprocess execution is allowed")
    
    def to_docker_limits(self) -> Dict[str, Any]:
        """Convert to Docker resource limits format."""
        return {
            "mem_limit": f"{self.memory_mb}m",
            "memswap_limit": f"{self.memory_mb}m",
            "cpu_period": 100000,
            "cpu_quota": int(self.cpu_time_seconds * 100000),
        }
    
    def to_podman_limits(self) -> Dict[str, Any]:
        """Convert to Podman resource limits format."""
        return {
            "memory": self.memory_mb * 1024 * 1024,  # Convert to bytes
            "cpus": self.cpu_time_seconds,
        }
    
    def validate_usage(self, memory_used_mb: float, cpu_time_ms: int) -> Dict[str, bool]:
        """Validate if current usage is within limits."""
        return {
            "memory_ok": memory_used_mb <= self.memory_mb,
            "cpu_ok": cpu_time_ms <= self.cpu_time_seconds * 1000,
            "execution_ok": True,  # Would need to track execution time
        }
    
    def get_violations(self, memory_used_mb: float, cpu_time_ms: int) -> list[str]:
        """Get list of resource limit violations."""
        violations = []
        
        if memory_used_mb > self.memory_mb:
            violations.append(f"Memory limit exceeded: {memory_used_mb:.1f}MB > {self.memory_mb}MB")
        
        if cpu_time_ms > self.cpu_time_seconds * 1000:
            violations.append(f"CPU time limit exceeded: {cpu_time_ms}ms > {self.cpu_time_seconds * 1000}ms")
        
        return violations
