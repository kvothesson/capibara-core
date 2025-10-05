"""HTTP server for Capibara Core API."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

import uvicorn
from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Response,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from capibara.api.health_endpoint import health_check, health_status
from capibara.utils.config import get_config
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    config = get_config()

    app = FastAPI(
        title="Capibara Core API",
        description="AI-powered script generation and execution platform",
        version="0.1.0",
        docs_url="/docs" if config.debug else None,
        redoc_url="/redoc" if config.debug else None,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if config.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request logging middleware
    @app.middleware("http")  # type: ignore[misc]
    async def log_requests(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = datetime.now(UTC)

        # Log request
        logger.info(
            "HTTP request",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
        )

        # Process request
        response = await call_next(request)

        # Log response
        duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
        logger.info(
            "HTTP response",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response

    # Health check endpoints
    @app.get("/health")  # type: ignore[misc]
    async def health_endpoint() -> JSONResponse:
        """Comprehensive health check endpoint."""
        try:
            result = await health_check(quick=False)
            status_code = 200 if result["overall_status"] == "healthy" else 503
            return JSONResponse(content=result, status_code=status_code)
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return JSONResponse(
                content={
                    "overall_status": "unhealthy",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "error": str(e),
                },
                status_code=503,
            )

    @app.get("/health/quick")  # type: ignore[misc]
    async def quick_health_endpoint() -> JSONResponse:
        """Quick health check endpoint."""
        try:
            result = await health_check(quick=True)
            status_code = 200 if result["overall_status"] == "healthy" else 503
            return JSONResponse(content=result, status_code=status_code)
        except Exception as e:
            logger.error("Quick health check failed", error=str(e))
            return JSONResponse(
                content={
                    "overall_status": "unhealthy",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "error": str(e),
                },
                status_code=503,
            )

    @app.get("/health/status")  # type: ignore[misc]
    async def health_status_endpoint() -> JSONResponse:
        """Get cached health status."""
        try:
            result = await health_status()
            status_code = 200 if result.get("overall_status") == "healthy" else 503
            return JSONResponse(content=result, status_code=status_code)
        except Exception as e:
            logger.error("Health status check failed", error=str(e))
            return JSONResponse(
                content={
                    "overall_status": "unknown",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "error": str(e),
                },
                status_code=503,
            )

    # Metrics endpoint (for Prometheus)
    @app.get("/metrics")  # type: ignore[misc]
    async def metrics_endpoint() -> Response:
        """Prometheus metrics endpoint."""
        try:
            # This would integrate with the metrics system
            # For now, return basic metrics
            metrics = generate_basic_metrics()
            return Response(content=metrics, media_type="text/plain")
        except Exception as e:
            logger.error("Metrics endpoint failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e)) from e

    # Root endpoint
    @app.get("/")  # type: ignore[misc]
    async def root() -> dict[str, Any]:
        """Root endpoint with API information."""
        return {
            "name": "Capibara Core API",
            "version": "0.1.0",
            "description": "AI-powered script generation and execution platform",
            "endpoints": {
                "health": "/health",
                "health_quick": "/health/quick",
                "health_status": "/health/status",
                "metrics": "/metrics",
                "docs": "/docs" if config.debug else "disabled",
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # Error handlers
    @app.exception_handler(404)  # type: ignore[misc]
    async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            content={
                "error": "Not Found",
                "message": f"The requested endpoint {request.url.path} was not found",
                "timestamp": datetime.now(UTC).isoformat(),
            },
            status_code=404,
        )

    @app.exception_handler(500)  # type: ignore[misc]
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Internal server error", error=str(exc), url=str(request.url))
        return JSONResponse(
            content={
                "error": "Internal Server Error",
                "message": "An internal error occurred",
                "timestamp": datetime.now(UTC).isoformat(),
            },
            status_code=500,
        )

    return app


def generate_basic_metrics() -> str:
    """Generate basic Prometheus metrics."""
    # This is a simplified version - in production you'd use a proper metrics library
    import time

    import psutil

    metrics = []

    # System metrics
    try:
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        metrics.extend(
            [
                "# HELP capibara_cpu_usage_percent CPU usage percentage",
                "# TYPE capibara_cpu_usage_percent gauge",
                f"capibara_cpu_usage_percent {cpu_percent}",
                "",
                "# HELP capibara_memory_usage_percent Memory usage percentage",
                "# TYPE capibara_memory_usage_percent gauge",
                f"capibara_memory_usage_percent {memory.percent}",
                "",
                "# HELP capibara_disk_usage_percent Disk usage percentage",
                "# TYPE capibara_disk_usage_percent gauge",
                f"capibara_disk_usage_percent {(disk.used / disk.total) * 100}",
                "",
            ]
        )
    except ImportError:
        metrics.extend(
            [
                "# HELP capibara_psutil_available psutil availability",
                "# TYPE capibara_psutil_available gauge",
                "capibara_psutil_available 0",
                "",
            ]
        )

    # Application metrics
    current_time = int(time.time() * 1000)
    metrics.extend(
        [
            "# HELP capibara_uptime_seconds Application uptime in seconds",
            "# TYPE capibara_uptime_seconds counter",
            f"capibara_uptime_seconds {current_time}",
            "",
            "# HELP capibara_requests_total Total number of requests",
            "# TYPE capibara_requests_total counter",
            "capibara_requests_total 0",
            "",
            "# HELP capibara_health_check_total Total number of health checks",
            "# TYPE capibara_health_check_total counter",
            "capibara_health_check_total 0",
            "",
        ]
    )

    return "\n".join(metrics)


async def start_server(
    host: str = "0.0.0.0", port: int = 8000, reload: bool = False
) -> None:
    """Start the HTTP server."""
    config = get_config()

    logger.info(f"Starting Capibara Core API server on {host}:{port}")

    app = create_app()

    # Configure uvicorn
    uvicorn_config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level=config.logging.level.lower(),
        access_log=True,
        reload=reload and config.debug,
    )

    server = uvicorn.Server(uvicorn_config)
    await server.serve()


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """Run the HTTP server (blocking)."""
    asyncio.run(start_server(host, port, reload))


if __name__ == "__main__":
    run_server()
