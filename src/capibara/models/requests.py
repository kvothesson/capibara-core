"""Request models for Capibara Core."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class RunRequest(BaseModel):
    """Request to run a script from a natural language prompt."""
    
    prompt: str = Field(..., description="Natural language prompt describing the desired script")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for script generation")
    language: str = Field("python", description="Target programming language")
    security_policy: Optional[str] = Field(None, description="Security policy to apply")
    llm_provider: Optional[str] = Field(None, description="Specific LLM provider to use")
    cache_ttl: Optional[int] = Field(3600, description="Cache TTL in seconds")
    resource_limits: Optional[Dict[str, Any]] = Field(None, description="Custom resource limits")
    execute: bool = Field(False, description="Whether to execute the generated script")
    
    @field_validator('prompt')
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        supported_languages = {'python', 'javascript', 'bash', 'powershell'}
        if v.lower() not in supported_languages:
            raise ValueError(f"Unsupported language: {v}. Supported: {supported_languages}")
        return v.lower()


class ListRequest(BaseModel):
    """Request to list cached scripts."""
    
    limit: int = Field(50, ge=1, le=1000, description="Maximum number of scripts to return")
    offset: int = Field(0, ge=0, description="Number of scripts to skip")
    language: Optional[str] = Field(None, description="Filter by programming language")
    search: Optional[str] = Field(None, description="Search in prompts and generated code")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    
    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        valid_fields = {'created_at', 'updated_at', 'execution_count', 'prompt_length'}
        if v not in valid_fields:
            raise ValueError(f"Invalid sort field: {v}. Valid: {valid_fields}")
        return v
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        if v.lower() not in {'asc', 'desc'}:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower()


class ShowRequest(BaseModel):
    """Request to show details of a specific script."""
    
    script_id: str = Field(..., description="Unique identifier of the script")
    include_code: bool = Field(True, description="Include the generated code in response")
    include_execution_logs: bool = Field(False, description="Include execution logs if available")


class ClearRequest(BaseModel):
    """Request to clear cache or specific scripts."""
    
    script_ids: Optional[List[str]] = Field(None, description="Specific script IDs to clear")
    language: Optional[str] = Field(None, description="Clear all scripts of specific language")
    older_than: Optional[int] = Field(None, description="Clear scripts older than N seconds")
    all: bool = Field(False, description="Clear all cached scripts")
    
    @field_validator('script_ids')
    @classmethod
    def validate_script_ids(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and len(v) == 0:
            raise ValueError("script_ids cannot be empty list")
        return v
