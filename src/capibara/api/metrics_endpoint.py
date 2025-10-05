"""Metrics endpoint for Prometheus monitoring."""

import time
from typing import Dict, Any
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from capibara.utils.metrics import get_metrics_collector
from capibara.utils.logging import get_logger

logger = get_logger(__name__)


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for metrics endpoint."""
    
    def do_GET(self):
        """Handle GET requests to metrics endpoint."""
        if self.path == '/metrics':
            self._handle_metrics()
        elif self.path == '/health':
            self._handle_health()
        else:
            self._handle_not_found()
    
    def _handle_metrics(self):
        """Handle metrics requests."""
        try:
            metrics_collector = get_metrics_collector()
            metrics_data = metrics_collector.get_metrics()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.send_header('Content-Length', str(len(metrics_data.encode('utf-8'))))
            self.end_headers()
            
            self.wfile.write(metrics_data.encode('utf-8'))
            
            logger.debug("Metrics endpoint accessed")
            
        except Exception as e:
            logger.error("Error serving metrics", error=str(e))
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Internal Server Error: {str(e)}".encode('utf-8'))
    
    def _handle_health(self):
        """Handle health check requests."""
        try:
            # Simple health check response
            health_data = {
                'status': 'healthy',
                'timestamp': time.time(),
                'version': '0.1.0'
            }
            
            response = '\n'.join([f"{k}: {v}" for k, v in health_data.items()])
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', str(len(response.encode('utf-8'))))
            self.end_headers()
            
            self.wfile.write(response.encode('utf-8'))
            
            logger.debug("Health endpoint accessed")
            
        except Exception as e:
            logger.error("Error serving health check", error=str(e))
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Internal Server Error: {str(e)}".encode('utf-8'))
    
    def _handle_not_found(self):
        """Handle 404 requests."""
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Override to use our logger instead of default logging."""
        logger.debug("HTTP request", message=format % args)


class MetricsServer:
    """HTTP server for serving Prometheus metrics."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        self.server: HTTPServer = None
        self.server_thread: Thread = None
        self.running = False
    
    def start(self) -> None:
        """Start the metrics server."""
        if self.running:
            logger.warning("Metrics server already running")
            return
        
        try:
            self.server = HTTPServer((self.host, self.port), MetricsHandler)
            self.server_thread = Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            self.running = True
            
            logger.info("Metrics server started", host=self.host, port=self.port)
            
        except Exception as e:
            logger.error("Failed to start metrics server", error=str(e))
            raise
    
    def stop(self) -> None:
        """Stop the metrics server."""
        if not self.running:
            logger.warning("Metrics server not running")
            return
        
        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
            
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=5.0)
            
            self.running = False
            logger.info("Metrics server stopped")
            
        except Exception as e:
            logger.error("Error stopping metrics server", error=str(e))
    
    def _run_server(self) -> None:
        """Run the HTTP server."""
        try:
            logger.info("Starting metrics HTTP server", host=self.host, port=self.port)
            self.server.serve_forever()
        except Exception as e:
            logger.error("Error running metrics server", error=str(e))
        finally:
            self.running = False
    
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self.running
    
    def get_url(self) -> str:
        """Get the metrics server URL."""
        return f"http://{self.host}:{self.port}"


def start_metrics_server(host: str = '0.0.0.0', port: int = 8080) -> MetricsServer:
    """Start a metrics server and return the server instance."""
    server = MetricsServer(host, port)
    server.start()
    return server


def stop_metrics_server(server: MetricsServer) -> None:
    """Stop a metrics server."""
    server.stop()


# Global metrics server instance
_metrics_server: MetricsServer = None


def get_metrics_server() -> MetricsServer:
    """Get the global metrics server instance."""
    return _metrics_server


def setup_metrics_server(host: str = '0.0.0.0', port: int = 8080) -> MetricsServer:
    """Set up and start the global metrics server."""
    global _metrics_server
    _metrics_server = start_metrics_server(host, port)
    return _metrics_server


if __name__ == '__main__':
    # For testing the metrics server
    import signal
    import sys
    
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        if _metrics_server:
            _metrics_server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start metrics server
    server = setup_metrics_server()
    
    logger.info("Metrics server running. Press Ctrl+C to stop.")
    
    try:
        # Keep the main thread alive
        while server.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        server.stop()
