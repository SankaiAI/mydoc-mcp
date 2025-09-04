# Docker Deployment Guide

## Overview

This document provides comprehensive instructions for deploying mydocs-mcp using Docker containers.

## Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- At least 256MB available RAM
- 1GB available disk space

## Quick Start

### Production Deployment

```bash
# Clone the repository
git clone https://github.com/yourusername/mydocs-mcp.git
cd mydocs-mcp

# Configure environment
cp .env.docker .env
# Edit .env with your document paths

# Start the container
docker-compose up -d

# Check health
docker-compose logs mydocs-mcp
```

### Development Setup

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# With database viewer
docker-compose -f docker-compose.dev.yml --profile debug up
```

## Configuration

The Docker deployment supports various configuration options through environment variables and volume mounts.

### Volume Mounts

- `/app/data`: Persistent application data
- `/documents`: Your document directories (read-only)
- `/app/config`: Configuration overrides (optional)

### Environment Variables

- `MCP_TRANSPORT`: Communication protocol (default: stdio)
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARN, ERROR)
- `DATABASE_PATH`: SQLite database location
- `DOCUMENT_DIRECTORIES`: Document search paths
- `MAX_DOCUMENT_SIZE`: Maximum file size for indexing

## Monitoring

The container includes comprehensive health checks and logging:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' mydocs-mcp-prod

# View logs
docker-compose logs -f mydocs-mcp

# Monitor resource usage
docker stats mydocs-mcp-prod
```

## Troubleshooting

Common issues and solutions:

1. **Container won't start**: Check file permissions on mounted volumes
2. **Database errors**: Verify write permissions on data directory
3. **Performance issues**: Increase memory limits in docker-compose.yml
4. **Document access**: Check document directory mounts and permissions

## Security Considerations

- Container runs as non-root user (appuser:1000)
- Read-only document mounts for security
- Resource limits prevent abuse
- Health checks ensure service availability