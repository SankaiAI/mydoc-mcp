"""
Main entry point for mydocs-mcp server.

This module provides the command-line interface and startup logic
for the mydocs-mcp MCP server.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from .config import ServerConfig
from .server import MyDocsMCPServer
from .logging_config import setup_logging


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="mydocs-mcp - Personal Document Intelligence MCP Server",
        prog="mydocs-mcp"
    )
    
    # Configuration options
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (.env format)"
    )
    
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "websocket"],
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file (optional)"
    )
    
    parser.add_argument(
        "--database-url",
        type=str,
        help="Database URL (default: sqlite:///data/mydocs.db)"
    )
    
    parser.add_argument(
        "--document-root",
        type=str,
        help="Document root directory (default: ./data/documents)"
    )
    
    # Development options
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--dev-tools",
        action="store_true",
        help="Enable development tools"
    )
    
    parser.add_argument(
        "--auto-reload",
        action="store_true",
        help="Auto-reload on code changes (development mode)"
    )
    
    # Version information
    parser.add_argument(
        "--version",
        action="version",
        version="mydocs-mcp 0.1.0"
    )
    
    return parser.parse_args()


def create_config_from_args(args: argparse.Namespace) -> ServerConfig:
    """Create server configuration from command line arguments."""
    # Load base configuration from environment/file
    config = ServerConfig.from_env(args.config)
    
    # Override with command line arguments
    if args.transport:
        config.transport = args.transport
    
    if args.log_level:
        config.log_level = args.log_level.upper()
    
    if args.log_file:
        config.log_file = args.log_file
    
    if args.database_url:
        config.database_url = args.database_url
    
    if args.document_root:
        config.document_root = args.document_root
    
    if args.debug:
        config.debug_mode = True
        config.log_level = "DEBUG"  # Force debug logging
    
    if args.dev_tools:
        config.enable_dev_tools = True
    
    if args.auto_reload:
        config.auto_reload = True
    
    return config


def validate_environment(config: ServerConfig) -> None:
    """Validate that the environment is ready for server startup."""
    # Validate configuration
    config.validate()
    
    # Ensure required directories exist
    config.ensure_directories()
    
    # Check Python version
    if sys.version_info < (3, 11):
        raise RuntimeError("Python 3.11 or higher is required")
    
    # Check that MCP is available
    try:
        import mcp
    except ImportError as e:
        raise RuntimeError("MCP library not found. Please install requirements.txt") from e


async def main_async(config: ServerConfig) -> None:
    """Async main function."""
    try:
        # Create and start server
        server = MyDocsMCPServer(config)
        
        print(f"Starting mydocs-mcp server with {config.transport} transport...", file=sys.stderr)
        print(f"Log level: {config.log_level}", file=sys.stderr)
        if config.debug_mode:
            print("Debug mode enabled", file=sys.stderr)
        
        await server.start()
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        if config.debug_mode:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main() -> None:
    """Main entry point for the mydocs-mcp server."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Create configuration
        config = create_config_from_args(args)
        
        # Validate environment
        validate_environment(config)
        
        # Run the server
        asyncio.run(main_async(config))
        
    except Exception as e:
        print(f"Startup failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()