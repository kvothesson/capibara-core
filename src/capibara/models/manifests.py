"""Manifest models for configuration and policies."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ResourceLimits(BaseModel):
    """Resource limits for script execution."""

    cpu_time_seconds: int = Field(
        default=30, ge=1, le=300, description="Maximum CPU time in seconds"
    )
    memory_mb: int = Field(
        default=512, ge=64, le=2048, description="Maximum memory in MB"
    )
    execution_time_seconds: int = Field(
        default=60, ge=1, le=600, description="Maximum wall clock time in seconds"
    )
    max_file_size_mb: int = Field(
        default=10, ge=1, le=100, description="Maximum file size for I/O operations"
    )
    max_files: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of files that can be created",
    )
    network_access: bool = Field(
        default=False, description="Whether network access is allowed"
    )
    allow_subprocess: bool = Field(
        default=False, description="Whether subprocess execution is allowed"
    )


class SecurityRule(BaseModel):
    """Individual security rule."""

    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    pattern: str = Field(..., description="Regex pattern to match")
    severity: str = Field(
        default="error", description="Severity level (error, warning, info)"
    )
    action: str = Field(
        default="block", description="Action to take (block, warn, allow)"
    )
    language: str | None = Field(
        default=None, description="Specific language this applies to"
    )

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        if v not in {"error", "warning", "info"}:
            raise ValueError("Severity must be 'error', 'warning', or 'info'")
        return v

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in {"block", "warn", "allow"}:
            raise ValueError("Action must be 'block', 'warn', or 'allow'")
        return v


class SecurityPolicy(BaseModel):
    """Security policy configuration."""

    name: str = Field(..., description="Policy name")
    description: str = Field(..., description="Policy description")
    version: str = Field(default="1.0", description="Policy version")
    rules: list[SecurityRule] = Field(..., description="Security rules")
    resource_limits: ResourceLimits = Field(
        default_factory=lambda: ResourceLimits(), description="Resource limits"
    )
    allowed_imports: list[str] = Field(
        default_factory=list, description="Allowed import patterns"
    )
    blocked_imports: list[str] = Field(
        default_factory=list, description="Blocked import patterns"
    )
    allowed_functions: list[str] = Field(
        default_factory=list, description="Allowed function patterns"
    )
    blocked_functions: list[str] = Field(
        default_factory=list, description="Blocked function patterns"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class LLMProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    name: str = Field(..., description="Provider name")
    type: str = Field(..., description="Provider type (openai, groq, etc.)")
    api_key: str | None = Field(default=None, description="API key (if required)")
    base_url: str | None = Field(default=None, description="Base URL for API")
    model: str = Field(..., description="Model name to use")
    max_tokens: int = Field(
        default=4000, ge=100, le=32000, description="Maximum tokens to generate"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    timeout_seconds: int = Field(
        default=30, ge=5, le=300, description="Request timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3, ge=0, le=10, description="Number of retry attempts"
    )
    priority: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Priority for fallback (lower = higher priority)",
    )
    enabled: bool = Field(default=True, description="Whether provider is enabled")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration"
    )


class ExecutionConfig(BaseModel):
    """Execution configuration."""

    container_runtime: str = Field(
        default="docker", description="Container runtime (docker, podman)"
    )
    base_image: str = Field(
        default="python:3.11-slim", description="Base container image"
    )
    working_directory: str = Field(
        default="/workspace", description="Working directory in container"
    )
    user: str = Field(default="nobody", description="User to run as in container")
    environment: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    volumes: list[str] = Field(default_factory=list, description="Volume mounts")
    security_opt: list[str] = Field(
        default_factory=list, description="Security options"
    )
    cap_drop: list[str] = Field(
        default_factory=list, description="Capabilities to drop"
    )
    cap_add: list[str] = Field(default_factory=list, description="Capabilities to add")
    seccomp_profile: str | None = Field(
        default=None, description="Seccomp profile path"
    )
    apparmor_profile: str | None = Field(
        default=None, description="AppArmor profile name"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration"
    )


class CapibaraConfig(BaseModel):
    """Main Capibara configuration."""

    version: str = Field(default="1.0", description="Configuration version")
    llm_providers: list[LLMProviderConfig] = Field(
        ..., description="LLM provider configurations"
    )
    security_policies: list[SecurityPolicy] = Field(
        ..., description="Security policies"
    )
    execution: ExecutionConfig = Field(
        default_factory=lambda: ExecutionConfig(), description="Execution configuration"
    )
    cache: dict[str, Any] = Field(
        default_factory=dict, description="Cache configuration"
    )
    logging: dict[str, Any] = Field(
        default_factory=dict, description="Logging configuration"
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict, description="Metrics configuration"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
