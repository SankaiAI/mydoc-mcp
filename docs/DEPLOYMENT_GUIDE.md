# mydocs-mcp Deployment Guide

## Overview

This guide covers deploying mydocs-mcp in various environments, from development to production, with Docker and manual installation options.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Configuration](#configuration)
6. [Health Checks](#health-checks)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10, macOS 10.15, Ubuntu 18.04 | Latest versions |
| Python | 3.11.0+ | 3.11.5+ |
| RAM | 512MB | 1GB+ |
| Storage | 1GB free | 5GB+ for large document collections |
| CPU | 1 core | 2+ cores for better performance |

### Dependencies

```bash
# Core dependencies
python-dotenv>=1.0.0
mcp>=1.0.0
aiosqlite>=0.19.0
watchdog>=3.0.0
aiofiles>=23.0.0
pyyaml>=6.0.0

# Optional for enhanced features
uvicorn>=0.23.0  # For HTTP transport (Phase 2)
fastapi>=0.100.0 # For HTTP API (Phase 2)
```

---

## Development Deployment

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourusername/mydocs-mcp.git
cd mydocs-mcp

# 2. Create virtual environment
python -m venv venv

# 3. Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create configuration
cp .env.example .env
# Edit .env with your settings

# 6. Initialize database
python -m src.database.init

# 7. Start server
python -m src.main
```

### Development Configuration

Create `.env` file:

```ini
# Development settings
TRANSPORT=stdio
LOG_LEVEL=DEBUG
DEBUG_MODE=true

# Paths
DATABASE_URL=sqlite:///data/dev_mydocs.db
DOCUMENT_ROOT=./examples/sample_documents
LOG_FILE=logs/mydocs-dev.log

# Performance
CACHE_TTL=60
MAX_SEARCH_RESULTS=50

# File watching
WATCH_ENABLED=true
WATCH_DEBOUNCE=1
```

---

## Production Deployment

### Manual Installation

```bash
# 1. Create production user
sudo useradd -r -s /bin/false mydocs
sudo mkdir -p /opt/mydocs-mcp
sudo chown mydocs:mydocs /opt/mydocs-mcp

# 2. Install application
cd /opt/mydocs-mcp
sudo -u mydocs git clone https://repo/mydocs-mcp.git .
sudo -u mydocs python -m venv venv
sudo -u mydocs ./venv/bin/pip install -r requirements.txt

# 3. Create directories
sudo -u mydocs mkdir -p data logs

# 4. Configure environment
sudo -u mydocs cp .env.production .env
# Edit configuration as needed

# 5. Set up systemd service (see below)
```

### Production Configuration

```ini
# Production settings
TRANSPORT=stdio
LOG_LEVEL=INFO
DEBUG_MODE=false

# Paths
DATABASE_URL=sqlite:///opt/mydocs-mcp/data/mydocs.db
DOCUMENT_ROOT=/home/user/Documents
LOG_FILE=/opt/mydocs-mcp/logs/mydocs.log

# Performance
CACHE_TTL=3600
MAX_SEARCH_RESULTS=20
ENABLE_METRICS=true

# Security
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=1000

# File watching
WATCH_ENABLED=true
WATCH_DEBOUNCE=5
IGNORED_PATTERNS=*.tmp,.*,*.swp
```

### Systemd Service

Create `/etc/systemd/system/mydocs-mcp.service`:

```ini
[Unit]
Description=mydocs-mcp MCP Server
After=network.target

[Service]
Type=simple
User=mydocs
Group=mydocs
WorkingDirectory=/opt/mydocs-mcp
Environment=PATH=/opt/mydocs-mcp/venv/bin
ExecStart=/opt/mydocs-mcp/venv/bin/python -m src.main
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

# Resource limits
LimitNOFILE=65536
MemoryMax=1G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mydocs-mcp
sudo systemctl start mydocs-mcp
sudo systemctl status mydocs-mcp
```

---

## Docker Deployment

### Development with Docker

```bash
# Build development image
docker build -f Dockerfile.dev -t mydocs-mcp:dev .

# Run development container
docker run -it --rm \
  -v ./data:/app/data \
  -v ./documents:/app/documents:ro \
  -v ./logs:/app/logs \
  mydocs-mcp:dev
```

### Production with Docker

```bash
# Build production image
docker build -t mydocs-mcp:latest .

# Run production container
docker run -d \
  --name mydocs-mcp \
  --restart unless-stopped \
  -v /opt/mydocs/data:/app/data \
  -v /home/user/Documents:/app/documents:ro \
  -v /var/log/mydocs:/app/logs \
  -e DOCUMENT_ROOT=/app/documents \
  -e LOG_LEVEL=INFO \
  mydocs-mcp:latest
```

### Docker Compose Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  mydocs-mcp:
    image: mydocs-mcp:latest
    container_name: mydocs-mcp
    restart: unless-stopped
    
    environment:
      - TRANSPORT=stdio
      - LOG_LEVEL=INFO
      - DATABASE_URL=sqlite:///app/data/mydocs.db
      - DOCUMENT_ROOT=/app/documents
      - CACHE_TTL=3600
      
    volumes:
      - ./data:/app/data
      - /home/user/Documents:/app/documents:ro
      - ./logs:/app/logs
      
    healthcheck:
      test: ["CMD", "python", "-m", "src.health_check"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
      
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 256M
          cpus: '0.25'
```

```bash
# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale if needed
docker-compose -f docker-compose.prod.yml up -d --scale mydocs-mcp=2
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRANSPORT` | stdio | MCP transport protocol |
| `LOG_LEVEL` | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `DEBUG_MODE` | false | Enable debug features |
| `DATABASE_URL` | sqlite:///data/mydocs.db | Database connection string |
| `DOCUMENT_ROOT` | ./documents | Root directory for documents |
| `LOG_FILE` | logs/mydocs.log | Log file path |
| `CACHE_TTL` | 300 | Cache time-to-live in seconds |
| `MAX_SEARCH_RESULTS` | 20 | Maximum search results to return |
| `WATCH_ENABLED` | true | Enable file system watching |
| `WATCH_DEBOUNCE` | 2 | File watch debounce delay in seconds |
| `IGNORED_PATTERNS` | *.tmp,.* | Patterns to ignore when watching |

### Database Configuration

```python
# SQLite optimizations for production
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = memory;
PRAGMA mmap_size = 268435456;
```

### Logging Configuration

Production logging in `/opt/mydocs-mcp/config/logging.yml`:

```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  json:
    format: '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'

handlers:
  console:
    class: logging.StreamHandler
    formatter: standard
    level: INFO
    
  file:
    class: logging.handlers.RotatingFileHandler
    filename: logs/mydocs.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
    formatter: json
    level: INFO

loggers:
  mydocs-mcp:
    level: INFO
    handlers: [console, file]
    propagate: false
    
root:
  level: INFO
  handlers: [console, file]
```

---

## Health Checks

### Built-in Health Check

Create `src/health_check.py`:

```python
#!/usr/bin/env python3
"""Health check script for mydocs-mcp."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import DatabaseConnection
from src.config import ServerConfig

async def health_check():
    """Perform health check."""
    try:
        # Check configuration
        config = ServerConfig()
        
        # Check database connection
        db = DatabaseConnection(config.database_url.replace("sqlite:///", ""))
        await db.connect()
        
        # Check document root
        if not Path(config.document_root).exists():
            raise Exception("Document root not accessible")
        
        print("Health check: OK")
        return 0
        
    except Exception as e:
        print(f"Health check: FAILED - {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(health_check()))
```

### External Health Monitoring

```bash
# Cron job for health monitoring
*/5 * * * * /opt/mydocs-mcp/venv/bin/python /opt/mydocs-mcp/src/health_check.py || echo "mydocs-mcp health check failed" | mail -s "Service Alert" admin@example.com
```

---

## Monitoring

### Metrics Collection

Enable metrics in production:

```ini
ENABLE_METRICS=true
METRICS_PORT=9090
METRICS_PATH=/metrics
```

### Log Analysis

```bash
# Monitor error rates
grep "ERROR\|CRITICAL" /opt/mydocs-mcp/logs/mydocs.log | tail -50

# Monitor performance
grep "performance" /opt/mydocs-mcp/logs/mydocs.log | grep -E "search_time|index_time" | tail -20

# Monitor database operations
grep "database" /opt/mydocs-mcp/logs/mydocs.log | tail -30
```

### Grafana Dashboard

Example metrics to monitor:
- Request rate (requests/second)
- Response time (P50, P95, P99)
- Error rate (%)
- Database query time
- File system watcher events
- Memory usage
- Cache hit/miss ratio

---

## Troubleshooting

### Common Deployment Issues

#### Permission Denied
```bash
# Fix file permissions
sudo chown -R mydocs:mydocs /opt/mydocs-mcp
sudo chmod -R 755 /opt/mydocs-mcp
sudo chmod 644 /opt/mydocs-mcp/data/*
```

#### Database Lock Issues
```bash
# Check for zombie processes
ps aux | grep mydocs
kill -9 <pid>

# Reset database permissions
sudo chown mydocs:mydocs /opt/mydocs-mcp/data/mydocs.db*
```

#### High Memory Usage
```bash
# Monitor memory usage
watch -n 5 'ps -p $(pgrep -f mydocs-mcp) -o pid,ppid,%mem,rss,vsz,command'

# Restart service if needed
sudo systemctl restart mydocs-mcp
```

#### Document Not Indexing
```bash
# Check file permissions
ls -la $DOCUMENT_ROOT

# Force reindex
sudo -u mydocs /opt/mydocs-mcp/venv/bin/python -c "
from src.tools.reindex import force_reindex
import asyncio
asyncio.run(force_reindex('/path/to/doc'))
"
```

### Performance Tuning

#### Database Optimization
```sql
-- Run monthly
PRAGMA optimize;
VACUUM;
ANALYZE;
```

#### File System Optimization
```bash
# For large document collections
echo 'fs.inotify.max_user_watches=524288' >> /etc/sysctl.conf
sysctl -p
```

### Backup and Recovery

```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/opt/backups/mydocs-mcp"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp /opt/mydocs-mcp/data/mydocs.db $BACKUP_DIR/mydocs_$DATE.db

# Backup configuration
cp /opt/mydocs-mcp/.env $BACKUP_DIR/env_$DATE

# Compress old backups
find $BACKUP_DIR -name "*.db" -mtime +7 -exec gzip {} \;
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

---

## Security Considerations

### File System Security
- Run as non-privileged user
- Restrict file permissions (644 for files, 755 for directories)
- Use read-only mounts for document directories

### Network Security
- Use stdio transport for local deployment
- Implement rate limiting for future HTTP transport
- Monitor for unusual access patterns

### Data Security
- Enable database encryption (SQLite with SQLCipher)
- Regular security updates
- Audit file access logs

---

## Scaling Considerations

### Horizontal Scaling
- Use load balancer for multiple instances
- Shared file system (NFS/GlusterFS)
- Distributed caching (Redis)

### Vertical Scaling
- Increase memory for larger document collections
- SSD storage for better I/O performance
- More CPU cores for concurrent operations

---

*Last Updated: September 4, 2025*
*Version: 1.0*