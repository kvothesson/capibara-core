"""Security-related models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SecurityViolation(BaseModel):
    """Security violation detected during scanning or execution."""
    
    violation_id: str = Field(..., description="Unique violation identifier")
    rule_name: str = Field(..., description="Name of the violated rule")
    severity: str = Field(..., description="Severity level (error, warning, info)")
    message: str = Field(..., description="Human-readable violation message")
    pattern_matched: str = Field(..., description="Pattern that was matched")
    line_number: Optional[int] = Field(None, description="Line number where violation occurred")
    column_number: Optional[int] = Field(None, description="Column number where violation occurred")
    code_snippet: Optional[str] = Field(None, description="Code snippet containing the violation")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When violation was detected")


class AuditEvent(BaseModel):
    """Audit event for security and compliance logging."""
    
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event (script_generated, script_executed, security_violation, etc.)")
    script_id: Optional[str] = Field(None, description="Associated script ID")
    user_id: Optional[str] = Field(None, description="User who triggered the event")
    session_id: Optional[str] = Field(None, description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    severity: str = Field("info", description="Event severity")
    message: str = Field(..., description="Event message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event details")
    ip_address: Optional[str] = Field(None, description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    resource_usage: Optional[Dict[str, Any]] = Field(None, description="Resource usage information")
    security_violations: List[SecurityViolation] = Field(default_factory=list, description="Associated security violations")


class ResourceUsage(BaseModel):
    """Resource usage information."""
    
    cpu_time_ms: int = Field(0, description="CPU time used in milliseconds")
    memory_peak_mb: float = Field(0.0, description="Peak memory usage in MB")
    memory_current_mb: float = Field(0.0, description="Current memory usage in MB")
    execution_time_ms: int = Field(0, description="Total execution time in milliseconds")
    files_created: int = Field(0, description="Number of files created")
    files_modified: int = Field(0, description="Number of files modified")
    files_deleted: int = Field(0, description="Number of files deleted")
    network_requests: int = Field(0, description="Number of network requests made")
    subprocess_calls: int = Field(0, description="Number of subprocess calls made")
    disk_io_bytes: int = Field(0, description="Total disk I/O in bytes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional resource metrics")


class SecurityScanResult(BaseModel):
    """Result of security scanning."""
    
    scan_id: str = Field(..., description="Unique scan identifier")
    script_id: str = Field(..., description="Scanned script identifier")
    scan_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When scan was performed")
    violations: List[SecurityViolation] = Field(default_factory=list, description="Detected violations")
    passed: bool = Field(True, description="Whether scan passed (no blocking violations)")
    scan_duration_ms: int = Field(0, description="Scan duration in milliseconds")
    rules_applied: List[str] = Field(default_factory=list, description="Security rules that were applied")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional scan information")


class SandboxConfig(BaseModel):
    """Sandbox configuration for script execution."""
    
    container_id: str = Field(..., description="Container identifier")
    image: str = Field(..., description="Container image")
    working_directory: str = Field("/workspace", description="Working directory")
    user: str = Field("nobody", description="User to run as")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    resource_limits: Dict[str, Any] = Field(default_factory=dict, description="Resource limits")
    security_options: List[str] = Field(default_factory=list, description="Security options")
    network_mode: str = Field("none", description="Network mode")
    read_only: bool = Field(True, description="Whether filesystem is read-only")
    seccomp_profile: Optional[str] = Field(None, description="Seccomp profile")
    apparmor_profile: Optional[str] = Field(None, description="AppArmor profile")
    capabilities: List[str] = Field(default_factory=list, description="Linux capabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")
