"""Metrics collection utilities for Capibara Core."""

import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and manages metrics for Capibara Core."""
    
    def __init__(self):
        self.metrics: List[MetricPoint] = []
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        if name not in self.counters:
            self.counters[name] = 0.0
        
        self.counters[name] += value
        
        self.metrics.append(MetricPoint(
            name=f"{name}_counter",
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        ))
        
        logger.debug("Counter incremented", name=name, value=value, total=self.counters[name])
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        self.gauges[name] = value
        
        self.metrics.append(MetricPoint(
            name=f"{name}_gauge",
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        ))
        
        logger.debug("Gauge set", name=name, value=value)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram metric value."""
        if name not in self.histograms:
            self.histograms[name] = []
        
        self.histograms[name].append(value)
        
        self.metrics.append(MetricPoint(
            name=f"{name}_histogram",
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        ))
        
        logger.debug("Histogram recorded", name=name, value=value)
    
    def record_timing(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timing metric."""
        self.record_histogram(f"{name}_duration", duration_ms, tags)
    
    def get_counter(self, name: str) -> float:
        """Get current counter value."""
        return self.counters.get(name, 0.0)
    
    def get_gauge(self, name: str) -> float:
        """Get current gauge value."""
        return self.gauges.get(name, 0.0)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics."""
        values = self.histograms.get(name, [])
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_values = sorted(values)
        count = len(values)
        
        return {
            "count": count,
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / count,
            "p50": sorted_values[int(count * 0.5)] if count > 0 else 0,
            "p95": sorted_values[int(count * 0.95)] if count > 0 else 0,
            "p99": sorted_values[int(count * 0.99)] if count > 0 else 0,
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics in a dictionary format."""
        return {
            "counters": self.counters.copy(),
            "gauges": self.gauges.copy(),
            "histograms": {
                name: self.get_histogram_stats(name)
                for name in self.histograms.keys()
            },
            "total_metrics": len(self.metrics),
        }
    
    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        logger.info("All metrics cleared")
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        if format == "json":
            import json
            return json.dumps(self.get_all_metrics(), indent=2)
        elif format == "prometheus":
            return self._export_prometheus()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # Export counters
        for name, value in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        # Export gauges
        for name, value in self.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        # Export histograms
        for name, stats in self.get_all_metrics()["histograms"].items():
            lines.append(f"# TYPE {name} histogram")
            lines.append(f"{name}_count {stats['count']}")
            lines.append(f"{name}_sum {stats['avg'] * stats['count']}")
            lines.append(f"{name}_bucket{{le=\"+Inf\"}} {stats['count']}")
        
        return "\n".join(lines)


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector


def increment_counter(name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
    """Increment a counter metric using the global collector."""
    _metrics_collector.increment_counter(name, value, tags)


def set_gauge(name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
    """Set a gauge metric using the global collector."""
    _metrics_collector.set_gauge(name, value, tags)


def record_histogram(name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
    """Record a histogram metric using the global collector."""
    _metrics_collector.record_histogram(name, value, tags)


def record_timing(name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None) -> None:
    """Record a timing metric using the global collector."""
    _metrics_collector.record_timing(name, duration_ms, tags)
