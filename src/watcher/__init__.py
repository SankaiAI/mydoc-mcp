"""
File system watcher module for mydocs-mcp.

This module provides file system monitoring capabilities that automatically
detect changes to document files and trigger appropriate indexing operations.

Key Components:
- FileWatcher: Main watcher class that coordinates monitoring and indexing
- WatcherConfig: Configuration management for watch directories and settings  
- AsyncFileSystemEventHandler: Async-compatible event processing
- FileEvent: Structured representation of file system events

Usage:
    from src.watcher import FileWatcher, WatcherConfig
    
    # Create configuration
    config = WatcherConfig(
        watch_directories=["/path/to/documents"],
        watched_extensions={'.md', '.txt'},
        debounce_delay_ms=500
    )
    
    # Initialize and start watcher
    watcher = FileWatcher(config=config)
    await watcher.start()
    
    # Stop when done
    await watcher.stop()
"""

from .config import (
    WatcherConfig,
    create_watcher_config,
    load_watcher_config_from_env
)
from .event_handler import (
    AsyncFileSystemEventHandler,
    FileEvent
)
from .file_watcher import FileWatcher

# Public API
__all__ = [
    'FileWatcher',
    'WatcherConfig',
    'create_watcher_config',
    'load_watcher_config_from_env',
    'AsyncFileSystemEventHandler',
    'FileEvent'
]

# Version info
__version__ = "1.0.0"
__author__ = "mydocs-mcp"
__description__ = "File system watcher with automatic document indexing"


def create_default_watcher(
    index_tool=None,
    database_manager=None,
    logger=None,
    **config_overrides
) -> FileWatcher:
    """
    Create a FileWatcher instance with default configuration.
    
    This is a convenience function that creates a watcher with sensible
    defaults, loading configuration from environment variables and
    accepting optional overrides.
    
    Args:
        index_tool: Optional IndexDocumentTool instance
        database_manager: Optional DocumentManager instance
        logger: Optional logger instance
        **config_overrides: Configuration overrides for WatcherConfig
        
    Returns:
        Configured FileWatcher instance
        
    Example:
        # Basic watcher with defaults
        watcher = create_default_watcher()
        
        # Watcher with custom directories
        watcher = create_default_watcher(
            watch_directories=['/home/user/docs', '/home/user/projects']
        )
        
        # Watcher with custom components
        watcher = create_default_watcher(
            index_tool=my_index_tool,
            database_manager=my_db_manager
        )
    """
    # Load base configuration from environment
    config = load_watcher_config_from_env()
    
    # Apply any overrides
    if config_overrides:
        # Create new config with overrides
        config_dict = {
            'watch_directories': config.watch_directories,
            'watched_extensions': config.watched_extensions,
            'ignore_patterns': config.ignore_patterns,
            'debounce_delay_ms': config.debounce_delay_ms,
            'enable_recursive': config.enable_recursive,
            'max_file_size_mb': config.max_file_size_mb,
            'batch_processing': config.batch_processing,
            'batch_delay_ms': config.batch_delay_ms
        }
        config_dict.update(config_overrides)
        config = WatcherConfig(**config_dict)
    
    return FileWatcher(
        config=config,
        index_tool=index_tool,
        database_manager=database_manager,
        logger=logger
    )


# Convenience aliases for common configurations
def create_lightweight_watcher(**kwargs) -> FileWatcher:
    """
    Create a lightweight watcher optimized for performance.
    
    This configuration uses minimal debouncing and batch processing
    for faster response times at the cost of higher resource usage.
    """
    config_overrides = {
        'debounce_delay_ms': 100,
        'batch_processing': False,
        'max_file_size_mb': 5
    }
    config_overrides.update(kwargs)
    return create_default_watcher(**config_overrides)


def create_batch_watcher(**kwargs) -> FileWatcher:
    """
    Create a batch-processing watcher optimized for efficiency.
    
    This configuration uses longer delays and batch processing
    to minimize resource usage when handling many file changes.
    """
    config_overrides = {
        'debounce_delay_ms': 1000,
        'batch_processing': True,
        'batch_delay_ms': 2000,
        'max_file_size_mb': 20
    }
    config_overrides.update(kwargs)
    return create_default_watcher(**config_overrides)