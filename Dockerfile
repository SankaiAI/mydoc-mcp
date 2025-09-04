# mydocs-mcp Docker Configuration
# Multi-stage build for optimized production container

# Base stage - common dependencies
FROM python:3.11-slim-bullseye as base

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and non-root user for security
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Development stage
FROM base as development

# Install development dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY --chown=appuser:appuser . .

# Create data directories with proper permissions
RUN mkdir -p /app/data/documents /app/data/indexes /app/data/cache /app/data/logs \
    && chown -R appuser:appuser /app/data

USER appuser

# Development command (with reload capability)
CMD ["python", "-m", "src.server"]

# Production build stage
FROM base as production-build

# Copy requirements and install production dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn uvicorn[standard]

# Production runtime stage
FROM python:3.11-slim-bullseye as production

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    MCP_TRANSPORT=stdio \
    LOG_LEVEL=INFO \
    DATABASE_PATH=/app/data/documents.db

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Copy Python packages from build stage
COPY --from=production-build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=production-build /usr/local/bin /usr/local/bin

WORKDIR /app

# Copy application source code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser scripts/docker-entrypoint.sh ./scripts/
COPY --chown=appuser:appuser scripts/docker-healthcheck.sh ./scripts/

# Create data directories and set permissions
RUN mkdir -p /app/data/documents /app/data/indexes /app/data/cache /app/data/logs \
    && chown -R appuser:appuser /app/data /app/scripts \
    && chmod +x /app/scripts/docker-entrypoint.sh /app/scripts/docker-healthcheck.sh

# Set up volume mount points
VOLUME ["/app/data", "/documents"]

# Health check to verify MCP server responsiveness
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/scripts/docker-healthcheck.sh

# Switch to non-root user for security
USER appuser

# Expose port for potential HTTP transport (future enhancement)
EXPOSE 8000

# Use entrypoint script for proper initialization
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]

# Default command to run MCP server
CMD ["python", "-m", "src.server"]