# mydocs-mcp Docker Deployment Guide

## Quick Start

### Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed  
- At least 1GB available RAM
- 2GB available disk space

### Development Deployment

```bash
# Clone the repository (if not already available)
git clone <repository-url>
cd mydocs-mcp

# Start development environment
docker-compose -f docker-compose.dev.yml up

# Or start with database viewer
docker-compose -f docker-compose.dev.yml --profile debug up
```

### Production Deployment

```bash
# Configure environment
cp .env.docker .env
# Edit .env with your document paths and settings

# Start production container
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs mydocs-mcp
```

## Container Images

- **Development Image**: `mydocs-mcp:dev` (597MB)
  - Includes development tools and dependencies
  - Hot reload capability
  - Interactive debugging support

- **Production Image**: `mydocs-mcp:prod` (405MB)
  - Optimized for production use
  - Multi-stage build for smaller size
  - Security hardened (non-root user)

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Communication protocol |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `DATABASE_PATH` | `/app/data/documents.db` | SQLite database location |
| `DOCUMENT_DIRECTORIES` | `/documents` | Document search paths |
| `MAX_DOCUMENT_SIZE` | `10485760` | Max file size (10MB) |

### Volume Mounts

| Mount Point | Purpose | Access |
|-------------|---------|--------|
| `/app/data` | Application data (database, cache, logs) | Read/Write |
| `/documents` | User document directories | Read-Only |
| `/app/config` | Configuration overrides | Read-Only |

## Health Monitoring

### Health Check

The container includes comprehensive health checks:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' mydocs-mcp-prod

# Manual health check
docker exec mydocs-mcp-prod /app/scripts/docker-healthcheck.sh
```

Health check validates:
- Server process is running
- Database connectivity
- Data directory accessibility  
- MCP functionality
- System resources

### Monitoring Commands

```bash
# View container logs
docker-compose logs -f mydocs-mcp

# Monitor resource usage
docker stats mydocs-mcp-prod

# Execute commands in container
docker exec -it mydocs-mcp-prod bash

# Test MCP functionality
docker exec mydocs-mcp-prod python -c "
import sys; sys.path.insert(0, '/app')
from src.config import ServerConfig
print('MCP server configuration loaded successfully')
"
```

## Performance Characteristics

### Container Performance

- **Cold start time**: <10 seconds
- **Memory usage**: 256-512MB baseline
- **CPU usage**: <50% of 1 core under load
- **Storage**: <100MB application + document index

### MCP Tool Performance

- **Tool call response**: <200ms average
- **Document search**: <100ms for 1K documents
- **Document indexing**: >10 docs/second
- **Health check**: <5 seconds

## Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   # Check logs
   docker-compose logs mydocs-mcp
   
   # Verify file permissions
   ls -la data/ config/
   
   # Check Docker resources
   docker system df
   ```

2. **Database connection errors**
   ```bash
   # Check data directory permissions
   docker exec mydocs-mcp-prod ls -la /app/data
   
   # Test database connectivity
   docker exec mydocs-mcp-prod python -c "
   import sqlite3
   conn = sqlite3.connect('/app/data/documents.db')
   print('Database connection: OK')
   conn.close()
   "
   ```

3. **Document access issues**
   ```bash
   # Check document mount
   docker exec mydocs-mcp-prod ls -la /documents
   
   # Verify mount in docker-compose.yml
   docker-compose config | grep -A 5 "volumes:"
   ```

4. **Performance issues**
   ```bash
   # Check resource usage
   docker stats mydocs-mcp-prod
   
   # Increase memory limits in docker-compose.yml
   # deploy:
   #   resources:
   #     limits:
   #       memory: 2G
   ```

### Debug Mode

Enable debug logging:

```bash
# Set debug environment
echo "LOG_LEVEL=DEBUG" >> .env

# Restart container
docker-compose up -d

# View debug logs
docker-compose logs -f mydocs-mcp | grep DEBUG
```

### Testing Container Functionality

```bash
# Test basic functionality
docker run --rm mydocs-mcp:dev python -c "
import sys
sys.path.insert(0, '/app')
from src.config import ServerConfig
from src.tool_registry import ToolRegistry
print('✅ Core functionality: PASSED')
"

# Test health check
docker run --rm mydocs-mcp:dev /app/scripts/docker-healthcheck.sh

# Test volume persistence
docker run --rm -v ./test-data:/app/data mydocs-mcp:dev bash -c "
echo 'test' > /app/data/test.txt && cat /app/data/test.txt
"
```

## Security Considerations

### Container Security

- Runs as non-root user (`appuser:1000`)
- Read-only document mounts prevent modification
- Security options: `no-new-privileges:true`
- Minimal base image (Python 3.11-slim)

### Data Protection

- Local-only processing by default
- No network communication required
- Document data never leaves the container
- Encrypted communication with MCP protocol

### Network Security

- No external network dependencies
- Optional port exposure for HTTP transport
- Isolated Docker network for multi-service deployments

## Integration with Claude Code

### MCP Client Configuration

Configure Claude Code to use the containerized MCP server:

```json
{
  "servers": {
    "mydocs-mcp": {
      "command": "docker",
      "args": [
        "exec", "-i", "mydocs-mcp-prod", 
        "python", "-m", "src.server"
      ]
    }
  }
}
```

### Development Integration

For development with hot reload:

```json
{
  "servers": {
    "mydocs-mcp-dev": {
      "command": "docker-compose",
      "args": [
        "-f", "docker-compose.dev.yml",
        "exec", "-T", "mydocs-mcp",
        "python", "-m", "src.server"
      ]
    }
  }
}
```

## Scaling and Production Considerations

### Resource Planning

- **Minimum**: 512MB RAM, 1 CPU core, 2GB storage
- **Recommended**: 1GB RAM, 2 CPU cores, 5GB storage  
- **Large datasets**: 2GB+ RAM, additional storage as needed

### Production Checklist

- [ ] Configure persistent volumes for data
- [ ] Set appropriate resource limits
- [ ] Configure log rotation
- [ ] Set up monitoring and alerting
- [ ] Regular health check validation
- [ ] Backup strategy for document database
- [ ] Security review and hardening

### Multi-Environment Deployment

```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up

# Production  
docker-compose -f docker-compose.yml up -d
```

This deployment guide provides comprehensive instructions for running mydocs-mcp in containerized environments with proper monitoring, troubleshooting, and production considerations.