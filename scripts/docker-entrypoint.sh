#!/bin/bash
# mydocs-mcp Docker Entrypoint Script
# Handles container initialization and graceful startup

set -e

# Color output for better logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Function to check if directory exists and create if needed
ensure_directory() {
    local dir=$1
    local description=$2
    
    if [[ ! -d "$dir" ]]; then
        log_info "Creating $description directory: $dir"
        mkdir -p "$dir"
        chown appuser:appuser "$dir" 2>/dev/null || true
    else
        log_info "$description directory exists: $dir"
    fi
}

# Function to validate environment variables
validate_environment() {
    log_info "Validating environment configuration"
    
    # Set default values if not provided
    export MCP_TRANSPORT=${MCP_TRANSPORT:-"stdio"}
    export LOG_LEVEL=${LOG_LEVEL:-"INFO"}
    export DATABASE_PATH=${DATABASE_PATH:-"/app/data/documents.db"}
    export DOCUMENT_DIRECTORIES=${DOCUMENT_DIRECTORIES:-"/documents"}
    export MAX_DOCUMENT_SIZE=${MAX_DOCUMENT_SIZE:-"10485760"}  # 10MB default
    
    log_info "Configuration:"
    log_info "  Transport: $MCP_TRANSPORT"
    log_info "  Log Level: $LOG_LEVEL"
    log_info "  Database: $DATABASE_PATH"
    log_info "  Document Directories: $DOCUMENT_DIRECTORIES"
}

# Function to initialize data directories
initialize_directories() {
    log_info "Initializing data directories"
    
    # Ensure required directories exist
    ensure_directory "/app/data" "application data"
    ensure_directory "/app/data/documents" "document storage"
    ensure_directory "/app/data/indexes" "search indexes"
    ensure_directory "/app/data/cache" "application cache"
    ensure_directory "/app/data/logs" "application logs"
    
    # Ensure document mount point exists
    ensure_directory "/documents" "document mount point"
    
    # Set proper permissions
    if [[ $(id -u) -eq 0 ]]; then
        chown -R appuser:appuser /app/data /documents 2>/dev/null || true
    fi
}

# Function to check database connectivity
check_database() {
    log_info "Checking database connectivity"
    
    # Check if we can create/access the database file
    local db_dir=$(dirname "$DATABASE_PATH")
    
    if [[ ! -d "$db_dir" ]]; then
        log_warn "Database directory doesn't exist, creating: $db_dir"
        mkdir -p "$db_dir"
        chown appuser:appuser "$db_dir" 2>/dev/null || true
    fi
    
    # Test database access with a simple Python check
    python3 -c "
import sqlite3
import sys
import os

try:
    db_path = '$DATABASE_PATH'
    db_dir = os.path.dirname(db_path)
    
    # Check if we can write to the directory
    if not os.access(db_dir, os.W_OK):
        print('ERROR: Cannot write to database directory: $db_dir', file=sys.stderr)
        sys.exit(1)
        
    # Test database connection
    conn = sqlite3.connect(db_path)
    conn.execute('SELECT 1')
    conn.close()
    print('Database connectivity: OK')
    
except Exception as e:
    print(f'Database connectivity check failed: {e}', file=sys.stderr)
    sys.exit(1)
" || {
        log_error "Database connectivity check failed"
        exit 1
    }
    
    log_info "Database connectivity: OK"
}

# Function to run pre-flight checks
run_preflight_checks() {
    log_info "Running pre-flight checks"
    
    # Check Python version
    python3 --version || {
        log_error "Python 3 not available"
        exit 1
    }
    
    # Check if MCP package is available
    python3 -c "import mcp; print(f'MCP version: {mcp.__version__}')" || {
        log_error "MCP package not available"
        exit 1
    }
    
    # Check if source code is available
    if [[ ! -f "/app/src/server.py" ]]; then
        log_error "Application source code not found"
        exit 1
    fi
    
    log_info "Pre-flight checks: OK"
}

# Function to handle graceful shutdown
cleanup() {
    log_info "Received shutdown signal, cleaning up..."
    
    # Kill background processes if any
    jobs -p | xargs -r kill 2>/dev/null || true
    
    log_info "Cleanup complete, exiting"
    exit 0
}

# Set up signal handlers for graceful shutdown
trap cleanup SIGTERM SIGINT

# Main initialization function
main() {
    log_info "mydocs-mcp container starting..."
    
    # Run initialization steps
    validate_environment
    initialize_directories
    check_database
    run_preflight_checks
    
    log_info "Container initialization complete"
    log_info "Starting mydocs-mcp server with command: $*"
    
    # Execute the main command
    exec "$@"
}

# Run main function with all arguments
main "$@"