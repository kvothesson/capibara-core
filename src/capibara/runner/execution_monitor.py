"""Execution monitoring for container-based script execution."""

import time
from dataclasses import dataclass
from typing import Any

from capibara.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionMetrics:
    """Metrics for script execution."""

    start_time: float
    end_time: float | None = None
    memory_peak_mb: float = 0.0
    memory_current_mb: float = 0.0
    cpu_time_ms: int = 0
    files_created: int = 0
    files_modified: int = 0
    files_deleted: int = 0
    network_requests: int = 0
    subprocess_calls: int = 0
    disk_io_bytes: int = 0

    @property
    def duration_ms(self) -> int:
        """Get execution duration in milliseconds."""
        if self.end_time is None:
            return int((time.time() - self.start_time) * 1000)
        return int((self.end_time - self.start_time) * 1000)

    @property
    def is_completed(self) -> bool:
        """Check if execution is completed."""
        return self.end_time is not None


class ExecutionMonitor:
    """Monitors script execution in containers."""

    def __init__(self):
        self.active_executions: dict[str, ExecutionMetrics] = {}

    def start_execution(self, execution_id: str) -> ExecutionMetrics:
        """Start monitoring an execution."""
        metrics = ExecutionMetrics(start_time=time.time())
        self.active_executions[execution_id] = metrics

        logger.debug("Started execution monitoring", execution_id=execution_id)
        return metrics

    def update_memory(self, execution_id: str, memory_mb: float) -> None:
        """Update memory usage for an execution."""
        if execution_id in self.active_executions:
            metrics = self.active_executions[execution_id]
            metrics.memory_current_mb = memory_mb
            metrics.memory_peak_mb = max(metrics.memory_peak_mb, memory_mb)

    def update_cpu_time(self, execution_id: str, cpu_time_ms: int) -> None:
        """Update CPU time for an execution."""
        if execution_id in self.active_executions:
            self.active_executions[execution_id].cpu_time_ms = cpu_time_ms

    def record_file_operation(self, execution_id: str, operation: str) -> None:
        """Record a file operation."""
        if execution_id not in self.active_executions:
            return

        metrics = self.active_executions[execution_id]

        if operation == "create":
            metrics.files_created += 1
        elif operation == "modify":
            metrics.files_modified += 1
        elif operation == "delete":
            metrics.files_deleted += 1

    def record_network_request(self, execution_id: str) -> None:
        """Record a network request."""
        if execution_id in self.active_executions:
            self.active_executions[execution_id].network_requests += 1

    def record_subprocess_call(self, execution_id: str) -> None:
        """Record a subprocess call."""
        if execution_id in self.active_executions:
            self.active_executions[execution_id].subprocess_calls += 1

    def record_disk_io(self, execution_id: str, bytes_count: int) -> None:
        """Record disk I/O."""
        if execution_id in self.active_executions:
            self.active_executions[execution_id].disk_io_bytes += bytes_count

    def end_execution(self, execution_id: str) -> ExecutionMetrics | None:
        """End monitoring an execution."""
        if execution_id not in self.active_executions:
            return None

        metrics = self.active_executions[execution_id]
        metrics.end_time = time.time()

        logger.debug(
            "Ended execution monitoring",
            execution_id=execution_id,
            duration_ms=metrics.duration_ms,
        )

        return metrics

    def get_execution_metrics(self, execution_id: str) -> ExecutionMetrics | None:
        """Get metrics for a specific execution."""
        return self.active_executions.get(execution_id)

    def get_all_metrics(self) -> dict[str, ExecutionMetrics]:
        """Get all execution metrics."""
        return self.active_executions.copy()

    def clear_completed_executions(self) -> int:
        """Clear completed executions and return count."""
        completed_ids = [
            exec_id
            for exec_id, metrics in self.active_executions.items()
            if metrics.is_completed
        ]

        for exec_id in completed_ids:
            del self.active_executions[exec_id]

        logger.debug("Cleared completed executions", count=len(completed_ids))
        return len(completed_ids)

    def get_active_executions_count(self) -> int:
        """Get count of active executions."""
        return len(
            [
                exec_id
                for exec_id, metrics in self.active_executions.items()
                if not metrics.is_completed
            ]
        )

    def get_execution_summary(self, execution_id: str) -> dict[str, Any] | None:
        """Get a summary of execution metrics."""
        metrics = self.get_execution_metrics(execution_id)
        if not metrics:
            return None

        return {
            "execution_id": execution_id,
            "duration_ms": metrics.duration_ms,
            "memory_peak_mb": metrics.memory_peak_mb,
            "memory_current_mb": metrics.memory_current_mb,
            "cpu_time_ms": metrics.cpu_time_ms,
            "files_created": metrics.files_created,
            "files_modified": metrics.files_modified,
            "files_deleted": metrics.files_deleted,
            "network_requests": metrics.network_requests,
            "subprocess_calls": metrics.subprocess_calls,
            "disk_io_bytes": metrics.disk_io_bytes,
            "is_completed": metrics.is_completed,
        }
