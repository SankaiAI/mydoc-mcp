#!/bin/bash
# mydocs-mcp Docker Health Check Script
# Verifies that the MCP server is running and responsive

set -e

# Health check configuration
TIMEOUT=5
DATABASE_PATH=${DATABASE_PATH:-"/app/data/documents.db"}

# Color output for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[HEALTH]${NC} $1"
}

log_error() {
    echo -e "${RED}[HEALTH]${NC} $1" >&2
}

# Function to check if the server process is running
check_server_process() {
    if pgrep -f "python.*src.server" > /dev/null; then
        log_info "Server process is running"
        return 0
    else
        log_error "Server process not found"
        return 1
    fi
}

# Function to check database connectivity
check_database_health() {
    local db_path="$DATABASE_PATH"
    
    # Check if database file exists and is accessible
    if [[ ! -f "$db_path" ]]; then
        log_error "Database file not found: $db_path"
        return 1
    fi
    
    # Test database connection
    if timeout $TIMEOUT python3 -c "
import sqlite3
import sys

try:
    conn = sqlite3.connect('$db_path')
    # Test a simple query
    cursor = conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\" LIMIT 1')
    cursor.fetchone()
    conn.close()
    print('Database health: OK')
    sys.exit(0)
except Exception as e:
    print(f'Database health check failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
        log_info "Database connectivity: OK"
        return 0
    else
        log_error "Database connectivity check failed"
        return 1
    fi
}

# Function to check if data directories are accessible
check_data_directories() {
    local directories=(
        "/app/data"
        "/app/data/documents"
        "/app/data/indexes"
        "/app/data/cache"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_error "Required directory missing: $dir"
            return 1
        fi
        
        if [[ ! -w "$dir" ]]; then
            log_error "Directory not writable: $dir"
            return 1
        fi
    done
    
    log_info "Data directories: OK"
    return 0
}

# Function to check MCP server functionality
check_mcp_functionality() {
    # Test if we can import and initialize core components
    if timeout $TIMEOUT python3 -c "
import sys
sys.path.insert(0, '/app')

try:
    # Test core imports
    from src.config import ServerConfig
    from src.tool_registry import ToolRegistry
    from src.logging_config import setup_logging
    
    # Test basic configuration loading
    config = ServerConfig.from_env()
    registry = ToolRegistry()
    logger = setup_logging('INFO')
    
    print('MCP functionality: OK')
    sys.exit(0)
    
except Exception as e:
    print(f'MCP functionality check failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
        log_info "MCP functionality: OK"
        return 0
    else
        log_error "MCP functionality check failed"
        return 1
    fi
}

# Function to check system resources
check_system_resources() {
    # Check available memory (should have at least 100MB free)
    local free_mem_kb=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo 2>/dev/null || echo "0")
    local free_mem_mb=$((free_mem_kb / 1024))
    
    if [[ $free_mem_mb -lt 100 ]]; then
        log_error "Low memory: ${free_mem_mb}MB available"
        return 1
    fi
    
    # Check available disk space (should have at least 100MB free)
    local free_disk_mb=$(df /app/data 2>/dev/null | awk 'NR==2 {print int($4/1024)}' || echo "0")
    
    if [[ $free_disk_mb -lt 100 ]]; then
        log_error "Low disk space: ${free_disk_mb}MB available in /app/data"
        return 1
    fi
    
    log_info "System resources: OK (Memory: ${free_mem_mb}MB, Disk: ${free_disk_mb}MB)"
    return 0
}

# Main health check function
main() {
    local exit_code=0
    
    log_info "Starting health check..."
    
    # Run all health checks
    check_server_process || exit_code=1
    check_data_directories || exit_code=1
    check_database_health || exit_code=1
    check_mcp_functionality || exit_code=1
    check_system_resources || exit_code=1
    
    if [[ $exit_code -eq 0 ]]; then
        log_info "Health check: PASSED"
    else
        log_error "Health check: FAILED"
    fi
    
    exit $exit_code
}

# Run main health check
main "$@"