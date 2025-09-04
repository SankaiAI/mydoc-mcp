"""mydocs-mcp: Personal Document Intelligence MCP Server

An intelligent document management system that provides MCP tools for indexing,
searching, and retrieving personal documents through Claude Code.
"""

__version__ = "0.1.0"
__author__ = "mydocs-mcp Team"

from .config import ServerConfig
from .server import MyDocsMCPServer
from .tool_registry import ToolRegistry, get_tool_registry, register_tool
from .logging_config import setup_logging, get_logger

__all__ = [
    "ServerConfig",
    "MyDocsMCPServer", 
    "ToolRegistry",
    "get_tool_registry",
    "register_tool",
    "setup_logging",
    "get_logger"
]