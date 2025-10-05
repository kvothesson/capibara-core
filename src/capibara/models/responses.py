"""Response models for Capibara Core."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScriptInfo(BaseModel):
    """Information about a cached script."""
    
    script_id: str = Field(..., description="Unique identifier")
    prompt: str = Field(..., description="Original prompt")
    language: str = Field(..., description="Programming language")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    execution_count: int = Field(0, description="Number of times executed")
    last_executed_at: Optional[datetime] = Field(None, description="Last execution timestamp")
    cache_hit_count: int = Field(0, description="Number of cache hits")
    security_policy: Optional[str] = Field(None, description="Applied security policy")
    llm_provider: str = Field(..., description="LLM provider used")
    fingerprint: str = Field(..., description="Content fingerprint (SHA-256)")
    size_bytes: int = Field(..., description="Script size in bytes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ExecutionResult(BaseModel):
    """Result of script execution."""
    
    success: bool = Field(..., description="Whether execution was successful")
    exit_code: int = Field(..., description="Process exit code")
    stdout: str = Field("", description="Standard output")
    stderr: str = Field("", description="Standard error")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    memory_used_mb: float = Field(0.0, description="Peak memory usage in MB")
    cpu_time_ms: int = Field(0, description="CPU time in milliseconds")
    security_violations: List[str] = Field(default_factory=list, description="Security violations detected")
    resource_limits_exceeded: List[str] = Field(default_factory=list, description="Resource limits exceeded")


class RunResponse(BaseModel):
    """Response from running a script."""
    
    script_id: str = Field(..., description="Unique identifier of the generated script")
    prompt: str = Field(..., description="Original prompt")
    language: str = Field(..., description="Programming language")
    code: str = Field(..., description="Generated script code")
    execution_result: Optional[ExecutionResult] = Field(None, description="Execution result if executed")
    cached: bool = Field(False, description="Whether this was served from cache")
    cache_hit_count: int = Field(0, description="Number of cache hits for this script")
    security_policy: Optional[str] = Field(None, description="Applied security policy")
    llm_provider: str = Field(..., description="LLM provider used")
    fingerprint: str = Field(..., description="Content fingerprint (SHA-256)")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ListResponse(BaseModel):
    """Response from listing scripts."""
    
    scripts: List[ScriptInfo] = Field(..., description="List of scripts")
    total_count: int = Field(..., description="Total number of scripts matching criteria")
    limit: int = Field(..., description="Requested limit")
    offset: int = Field(..., description="Requested offset")
    has_more: bool = Field(..., description="Whether there are more results")


class ShowResponse(BaseModel):
    """Response from showing script details."""
    
    script: ScriptInfo = Field(..., description="Script information")
    code: Optional[str] = Field(None, description="Generated code if requested")
    execution_logs: Optional[List[Dict[str, Any]]] = Field(None, description="Execution logs if requested")


class ClearResponse(BaseModel):
    """Response from clearing cache."""
    
    cleared_count: int = Field(..., description="Number of scripts cleared")
    cleared_script_ids: List[str] = Field(..., description="IDs of cleared scripts")
    total_size_freed_bytes: int = Field(0, description="Total size freed in bytes")


class ErrorResponse(BaseModel):
    """Error response."""
    
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Error timestamp")
