# Multi-stage build for Capibara Core
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILDPLATFORM
ARG TARGETPLATFORM

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./

# Copy source code and project files
COPY src/ /app/src/
COPY README.md LICENSE ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    docker.io \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r capibara && useradd -r -g capibara capibara

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Copy application code
COPY src/ /app/src/
COPY config/ /app/config/

# Create necessary directories
RUN mkdir -p /app/logs /app/cache /app/tmp && \
    chown -R capibara:capibara /app

# Switch to non-root user
USER capibara

# Set environment variables
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    CACHE_DIR=/app/cache \
    LOG_DIR=/app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD capibara health || exit 1

# Expose port (if needed for API in future)
EXPOSE 8000

# Default command
CMD ["capibara", "--help"]
