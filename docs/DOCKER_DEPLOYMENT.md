# Docker Deployment Guide for mydoc-mcp

## Prerequisites
- Docker Engine 20.10+ installed
- Docker Compose 2.0+ installed (optional, for docker-compose deployment)
- At least 2GB of available RAM
- 1GB of available disk space

## Quick Start

### 1. Build the Docker Image

```bash
# Clone the repository
git clone https://github.com/SankaiAI/mydoc-mcp.git
cd mydoc-mcp

# Build the production image
docker build -t mydoc-mcp:latest --target production .
```

### 2. Run the Container

#### Basic Run
```bash
docker run -d \
  --name mydoc-mcp \
  -v $(pwd)/data:/app/data \
  -v /path/to/your/documents:/documents:ro \
  -e LOG_LEVEL=INFO \
  mydoc-mcp:latest
```

#### With Custom Configuration
```bash
docker run -d \
  --name mydoc-mcp \
  -v $(pwd)/data:/app/data \
  -v /path/to/your/documents:/documents:ro \
  -v $(pwd)/config:/app/config:ro \
  -e LOG_LEVEL=DEBUG \
  -e DATABASE_PATH=/app/data/documents.db \
  -e MAX_DOCUMENT_SIZE=20971520 \
  --restart unless-stopped \
  mydoc-mcp:latest
```

## Docker Compose Deployment

### 1. Using the Default Configuration

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f mydocs-mcp

# Stop the service
docker-compose down
```

### 2. With Environment Variables

Create a `.env` file:
```env
DOCUMENT_PATH=/path/to/your/documents
CONFIG_PATH=./config
LOG_LEVEL=INFO
```

Then run:
```bash
docker-compose --env-file .env up -d
```

### 3. Development Mode

```bash
# Use the development compose file
docker-compose -f docker-compose.dev.yml up -d

# This enables:
# - Hot reload on code changes
# - Debug logging
# - Volume mounts for source code
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_TRANSPORT` | Transport protocol | `stdio` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `DATABASE_PATH` | Path to SQLite database | `/app/data/documents.db` |
| `DOCUMENT_DIRECTORIES` | Directories to scan for documents | `/documents` |
| `MAX_DOCUMENT_SIZE` | Maximum document size in bytes | `10485760` (10MB) |
| `PYTHONUNBUFFERED` | Python output buffering | `1` |

## Volume Mounts

### Required Volumes

- `/app/data` - Persistent data storage (database, indexes, cache)
- `/documents` - Your document directories (read-only recommended)

### Optional Volumes

- `/app/config` - Custom configuration files
- `/app/logs` - Application logs (if not using Docker logging)

## Health Checks

The container includes built-in health checks:

```bash
# Check container health
docker ps --filter name=mydoc-mcp --format "table {{.Names}}\t{{.Status}}"

# View health check logs
docker exec mydoc-mcp /app/scripts/docker-healthcheck.sh
```

## Resource Limits

### Production Recommendations

```yaml
# docker-compose.yml
services:
  mydocs-mcp:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
```

### Docker Run with Limits

```bash
docker run -d \
  --name mydoc-mcp \
  --memory="1g" \
  --memory-reservation="256m" \
  --cpus="2.0" \
  -v $(pwd)/data:/app/data \
  -v /documents:/documents:ro \
  mydoc-mcp:latest
```

## Networking

### Expose MCP Server (Future HTTP Transport)

```bash
docker run -d \
  --name mydoc-mcp \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v /documents:/documents:ro \
  mydoc-mcp:latest
```

### Custom Network

```bash
# Create network
docker network create mydocs-network

# Run container in network
docker run -d \
  --name mydoc-mcp \
  --network mydocs-network \
  -v $(pwd)/data:/app/data \
  -v /documents:/documents:ro \
  mydoc-mcp:latest
```

## Monitoring and Logging

### View Logs

```bash
# Follow logs
docker logs -f mydoc-mcp

# Last 100 lines
docker logs --tail 100 mydoc-mcp

# Logs since timestamp
docker logs --since 2025-01-01T00:00:00 mydoc-mcp
```

### Log Rotation

Configure in `docker-compose.yml`:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Monitoring Commands

```bash
# Container statistics
docker stats mydoc-mcp

# Inspect container
docker inspect mydoc-mcp

# Execute commands inside container
docker exec -it mydoc-mcp bash

# Check Python packages
docker exec mydoc-mcp pip list
```

## Backup and Restore

### Backup Data

```bash
# Stop container
docker stop mydoc-mcp

# Backup data volume
tar -czf mydoc-mcp-backup-$(date +%Y%m%d).tar.gz \
  -C $(docker inspect mydoc-mcp | jq -r '.[0].Mounts[] | select(.Destination=="/app/data") | .Source') .

# Restart container
docker start mydoc-mcp
```

### Restore Data

```bash
# Stop container
docker stop mydoc-mcp

# Restore backup
tar -xzf mydoc-mcp-backup-20250101.tar.gz \
  -C $(docker inspect mydoc-mcp | jq -r '.[0].Mounts[] | select(.Destination=="/app/data") | .Source')

# Start container
docker start mydoc-mcp
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs mydoc-mcp

# Check exit code
docker inspect mydoc-mcp --format='{{.State.ExitCode}}'

# Run in foreground for debugging
docker run --rm -it \
  -v $(pwd)/data:/app/data \
  -v /documents:/documents:ro \
  -e LOG_LEVEL=DEBUG \
  mydoc-mcp:latest
```

### Permission Issues

```bash
# Fix data directory permissions
docker exec mydoc-mcp chown -R appuser:appuser /app/data

# Run as root for debugging (not recommended for production)
docker run --user root -it mydoc-mcp:latest bash
```

### Database Issues

```bash
# Check database integrity
docker exec mydoc-mcp python -c "
import sqlite3
conn = sqlite3.connect('/app/data/documents.db')
print('Database OK')
conn.close()
"

# Reset database (WARNING: Deletes all data)
docker exec mydoc-mcp rm -f /app/data/documents.db
docker restart mydoc-mcp
```

### Memory Issues

```bash
# Check memory usage
docker stats mydoc-mcp --no-stream

# Increase memory limit
docker update --memory="2g" --memory-reservation="512m" mydoc-mcp
```

## Security Best Practices

1. **Run as non-root user** (default: appuser)
2. **Mount documents as read-only** (`:ro` flag)
3. **Use secrets for sensitive data**:
   ```bash
   docker secret create db_password ./password.txt
   docker service create --secret db_password mydoc-mcp:latest
   ```
4. **Enable security options**:
   ```bash
   docker run --security-opt no-new-privileges:true mydoc-mcp:latest
   ```
5. **Regular updates**:
   ```bash
   docker pull mydoc-mcp:latest
   docker-compose pull
   ```

## Multi-Stage Build Options

### Development Build
```bash
docker build -t mydoc-mcp:dev --target development .
```

### Production Build (Default)
```bash
docker build -t mydoc-mcp:latest --target production .
```

### Base Image Only
```bash
docker build -t mydoc-mcp:base --target base .
```

## Kubernetes Deployment

For Kubernetes deployment, see the `k8s/` directory:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/configmap.yaml
```

## Support

- GitHub Issues: https://github.com/SankaiAI/mydoc-mcp/issues
- Documentation: https://github.com/SankaiAI/mydoc-mcp/wiki
- Docker Hub: https://hub.docker.com/r/sankaiai/mydoc-mcp

## Version Information

- Base Image: `python:3.11-slim-bullseye`
- MCP Protocol: Latest
- Application: mydoc-mcp v1.0.0