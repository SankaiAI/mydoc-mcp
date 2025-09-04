"""
Logging configuration for mydocs-mcp server.

This module provides structured logging setup with appropriate formatters,
handlers, and log levels for the MCP server.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels in console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green  
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors for console output."""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # Format the message
        formatted = super().format(record)
        
        # Reset levelname to avoid affecting other handlers
        record.levelname = levelname
        
        return formatted


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_colors: bool = True
) -> logging.Logger:
    """
    Set up logging configuration for the mydocs-mcp server.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, logs only to console.
        enable_colors: Whether to enable colored output in console
    
    Returns:
        Configured logger instance
    """
    # Get the root logger for mydocs-mcp
    logger = logging.getLogger("mydocs-mcp")
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if enable_colors and sys.stdout.isatty():
        console_formatter = ColoredFormatter(console_format)
    else:
        console_formatter = logging.Formatter(console_format)
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        
        # Create log directory if it doesn't exist
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler to prevent huge log files
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Configure other loggers to avoid noise
    
    # Reduce noise from aiofiles and other dependencies
    logging.getLogger("aiofiles").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    
    # Keep MCP protocol logging at INFO level for debugging
    logging.getLogger("mcp").setLevel(logging.INFO)
    
    logger.info("Logging configured successfully")
    logger.info(f"Log level: {level.upper()}")
    if log_file:
        logger.info(f"Log file: {log_file}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f"mydocs-mcp.{name}")


class PerformanceLogger:
    """
    Context manager for logging performance metrics.
    
    Usage:
        async with PerformanceLogger("search_operation") as perf:
            # ... do work ...
            perf.add_metric("documents_processed", count)
    """
    
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        """Initialize performance logger."""
        self.operation_name = operation_name
        self.logger = logger or get_logger("performance")
        self.start_time = None
        self.metrics = {}
    
    async def __aenter__(self):
        """Start performance tracking."""
        import time
        self.start_time = time.perf_counter()
        self.logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End performance tracking and log results."""
        import time
        if self.start_time is not None:
            duration = time.perf_counter() - self.start_time
            
            # Log performance metrics
            metrics_str = ", ".join(f"{k}={v}" for k, v in self.metrics.items())
            if metrics_str:
                self.logger.info(
                    f"Operation '{self.operation_name}' completed in {duration:.3f}s "
                    f"({metrics_str})"
                )
            else:
                self.logger.info(
                    f"Operation '{self.operation_name}' completed in {duration:.3f}s"
                )
            
            # Log warning for slow operations
            if duration > 1.0:  # > 1 second
                self.logger.warning(
                    f"Slow operation detected: '{self.operation_name}' took {duration:.3f}s"
                )
    
    def add_metric(self, name: str, value: any) -> None:
        """Add a performance metric."""
        self.metrics[name] = value
    
    def set_metrics(self, **kwargs) -> None:
        """Set multiple performance metrics."""
        self.metrics.update(kwargs)