"""
File system watcher configuration for mydocs-mcp.

This module provides configuration management for the file system watcher,
including watch directories, file type filtering, and performance settings.
"""

import os
from pathlib import Path
from typing import List, Set, Optional, Dict, Any
from dataclasses import dataclass, field
from ..config import ServerConfig


@dataclass
class WatcherConfig:
    """
    Configuration settings for the file system watcher.
    
    Attributes:
        watch_directories: List of directories to monitor for changes
        watched_extensions: File extensions to monitor (.md, .txt)
        ignore_patterns: Glob patterns to ignore during monitoring
        debounce_delay_ms: Delay in milliseconds to debounce rapid file changes
        enable_recursive: Whether to watch subdirectories recursively
        max_file_size_mb: Maximum file size to process (in MB)
        batch_processing: Whether to batch multiple file changes
        batch_delay_ms: Delay for batching file changes
    """
    watch_directories: List[str] = field(default_factory=list)
    watched_extensions: Set[str] = field(default_factory=lambda: {'.md', '.txt'})
    ignore_patterns: List[str] = field(default_factory=lambda: [
        '*.tmp', '*.swp', '*~', '.DS_Store', 'Thumbs.db',
        '__pycache__', '*.pyc', '.git', '.svn', '.hg'
    ])
    debounce_delay_ms: int = 500
    enable_recursive: bool = True
    max_file_size_mb: int = 10
    batch_processing: bool = True
    batch_delay_ms: int = 1000
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Normalize watched extensions to lowercase with dots
        self.watched_extensions = {
            ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
            for ext in self.watched_extensions
        }
        
        # Set default watch directories if none specified
        if not self.watch_directories:
            self.watch_directories = self._get_default_watch_directories()
        
        # Validate and normalize watch directories
        self.watch_directories = self._validate_watch_directories(self.watch_directories)
    
    def _get_default_watch_directories(self) -> List[str]:
        """
        Get default watch directories based on environment and platform.
        
        Returns:
            List of default directory paths
        """
        default_dirs = []
        home_dir = Path.home()
        
        # Common document directories
        potential_dirs = [
            home_dir / "Documents",
            home_dir / "Desktop" / "notes",
            home_dir / "notes",
            home_dir / "docs",
        ]
        
        # Check for environment variable override
        env_dirs = os.getenv('MYDOCS_WATCH_DIRS', '').strip()
        if env_dirs:
            # Split by semicolon for Windows, colon for Unix
            separator = ';' if os.name == 'nt' else ':'
            env_paths = [path.strip() for path in env_dirs.split(separator) if path.strip()]
            default_dirs.extend(env_paths)
        else:
            # Add existing directories from potential list
            for dir_path in potential_dirs:
                if dir_path.exists() and dir_path.is_dir():
                    default_dirs.append(str(dir_path))
        
        return default_dirs
    
    def _validate_watch_directories(self, directories: List[str]) -> List[str]:
        """
        Validate and normalize watch directories.
        
        Args:
            directories: List of directory paths to validate
            
        Returns:
            List of validated directory paths
        """
        valid_dirs = []
        
        for dir_path in directories:
            path_obj = Path(dir_path).expanduser().resolve()
            
            # Skip if directory doesn't exist (will be created if needed)
            if not path_obj.exists():
                continue
                
            # Skip if not a directory
            if not path_obj.is_dir():
                continue
                
            # Check if readable
            if not os.access(path_obj, os.R_OK):
                continue
            
            valid_dirs.append(str(path_obj))
        
        return valid_dirs
    
    def should_watch_file(self, file_path: Path) -> bool:
        """
        Check if a file should be watched based on configuration.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file should be watched
        """
        # Check file extension
        if file_path.suffix.lower() not in self.watched_extensions:
            return False
        
        # Check file size
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                return False
        except OSError:
            return False
        
        # Check ignore patterns
        file_name = file_path.name
        for pattern in self.ignore_patterns:
            # Simple glob-style pattern matching
            if self._matches_pattern(file_name, pattern):
                return False
        
        return True
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """
        Simple glob-style pattern matching.
        
        Args:
            filename: File name to check
            pattern: Glob pattern (supports * and ?)
            
        Returns:
            True if filename matches pattern
        """
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def get_watch_summary(self) -> Dict[str, Any]:
        """
        Get a summary of watch configuration.
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            "directories_count": len(self.watch_directories),
            "directories": self.watch_directories,
            "watched_extensions": list(self.watched_extensions),
            "recursive_watch": self.enable_recursive,
            "debounce_delay_ms": self.debounce_delay_ms,
            "batch_processing": self.batch_processing,
            "batch_delay_ms": self.batch_delay_ms,
            "max_file_size_mb": self.max_file_size_mb,
            "ignore_patterns_count": len(self.ignore_patterns)
        }


def create_watcher_config(
    watch_directories: Optional[List[str]] = None,
    **kwargs
) -> WatcherConfig:
    """
    Create watcher configuration with optional overrides.
    
    Args:
        watch_directories: Optional list of directories to watch
        **kwargs: Additional configuration overrides
        
    Returns:
        WatcherConfig instance
    """
    config_data = {}
    
    if watch_directories:
        config_data["watch_directories"] = watch_directories
    
    # Apply any additional overrides
    config_data.update(kwargs)
    
    return WatcherConfig(**config_data)


def load_watcher_config_from_env() -> WatcherConfig:
    """
    Load watcher configuration from environment variables.
    
    Returns:
        WatcherConfig instance with environment-based settings
    """
    config_data = {}
    
    # Watch directories from environment
    env_dirs = os.getenv('MYDOCS_WATCH_DIRS', '').strip()
    if env_dirs:
        separator = ';' if os.name == 'nt' else ':'
        config_data["watch_directories"] = [
            path.strip() for path in env_dirs.split(separator) if path.strip()
        ]
    
    # Watched file extensions
    env_extensions = os.getenv('MYDOCS_WATCH_EXTENSIONS', '').strip()
    if env_extensions:
        config_data["watched_extensions"] = set(
            ext.strip() for ext in env_extensions.split(',') if ext.strip()
        )
    
    # Debounce delay
    env_debounce = os.getenv('MYDOCS_DEBOUNCE_DELAY_MS', '').strip()
    if env_debounce and env_debounce.isdigit():
        config_data["debounce_delay_ms"] = int(env_debounce)
    
    # Enable recursive watching
    env_recursive = os.getenv('MYDOCS_RECURSIVE_WATCH', '').strip().lower()
    if env_recursive in ('true', 'false'):
        config_data["enable_recursive"] = env_recursive == 'true'
    
    # Max file size
    env_max_size = os.getenv('MYDOCS_MAX_FILE_SIZE_MB', '').strip()
    if env_max_size and env_max_size.isdigit():
        config_data["max_file_size_mb"] = int(env_max_size)
    
    # Batch processing
    env_batch = os.getenv('MYDOCS_BATCH_PROCESSING', '').strip().lower()
    if env_batch in ('true', 'false'):
        config_data["batch_processing"] = env_batch == 'true'
    
    # Batch delay
    env_batch_delay = os.getenv('MYDOCS_BATCH_DELAY_MS', '').strip()
    if env_batch_delay and env_batch_delay.isdigit():
        config_data["batch_delay_ms"] = int(env_batch_delay)
    
    return WatcherConfig(**config_data)