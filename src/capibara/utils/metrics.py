"""Prometheus metrics collection for Capibara Core."""

import time
from typing import Any

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Collects and exposes Prometheus metrics for Capibara Core."""

    def __init__(self, registry: CollectorRegistry | None = None):
        self.registry = registry or CollectorRegistry()
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Set up Prometheus metrics."""

        # Script generation metrics
        self.script_generations_total = Counter(
            "capibara_script_generations_total",
            "Total number of script generation requests",
            ["language", "provider", "status"],
            registry=self.registry,
        )

        self.script_generation_duration = Histogram(
            "capibara_script_generation_duration_seconds",
            "Time spent generating scripts",
            ["language", "provider"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry,
        )

        # Execution metrics
        self.script_executions_total = Counter(
            "capibara_script_executions_total",
            "Total number of script executions",
            ["language", "status"],
            registry=self.registry,
        )

        self.script_execution_duration = Histogram(
            "capibara_script_execution_duration_seconds",
            "Time spent executing scripts",
            ["language"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
            registry=self.registry,
        )

        self.script_execution_memory = Histogram(
            "capibara_script_execution_memory_bytes",
            "Memory used during script execution",
            ["language"],
            buckets=[
                1024 * 1024,
                5 * 1024 * 1024,
                10 * 1024 * 1024,
                25 * 1024 * 1024,
                50 * 1024 * 1024,
                100 * 1024 * 1024,
            ],
            registry=self.registry,
        )

        # Cache metrics
        self.cache_operations_total = Counter(
            "capibara_cache_operations_total",
            "Total number of cache operations",
            ["operation", "result"],
            registry=self.registry,
        )

        self.cache_size_bytes = Gauge(
            "capibara_cache_size_bytes",
            "Total size of cached scripts in bytes",
            registry=self.registry,
        )

        self.cache_entries_total = Gauge(
            "capibara_cache_entries_total",
            "Total number of cached scripts",
            registry=self.registry,
        )

        # Security metrics
        self.security_scans_total = Counter(
            "capibara_security_scans_total",
            "Total number of security scans",
            ["language", "policy", "result"],
            registry=self.registry,
        )

        self.security_violations_total = Counter(
            "capibara_security_violations_total",
            "Total number of security violations",
            ["rule_name", "severity"],
            registry=self.registry,
        )

        self.security_scan_duration = Histogram(
            "capibara_security_scan_duration_seconds",
            "Time spent on security scans",
            ["language"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
            registry=self.registry,
        )

        # LLM provider metrics
        self.llm_requests_total = Counter(
            "capibara_llm_requests_total",
            "Total number of LLM requests",
            ["provider", "model", "status"],
            registry=self.registry,
        )

        self.llm_request_duration = Histogram(
            "capibara_llm_request_duration_seconds",
            "Time spent on LLM requests",
            ["provider", "model"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry,
        )

        self.llm_tokens_total = Counter(
            "capibara_llm_tokens_total",
            "Total number of LLM tokens processed",
            ["provider", "model", "type"],
            registry=self.registry,
        )

        # System metrics
        self.active_containers = Gauge(
            "capibara_active_containers",
            "Number of active execution containers",
            registry=self.registry,
        )

        self.container_errors_total = Counter(
            "capibara_container_errors_total",
            "Total number of container errors",
            ["error_type"],
            registry=self.registry,
        )

        # Health check metrics
        self.health_check_status = Gauge(
            "capibara_health_check_status",
            "Health check status (1=healthy, 0=unhealthy)",
            ["component"],
            registry=self.registry,
        )

        # Application info
        self.app_info = Info(
            "capibara_app_info", "Application information", registry=self.registry
        )

        # Set application info
        self.app_info.info(
            {
                "version": "0.1.0",
                "build_date": time.strftime("%Y-%m-%d"),
                "python_version": "3.11",
            }
        )

        logger.info("Metrics collector initialized")

    def record_script_generation(
        self, language: str, provider: str, status: str, duration: float
    ) -> None:
        """Record script generation metrics."""
        self.script_generations_total.labels(
            language=language, provider=provider, status=status
        ).inc()

        self.script_generation_duration.labels(
            language=language, provider=provider
        ).observe(duration)

        logger.debug(
            "Recorded script generation metrics",
            language=language,
            provider=provider,
            status=status,
            duration=duration,
        )

    def record_script_execution(
        self, language: str, status: str, duration: float, memory_bytes: int
    ) -> None:
        """Record script execution metrics."""
        self.script_executions_total.labels(language=language, status=status).inc()

        self.script_execution_duration.labels(language=language).observe(duration)

        self.script_execution_memory.labels(language=language).observe(memory_bytes)

        logger.debug(
            "Recorded script execution metrics",
            language=language,
            status=status,
            duration=duration,
            memory_bytes=memory_bytes,
        )

    def record_cache_operation(self, operation: str, result: str) -> None:
        """Record cache operation metrics."""
        self.cache_operations_total.labels(operation=operation, result=result).inc()

        logger.debug(
            "Recorded cache operation metrics", operation=operation, result=result
        )

    def update_cache_metrics(self, size_bytes: int, entries_count: int) -> None:
        """Update cache size and entry count metrics."""
        self.cache_size_bytes.set(size_bytes)
        self.cache_entries_total.set(entries_count)

        logger.debug(
            "Updated cache metrics", size_bytes=size_bytes, entries_count=entries_count
        )

    def record_security_scan(
        self, language: str, policy: str, result: str, duration: float
    ) -> None:
        """Record security scan metrics."""
        self.security_scans_total.labels(
            language=language, policy=policy, result=result
        ).inc()

        self.security_scan_duration.labels(language=language).observe(duration)

        logger.debug(
            "Recorded security scan metrics",
            language=language,
            policy=policy,
            result=result,
            duration=duration,
        )

    def record_security_violation(self, rule_name: str, severity: str) -> None:
        """Record security violation metrics."""
        self.security_violations_total.labels(
            rule_name=rule_name, severity=severity
        ).inc()

        logger.debug(
            "Recorded security violation metrics",
            rule_name=rule_name,
            severity=severity,
        )

    def record_llm_request(
        self,
        provider: str,
        model: str,
        status: str,
        duration: float,
        tokens_prompt: int = 0,
        tokens_completion: int = 0,
    ) -> None:
        """Record LLM request metrics."""
        self.llm_requests_total.labels(
            provider=provider, model=model, status=status
        ).inc()

        self.llm_request_duration.labels(provider=provider, model=model).observe(
            duration
        )

        if tokens_prompt > 0:
            self.llm_tokens_total.labels(
                provider=provider, model=model, type="prompt"
            ).inc(tokens_prompt)

        if tokens_completion > 0:
            self.llm_tokens_total.labels(
                provider=provider, model=model, type="completion"
            ).inc(tokens_completion)

        logger.debug(
            "Recorded LLM request metrics",
            provider=provider,
            model=model,
            status=status,
            duration=duration,
        )

    def update_active_containers(self, count: int) -> None:
        """Update active containers count."""
        self.active_containers.set(count)

        logger.debug("Updated active containers count", count=count)

    def record_container_error(self, error_type: str) -> None:
        """Record container error metrics."""
        self.container_errors_total.labels(error_type=error_type).inc()

        logger.debug("Recorded container error metrics", error_type=error_type)

    def update_health_status(self, component: str, healthy: bool) -> None:
        """Update health check status."""
        self.health_check_status.labels(component=component).set(1 if healthy else 0)

        logger.debug("Updated health status", component=component, healthy=healthy)

    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        return generate_latest(self.registry).decode("utf-8")

    def get_metrics_dict(self) -> dict[str, Any]:
        """Get metrics as a dictionary for debugging."""
        metrics: dict[str, Any] = {}

        # Collect all metric families
        for metric_family in self.registry.collect():
            family_name = metric_family.name
            family_type = metric_family.type

            if family_name not in metrics:
                metrics[family_name] = {"type": family_type, "samples": []}

            for sample in metric_family.samples:
                metrics[family_name]["samples"].append(
                    {
                        "name": sample.name,
                        "labels": sample.labels,
                        "value": sample.value,
                        "timestamp": getattr(sample, "timestamp", None),
                    }
                )

        return metrics


# Global metrics collector instance
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def setup_metrics(registry: CollectorRegistry | None = None) -> MetricsCollector:
    """Set up the global metrics collector."""
    global _metrics_collector
    _metrics_collector = MetricsCollector(registry)
    return _metrics_collector
