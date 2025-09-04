# mydocs-mcp Troubleshooting Guide

## Quick Diagnosis

### Is the Server Running?
```bash
# Check if process is running
ps aux | grep mydocs-mcp

# Check logs for startup messages
tail -f logs/mydocs-mcp.log

# Test basic connectivity
python tests/test_mcp_validation.py
```

### Is Claude Code Connected?
```bash
# Check Claude Code MCP status
# In Claude Code, type: "List available MCP tools"

# Expected response should include:
# - indexDocument
# - searchDocuments  
# - getDocument
```

---

## Common Issues and Solutions

### 1. Server Won't Start

#### Problem: `ModuleNotFoundError: No module named 'mcp'`
```bash
# Solution: Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep mcp
```

#### Problem: `Permission denied` on database file
```bash
# Solution: Fix permissions
chmod 755 data/
chmod 644 data/mydocs.db

# Or for Docker
docker run --user $(id -u):$(id -g) mydocs-mcp
```

#### Problem: `Port already in use`
```bash
# Solution: Kill existing process
ps aux | grep mydocs
kill <pid>

# Or change port in configuration
export TRANSPORT_PORT=3001
```

#### Problem: `Python version too old`
```bash
# Check version
python --version  # Must be 3.11+

# Update Python
# Windows: Download from python.org
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
```

---

### 2. Database Issues

#### Problem: `Database is locked`
```bash
# Solution 1: Check for zombie processes
ps aux | grep mydocs
kill -9 <pid>

# Solution 2: Remove lock file
rm data/mydocs.db-wal
rm data/mydocs.db-shm

# Solution 3: Recreate database
mv data/mydocs.db data/mydocs.db.backup
python -m src.database.init
```

#### Problem: `No such table: documents`
```bash
# Solution: Initialize database schema
python -c "
import asyncio
from src.database.connection import DatabaseConnection
async def init():
    db = DatabaseConnection('data/mydocs.db')
    await db.connect()
asyncio.run(init())
"
```

#### Problem: Slow database queries
```bash
# Solution: Optimize database
python -c "
import sqlite3
conn = sqlite3.connect('data/mydocs.db')
conn.execute('PRAGMA optimize')
conn.execute('VACUUM')
conn.execute('ANALYZE')
conn.close()
"
```

---

### 3. Document Indexing Issues

#### Problem: Documents not being indexed
```bash
# Check document root exists
ls -la $DOCUMENT_ROOT

# Check file permissions
find $DOCUMENT_ROOT -name "*.md" -exec ls -l {} \;

# Force manual indexing
python -c "
import asyncio
from src.tools.indexDocument import IndexDocumentTool
from src.database.manager import DocumentManager
from src.parsers.parser_factory import ParserFactory

async def test_index():
    dm = DocumentManager('data/mydocs.db')
    pf = ParserFactory()
    tool = IndexDocumentTool(dm, pf)
    result = await tool.execute({'file_path': '/path/to/test.md'})
    print(result)

asyncio.run(test_index())
"
```

#### Problem: File watcher not working
```bash
# Check if watchdog is installed
pip list | grep watchdog

# Check system limits (Linux)
cat /proc/sys/fs/inotify/max_user_watches

# Increase limit if needed
echo 'fs.inotify.max_user_watches=524288' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Test file watcher manually
python -c "
from src.watcher.file_watcher import FileWatcher
import asyncio

async def test():
    watcher = FileWatcher('./documents')
    await watcher.start()

asyncio.run(test())
"
```

#### Problem: Parsing errors for specific files
```bash
# Test parser directly
python -c "
import asyncio
from src.parsers.parser_factory import ParserFactory

async def test_parse():
    factory = ParserFactory()
    parser = factory.get_parser('/path/to/problematic/file.md')
    result = await parser.parse('/path/to/problematic/file.md')
    print(result)

asyncio.run(test_parse())
"
```

---

### 4. Search Issues

#### Problem: Search returns no results
```bash
# Check if documents are indexed
python -c "
import asyncio
import sqlite3

def check_index():
    conn = sqlite3.connect('data/mydocs.db')
    count = conn.execute('SELECT COUNT(*) FROM documents').fetchone()[0]
    print(f'Documents indexed: {count}')
    
    if count > 0:
        sample = conn.execute('SELECT file_path, title FROM documents LIMIT 5').fetchall()
        print('Sample documents:')
        for row in sample:
            print(f'  - {row[1]} ({row[0]})')
    conn.close()

check_index()
"

# Force reindex all documents
find $DOCUMENT_ROOT -name "*.md" -exec python -c "
import asyncio
import sys
from src.tools.indexDocument import IndexDocumentTool
from src.database.manager import DocumentManager
from src.parsers.parser_factory import ParserFactory

async def index_file(path):
    dm = DocumentManager('data/mydocs.db')
    pf = ParserFactory()
    tool = IndexDocumentTool(dm, pf)
    result = await tool.execute({'file_path': path})
    print(f'Indexed: {path}')

asyncio.run(index_file(sys.argv[1]))
" {} \;
```

#### Problem: Search is too slow
```bash
# Check database size
ls -lh data/mydocs.db

# Check query performance
python -c "
import asyncio
import time
from src.tools.searchDocuments import SearchDocumentsTool
from src.database.manager import DocumentManager

async def test_search():
    dm = DocumentManager('data/mydocs.db')
    tool = SearchDocumentsTool(dm)
    
    start = time.time()
    result = await tool.execute({'query': 'test'})
    elapsed = (time.time() - start) * 1000
    
    print(f'Search took: {elapsed:.2f}ms')
    print(f'Results: {len(result.get(\"results\", []))}')

asyncio.run(test_search())
"

# Optimize database if slow
python -c "
import sqlite3
conn = sqlite3.connect('data/mydocs.db')
conn.execute('PRAGMA optimize')
conn.execute('VACUUM')
conn.close()
print('Database optimized')
"
```

#### Problem: Search results not relevant
```bash
# Check search algorithm settings
grep -r "TF_IDF\|relevance" src/

# Test search manually
python -c "
import asyncio
from src.tools.searchDocuments import SearchDocumentsTool
from src.database.manager import DocumentManager

async def debug_search():
    dm = DocumentManager('data/mydocs.db')
    tool = SearchDocumentsTool(dm)
    
    result = await tool.execute({
        'query': 'API design',
        'limit': 5,
        'include_content': True
    })
    
    for r in result.get('results', []):
        print(f'{r[\"title\"]}: {r[\"relevance_score\"]:.3f}')
        print(f'  Snippet: {r[\"snippet\"][:100]}...')

asyncio.run(debug_search())
"
```

---

### 5. Claude Code Integration Issues

#### Problem: Claude Code can't find MCP server
```bash
# Check Claude Code MCP configuration
# Should be in ~/.config/claude-code/settings.json or similar

# Verify MCP server path
which python
ls -la $(which python)

# Test MCP protocol manually
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | python -m src.main
```

#### Problem: Tools not showing up in Claude Code
```bash
# Test tool registry
python -c "
from src.tool_registry import ToolRegistry
registry = ToolRegistry()

# Register tools manually
from src.tools.indexDocument import IndexDocumentTool
from src.tools.searchDocuments import SearchDocumentsTool  
from src.tools.getDocument import GetDocumentTool
from src.database.manager import DocumentManager
from src.parsers.parser_factory import ParserFactory

dm = DocumentManager('data/mydocs.db')
pf = ParserFactory()

tools = [
    IndexDocumentTool(dm, pf),
    SearchDocumentsTool(dm),
    GetDocumentTool(dm)
]

for tool in tools:
    registry.register_tool(
        name=tool.name,
        handler=tool.execute,
        description=tool.description,
        input_schema=tool.input_schema
    )

print('Registered tools:', registry.get_tool_names())
available = registry.get_available_tools()
for tool in available:
    print(f'- {tool[\"name\"]}: {tool[\"description\"]}')
"
```

#### Problem: MCP protocol errors
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m src.main

# Check MCP message format
python -c "
import json
message = {
    'jsonrpc': '2.0',
    'method': 'tools/call',
    'params': {
        'name': 'searchDocuments',
        'arguments': {'query': 'test'}
    },
    'id': 1
}
print(json.dumps(message, indent=2))
"
```

---

### 6. Performance Issues

#### Problem: Operations taking longer than 200ms
```bash
# Enable performance monitoring
export LOG_LEVEL=DEBUG
export DEBUG_MODE=true

# Run performance test
python tests/test_performance.py

# Profile slow operations
python -c "
import asyncio
import cProfile
import pstats
from src.tools.searchDocuments import SearchDocumentsTool
from src.database.manager import DocumentManager

async def profile_search():
    dm = DocumentManager('data/mydocs.db')
    tool = SearchDocumentsTool(dm)
    
    pr = cProfile.Profile()
    pr.enable()
    
    result = await tool.execute({'query': 'test query'})
    
    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats(10)

asyncio.run(profile_search())
"
```

#### Problem: High memory usage
```bash
# Monitor memory usage
watch -n 5 'ps -p $(pgrep -f mydocs) -o pid,ppid,%mem,rss,vsz,command'

# Check for memory leaks
python -c "
import gc
import psutil
import asyncio
from src.server import MyDocsMCPServer
from src.config import ServerConfig

async def memory_test():
    config = ServerConfig()
    server = MyDocsMCPServer(config)
    
    process = psutil.Process()
    start_memory = process.memory_info().rss / 1024 / 1024
    
    # Simulate load
    for i in range(100):
        # Perform operations
        pass
        
    gc.collect()
    end_memory = process.memory_info().rss / 1024 / 1024
    print(f'Memory usage: {start_memory:.1f}MB -> {end_memory:.1f}MB')

asyncio.run(memory_test())
"
```

---

### 7. Docker Issues

#### Problem: Container won't start
```bash
# Check Docker logs
docker logs mydocs-mcp

# Run interactive debug session
docker run -it --rm mydocs-mcp:latest /bin/bash

# Check container health
docker exec mydocs-mcp python src/health_check.py
```

#### Problem: Volume mounting issues
```bash
# Check volume permissions
ls -la /path/to/host/documents
docker exec mydocs-mcp ls -la /app/documents

# Fix permissions
sudo chown -R 1000:1000 /path/to/host/documents
# Or
docker run --user $(id -u):$(id -g) mydocs-mcp
```

#### Problem: Environment variables not working
```bash
# Check environment inside container
docker exec mydocs-mcp env | grep DOCUMENT_ROOT

# Override environment
docker run -e DOCUMENT_ROOT=/app/docs mydocs-mcp
```

---

## Diagnostic Scripts

### Health Check Script
```bash
#!/bin/bash
# save as scripts/health_check.sh

echo "=== mydocs-mcp Health Check ==="

# Check Python version
echo "Python version:"
python --version

# Check dependencies
echo "Checking dependencies..."
python -c "
try:
    import mcp, aiosqlite, watchdog, aiofiles, yaml
    print('✓ All dependencies installed')
except ImportError as e:
    print(f'✗ Missing dependency: {e}')
"

# Check database
echo "Checking database..."
if [ -f "data/mydocs.db" ]; then
    echo "✓ Database exists"
    python -c "
import sqlite3
try:
    conn = sqlite3.connect('data/mydocs.db')
    count = conn.execute('SELECT COUNT(*) FROM documents').fetchone()[0]
    print(f'✓ Database accessible, {count} documents indexed')
    conn.close()
except Exception as e:
    print(f'✗ Database error: {e}')
"
else
    echo "✗ Database not found"
fi

# Check document root
echo "Checking document root..."
if [ -d "${DOCUMENT_ROOT:-./documents}" ]; then
    count=$(find "${DOCUMENT_ROOT:-./documents}" -name "*.md" -o -name "*.txt" | wc -l)
    echo "✓ Document root exists, $count documents found"
else
    echo "✗ Document root not found"
fi

# Test server startup
echo "Testing server startup..."
timeout 10 python -m src.main --version && echo "✓ Server can start" || echo "✗ Server startup failed"

echo "=== Health Check Complete ==="
```

### Performance Benchmark Script
```bash
#!/bin/bash
# save as scripts/benchmark.sh

echo "=== Performance Benchmark ==="

python -c "
import asyncio
import time
import statistics
from src.tools.indexDocument import IndexDocumentTool
from src.tools.searchDocuments import SearchDocumentsTool
from src.tools.getDocument import GetDocumentTool
from src.database.manager import DocumentManager
from src.parsers.parser_factory import ParserFactory

async def benchmark():
    dm = DocumentManager('data/mydocs.db')
    pf = ParserFactory()
    
    # Benchmark search
    search_tool = SearchDocumentsTool(dm)
    search_times = []
    
    for i in range(10):
        start = time.time()
        await search_tool.execute({'query': f'test query {i}'})
        search_times.append((time.time() - start) * 1000)
    
    print(f'Search performance:')
    print(f'  Average: {statistics.mean(search_times):.1f}ms')
    print(f'  Median:  {statistics.median(search_times):.1f}ms')
    print(f'  95th %:  {sorted(search_times)[int(len(search_times)*0.95)]:.1f}ms')
    print(f'  Target:  <200ms')
    
    # Benchmark retrieval
    get_tool = GetDocumentTool(dm)
    get_times = []
    
    # Get sample document IDs
    import sqlite3
    conn = sqlite3.connect('data/mydocs.db')
    doc_ids = [row[0] for row in conn.execute('SELECT id FROM documents LIMIT 10').fetchall()]
    conn.close()
    
    for doc_id in doc_ids:
        start = time.time()
        await get_tool.execute({'document_id': doc_id})
        get_times.append((time.time() - start) * 1000)
    
    if get_times:
        print(f'Retrieval performance:')
        print(f'  Average: {statistics.mean(get_times):.1f}ms')
        print(f'  Median:  {statistics.median(get_times):.1f}ms')
        print(f'  Target:  <200ms')

asyncio.run(benchmark())
"
```

---

## Getting Help

### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
export DEBUG_MODE=true
python -m src.main
```

### Collect Diagnostic Information
```bash
# System info
uname -a
python --version
pip list

# mydocs-mcp info
git log --oneline -5
ls -la data/
tail -50 logs/mydocs-mcp.log

# Configuration
cat .env
env | grep MYDOCS
```

### Report Issues

When reporting issues, include:

1. **Environment Information**
   - OS and version
   - Python version
   - mydocs-mcp version/commit

2. **Configuration**
   - .env file (redacted)
   - Command used to start server
   - Docker/manual installation

3. **Error Details**
   - Complete error message
   - Stack trace
   - Log file excerpts

4. **Reproduction Steps**
   - Exact steps to reproduce
   - Expected vs actual behavior
   - Minimal test case

---

*Last Updated: September 4, 2025*
*Version: 1.0*