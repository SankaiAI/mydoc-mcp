# Claude Code MCP Integration Setup

## Overview
This guide explains how to connect Claude Code to your mydoc-mcp server running in Docker.

## Prerequisites
- Docker Desktop running
- mydoc-mcp container deployed (`mydocs-mcp-prod`)
- Claude Code installed

## Setup Instructions

### 1. Deploy the MCP Server

First, ensure your MCP server is running in Docker:

```bash
# Navigate to project directory
cd D:\AI_Agent_Practice\mydoc-mcp

# Start the container
docker-compose up -d

# Verify it's running
docker ps --filter name=mydocs-mcp-prod

# Check logs to ensure it started correctly
docker logs mydocs-mcp-prod --tail 20
```

### 2. Configure Claude Code

Add the MCP server configuration to your Claude Code settings:

#### Option A: Using Docker Exec (Recommended)

Add this to your Claude Code configuration file (`%APPDATA%\Code\User\claude_code_config.json` on Windows):

```json
{
  "mcpServers": {
    "mydoc-mcp": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mydocs-mcp-prod",
        "python",
        "-m",
        "src.server"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Option B: Using Direct Connection Script

Create a connection script `connect_mcp.bat`:

```batch
@echo off
docker exec -i mydocs-mcp-prod python -m src.server
```

Then configure Claude Code:

```json
{
  "mcpServers": {
    "mydoc-mcp": {
      "command": "D:\\AI_Agent_Practice\\mydoc-mcp\\connect_mcp.bat",
      "args": []
    }
  }
}
```

### 3. Test the Connection

In Claude Code, you should now be able to:

1. Use the MCP tools via commands or chat
2. See available tools: `indexDocument`, `searchDocuments`, `getDocument`
3. Index documents from mounted directories
4. Search indexed documents
5. Retrieve document content

### 4. Available MCP Tools

#### indexDocument
Index a document for searching:
```
Tool: indexDocument
Arguments:
{
  "path": "/documents/example.md",
  "type": "markdown",
  "metadata": {
    "tags": ["documentation", "guide"]
  }
}
```

#### searchDocuments
Search indexed documents:
```
Tool: searchDocuments
Arguments:
{
  "query": "docker setup",
  "limit": 10
}
```

#### getDocument
Retrieve a specific document:
```
Tool: getDocument
Arguments:
{
  "document_id": "doc_123abc"
}
```

## Managing Documents

### Add Documents to Index

1. Place documents in a directory on your host
2. Mount the directory to the container:

```bash
# Stop container
docker-compose down

# Edit docker-compose.yml to add your documents directory
# Under volumes section, add:
#   - /path/to/your/docs:/documents:ro

# Restart container
docker-compose up -d
```

### View Indexed Documents

```bash
# Connect to container
docker exec -it mydocs-mcp-prod bash

# Check database
sqlite3 /app/data/mydocs.db "SELECT id, path, type FROM documents;"
```

## Troubleshooting

### Container Not Running
```bash
# Check container status
docker ps -a --filter name=mydocs-mcp

# View logs
docker logs mydocs-mcp-prod

# Restart container
docker-compose restart
```

### MCP Connection Issues
```bash
# Test MCP server directly
docker exec -it mydocs-mcp-prod python -c "
from src.server import MyDocsMCPServer
import asyncio
server = MyDocsMCPServer()
print('Server initialized successfully')
"

# Check if tools are registered
docker exec -it mydocs-mcp-prod python -c "
from src.tool_registry import get_tool_registry
registry = get_tool_registry()
print('Available tools:', registry.get_tool_names())
"
```

### Permission Issues
```bash
# Fix permissions
docker exec -u root mydocs-mcp-prod chown -R appuser:appuser /app/data
```

## Advanced Configuration

### Custom Document Directories

Edit `docker-compose.yml`:

```yaml
volumes:
  # Add multiple document directories
  - ./docs:/documents/docs:ro
  - ./examples:/documents/examples:ro
  - /path/to/external/docs:/documents/external:ro
```

### Environment Variables

Configure in `docker-compose.yml`:

```yaml
environment:
  - LOG_LEVEL=DEBUG  # For verbose logging
  - MAX_DOCUMENT_SIZE=20971520  # 20MB max file size
  - DATABASE_PATH=/app/data/custom.db  # Custom database location
```

### Resource Limits

Set memory and CPU limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1G
```

## Monitoring

### View Real-time Logs
```bash
docker logs -f mydocs-mcp-prod
```

### Check Resource Usage
```bash
docker stats mydocs-mcp-prod
```

### Database Statistics
```bash
docker exec mydocs-mcp-prod sqlite3 /app/data/mydocs.db "
  SELECT COUNT(*) as total_docs FROM documents;
  SELECT type, COUNT(*) FROM documents GROUP BY type;
"
```

## Backup and Restore

### Backup Database
```bash
docker exec mydocs-mcp-prod sqlite3 /app/data/mydocs.db ".backup /app/data/backup.db"
docker cp mydocs-mcp-prod:/app/data/backup.db ./mydocs_backup.db
```

### Restore Database
```bash
docker cp ./mydocs_backup.db mydocs-mcp-prod:/app/data/restore.db
docker exec mydocs-mcp-prod sqlite3 /app/data/mydocs.db ".restore /app/data/restore.db"
```

## Security Notes

1. The container runs as non-root user (`appuser`)
2. Documents are mounted read-only by default
3. Network isolation via Docker networks
4. No unnecessary ports exposed

## Support

- Check logs: `docker logs mydocs-mcp-prod`
- GitHub Issues: https://github.com/SankaiAI/mydoc-mcp/issues
- Documentation: See project README.md