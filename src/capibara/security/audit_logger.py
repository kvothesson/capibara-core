"""Audit logging for security and compliance."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from capibara.models.security import AuditEvent, SecurityViolation
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class AuditLogger:
    """Handles audit logging for security and compliance."""

    def __init__(self, log_dir: str = "~/.capibara/logs/audit"):
        self.log_dir = Path(log_dir).expanduser()
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Audit log file
        self.audit_log_file = self.log_dir / "audit.jsonl"

        # Security violations log
        self.violations_log_file = self.log_dir / "violations.jsonl"

        # Statistics
        self.stats = {
            "total_events": 0,
            "security_violations": 0,
            "script_generations": 0,
            "script_executions": 0,
            "errors": 0,
        }

    async def log_event(self, event: AuditEvent) -> None:
        """Log an audit event."""
        try:
            # Add timestamp if not present
            if not event.timestamp:
                event.timestamp = datetime.now(UTC)

            # Write to audit log
            await self._write_audit_event(event)

            # Update statistics
            self._update_stats(event)

            # Log to application logger
            logger.info(
                "Audit event logged",
                event_type=event.event_type,
                event_id=event.event_id,
                script_id=event.script_id,
            )

        except Exception as e:
            logger.error(
                "Failed to log audit event", event_id=event.event_id, error=str(e)
            )
            raise AuditLoggingError(f"Failed to log audit event: {str(e)}") from e

    async def log_script_generation(
        self,
        script_id: str,
        prompt: str,
        language: str,
        provider: str,
        user_id: str | None = None,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Log script generation event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type="script_generated",
            script_id=script_id,
            user_id=user_id,
            session_id=session_id,
            message=f"Script generated: {script_id}",
            details={
                "prompt_length": len(prompt),
                "language": language,
                "provider": provider,
                **kwargs,
            },
        )

        await self.log_event(event)

    async def log_script_execution(
        self,
        script_id: str,
        execution_result: dict[str, Any],
        user_id: str | None = None,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Log script execution event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type="script_executed",
            script_id=script_id,
            user_id=user_id,
            session_id=session_id,
            message=f"Script executed: {script_id}",
            details={
                "success": execution_result.get("success", False),
                "exit_code": execution_result.get("exit_code", -1),
                "execution_time_ms": execution_result.get("execution_time_ms", 0),
                "memory_used_mb": execution_result.get("memory_used_mb", 0.0),
                **kwargs,
            },
        )

        await self.log_event(event)

    async def log_security_violation(
        self,
        violation: SecurityViolation,
        script_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Log security violation event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type="security_violation",
            script_id=script_id,
            user_id=user_id,
            session_id=session_id,
            severity="error",
            message=f"Security violation: {violation.message}",
            details={
                "rule_name": violation.rule_name,
                "severity": violation.severity,
                "pattern_matched": violation.pattern_matched,
                "line_number": violation.line_number,
                "column_number": violation.column_number,
                **kwargs,
            },
            security_violations=[violation],
        )

        await self.log_event(event)

        # Also write to violations log
        await self._write_violation(violation)

    async def log_error(
        self,
        error: str,
        error_code: str,
        script_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Log error event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type="error",
            script_id=script_id,
            user_id=user_id,
            session_id=session_id,
            severity="error",
            message=f"Error: {error}",
            details={"error_code": error_code, **kwargs},
        )

        await self.log_event(event)

    async def _write_audit_event(self, event: AuditEvent) -> None:
        """Write audit event to log file."""
        log_entry = {
            "timestamp": event.timestamp.isoformat(),
            "event_id": event.event_id,
            "event_type": event.event_type,
            "script_id": event.script_id,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "severity": event.severity,
            "message": event.message,
            "details": event.details,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "resource_usage": event.resource_usage,
            "security_violations": (
                [v.dict() for v in event.security_violations]
                if event.security_violations
                else []
            ),
        }

        with open(self.audit_log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    async def _write_violation(self, violation: SecurityViolation) -> None:
        """Write security violation to violations log."""
        violation_entry = {
            "timestamp": violation.timestamp.isoformat(),
            "violation_id": violation.violation_id,
            "rule_name": violation.rule_name,
            "severity": violation.severity,
            "message": violation.message,
            "pattern_matched": violation.pattern_matched,
            "line_number": violation.line_number,
            "column_number": violation.column_number,
            "code_snippet": violation.code_snippet,
            "context": violation.context,
        }

        with open(self.violations_log_file, "a") as f:
            f.write(json.dumps(violation_entry) + "\n")

    def _update_stats(self, event: AuditEvent) -> None:
        """Update audit statistics."""
        self.stats["total_events"] += 1

        if event.event_type == "script_generated":
            self.stats["script_generations"] += 1
        elif event.event_type == "script_executed":
            self.stats["script_executions"] += 1
        elif event.event_type == "security_violation":
            self.stats["security_violations"] += 1
        elif event.event_type == "error":
            self.stats["errors"] += 1

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        import uuid

        return f"event_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

    def get_audit_stats(self) -> dict[str, Any]:
        """Get audit logging statistics."""
        return {
            **self.stats,
            "log_directory": str(self.log_dir),
            "audit_log_file": str(self.audit_log_file),
            "violations_log_file": str(self.violations_log_file),
        }

    async def query_events(
        self,
        event_types: list[str] | None = None,
        script_id: str | None = None,
        user_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query audit events with filters."""
        events = []

        try:
            with open(self.audit_log_file) as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())

                        # Apply filters
                        if event_types and event.get("event_type") not in event_types:
                            continue

                        if script_id and event.get("script_id") != script_id:
                            continue

                        if user_id and event.get("user_id") != user_id:
                            continue

                        if start_time:
                            event_time = datetime.fromisoformat(
                                event.get("timestamp", "")
                            )
                            if event_time < start_time:
                                continue

                        if end_time:
                            event_time = datetime.fromisoformat(
                                event.get("timestamp", "")
                            )
                            if event_time > end_time:
                                continue

                        events.append(event)

                        if len(events) >= limit:
                            break

                    except json.JSONDecodeError:
                        continue

            # Sort by timestamp (newest first)
            events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        except FileNotFoundError:
            logger.warning("Audit log file not found", file=str(self.audit_log_file))

        return events


class AuditLoggingError(Exception):
    """Raised when audit logging fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
