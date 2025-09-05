"""
Configuration management for mydocs-mcp server.

This module handles server configuration loading from environment variables,
configuration files, and default values.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class ServerConfig:
    """
    Configuration settings for the mydocs-mcp server.
    
    Configuration is loaded in the following order (later overrides earlier):
    1. Default values
    2. Environment variables with MYDOCS_MCP_ prefix
    3. .env file (if present)
    """
    
    # Transport configuration
    transport: str = "stdio"
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Performance configuration
    max_concurrent_connections: int = 10
    request_timeout: float = 30.0
    response_timeout: float = 30.0
    
    # Storage configuration
    database_url: str = "sqlite:///data/mydocs.db"
    document_root: str = "./data/documents"
    cache_directory: str = "./data/cache"
    
    # Document processing configuration
    max_document_size: int = 10 * 1024 * 1024  # 10MB
    supported_extensions: list[str] = field(default_factory=lambda: [
        # Documentation files
        ".md", ".markdown", ".mdown", ".mkd", ".mkdn", ".txt", ".text", 
        ".readme", ".changelog", ".authors", ".contributors", ".install", ".license",
        # Code files
        ".py", ".js", ".css", ".html", ".htm", ".sql", 
        ".sh", ".bat", ".cmd", ".ps1", ".dockerfile",
        # Configuration files
        ".json", ".xml", ".yaml", ".yml", ".cfg", ".conf", ".config", 
        ".ini", ".properties", ".env", ".gitignore",
        # Data files
        ".csv", ".tsv", ".dat", ".log",
        # Notes and project files
        ".notes", ".todo", ".fixme"
    ])
    
    # Search configuration
    max_search_results: int = 50
    default_search_limit: int = 10
    enable_search_caching: bool = True
    search_cache_ttl: int = 3600  # 1 hour
    
    # Development/Debug configuration
    debug_mode: bool = False
    enable_dev_tools: bool = False
    auto_reload: bool = False
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "ServerConfig":
        """
        Load configuration from environment variables and optional .env file.
        
        Args:
            env_file: Optional path to .env file. If None, looks for .env in current directory.
        
        Returns:
            ServerConfig instance with loaded configuration.
        """
        # Load .env file if it exists
        if env_file:
            load_dotenv(env_file)
        else:
            # Look for .env in current directory
            env_path = Path(".env")
            if env_path.exists():
                load_dotenv(env_path)
        
        # Load configuration from environment variables
        config = cls()
        
        # Transport configuration
        if transport := os.getenv("MYDOCS_MCP_TRANSPORT"):
            config.transport = transport
        
        # Logging configuration
        if log_level := os.getenv("MYDOCS_MCP_LOG_LEVEL"):
            config.log_level = log_level.upper()
        
        if log_file := os.getenv("MYDOCS_MCP_LOG_FILE"):
            config.log_file = log_file
        
        # Performance configuration
        if max_conn := os.getenv("MYDOCS_MCP_MAX_CONNECTIONS"):
            try:
                config.max_concurrent_connections = int(max_conn)
            except ValueError:
                pass  # Keep default value
        
        if req_timeout := os.getenv("MYDOCS_MCP_REQUEST_TIMEOUT"):
            try:
                config.request_timeout = float(req_timeout)
            except ValueError:
                pass
        
        if resp_timeout := os.getenv("MYDOCS_MCP_RESPONSE_TIMEOUT"):
            try:
                config.response_timeout = float(resp_timeout)
            except ValueError:
                pass
        
        # Storage configuration
        if db_url := os.getenv("MYDOCS_MCP_DATABASE_URL"):
            config.database_url = db_url
        
        if doc_root := os.getenv("MYDOCS_MCP_DOCUMENT_ROOT"):
            config.document_root = doc_root
        
        if cache_dir := os.getenv("MYDOCS_MCP_CACHE_DIRECTORY"):
            config.cache_directory = cache_dir
        
        # Document processing configuration
        if max_size := os.getenv("MYDOCS_MCP_MAX_DOCUMENT_SIZE"):
            try:
                config.max_document_size = int(max_size)
            except ValueError:
                pass
        
        if extensions := os.getenv("MYDOCS_MCP_SUPPORTED_EXTENSIONS"):
            # Parse comma-separated list
            config.supported_extensions = [ext.strip() for ext in extensions.split(",")]
        
        # Search configuration
        if max_results := os.getenv("MYDOCS_MCP_MAX_SEARCH_RESULTS"):
            try:
                config.max_search_results = int(max_results)
            except ValueError:
                pass
        
        if default_limit := os.getenv("MYDOCS_MCP_DEFAULT_SEARCH_LIMIT"):
            try:
                config.default_search_limit = int(default_limit)
            except ValueError:
                pass
        
        if cache_enabled := os.getenv("MYDOCS_MCP_ENABLE_SEARCH_CACHING"):
            config.enable_search_caching = cache_enabled.lower() in ("true", "1", "yes")
        
        if cache_ttl := os.getenv("MYDOCS_MCP_SEARCH_CACHE_TTL"):
            try:
                config.search_cache_ttl = int(cache_ttl)
            except ValueError:
                pass
        
        # Development configuration
        if debug := os.getenv("MYDOCS_MCP_DEBUG"):
            config.debug_mode = debug.lower() in ("true", "1", "yes")
        
        if dev_tools := os.getenv("MYDOCS_MCP_DEV_TOOLS"):
            config.enable_dev_tools = dev_tools.lower() in ("true", "1", "yes")
        
        if auto_reload := os.getenv("MYDOCS_MCP_AUTO_RELOAD"):
            config.auto_reload = auto_reload.lower() in ("true", "1", "yes")
        
        return config
    
    def get_database_path(self) -> Path:
        """Get the resolved database file path."""
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url[10:]  # Remove 'sqlite:///'
            return Path(db_path).resolve()
        else:
            raise ValueError(f"Unsupported database URL format: {self.database_url}")
    
    def get_document_root_path(self) -> Path:
        """Get the resolved document root directory path."""
        return Path(self.document_root).resolve()
    
    def get_cache_directory_path(self) -> Path:
        """Get the resolved cache directory path."""
        return Path(self.cache_directory).resolve()
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        # Create data directories if they don't exist
        self.get_database_path().parent.mkdir(parents=True, exist_ok=True)
        self.get_document_root_path().mkdir(parents=True, exist_ok=True)
        self.get_cache_directory_path().mkdir(parents=True, exist_ok=True)
        
        # Create logs directory if log_file is specified
        if self.log_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> None:
        """
        Validate configuration settings.
        
        Raises:
            ValueError: If configuration is invalid.
        """
        # Validate transport
        if self.transport not in ["stdio", "http", "websocket"]:
            raise ValueError(f"Invalid transport: {self.transport}")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.log_level}")
        
        # Validate numeric settings
        if self.max_concurrent_connections <= 0:
            raise ValueError("max_concurrent_connections must be positive")
        
        if self.request_timeout <= 0:
            raise ValueError("request_timeout must be positive")
        
        if self.response_timeout <= 0:
            raise ValueError("response_timeout must be positive")
        
        if self.max_document_size <= 0:
            raise ValueError("max_document_size must be positive")
        
        if self.max_search_results <= 0:
            raise ValueError("max_search_results must be positive")
        
        if self.default_search_limit <= 0:
            raise ValueError("default_search_limit must be positive")
        
        if self.search_cache_ttl < 0:
            raise ValueError("search_cache_ttl must be non-negative")
        
        # Validate file extensions format
        for ext in self.supported_extensions:
            if not ext.startswith("."):
                raise ValueError(f"File extension must start with dot: {ext}")
    
    def __str__(self) -> str:
        """Return a string representation of the configuration."""
        return (
            f"ServerConfig("
            f"transport={self.transport}, "
            f"log_level={self.log_level}, "
            f"database_url={self.database_url}, "
            f"document_root={self.document_root}, "
            f"debug_mode={self.debug_mode}"
            f")"
        )