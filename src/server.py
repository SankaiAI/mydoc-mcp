"""
mydocs-mcp Server Implementation

This module provides the main MCP server implementation for the mydocs-mcp project.
It implements the Model Context Protocol (MCP) for AI agent document intelligence.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest, 
    ListPromptsResult,
    Resource,
    ListResourcesRequest,
    ListResourcesResult,
    ReadResourceRequest,
    ReadResourceResult,
)

from .config import ServerConfig
from .tool_registry import ToolRegistry
from .logging_config import setup_logging
from .tools.registration import register_core_tools
from .watcher import FileWatcher, create_default_watcher


class MyDocsMCPServer:
    """
    Main MCP server class for mydocs-mcp.
    
    This server provides document intelligence capabilities through MCP protocol,
    allowing AI agents to search, retrieve, and index personal documents.
    """
    
    def __init__(self, config: Optional[ServerConfig] = None):
        """Initialize the MCP server with configuration."""
        self.config = config or ServerConfig()
        self.logger = setup_logging(self.config.log_level)
        self.tool_registry = ToolRegistry()
        
        # Initialize the MCP Server
        self.server = Server("mydocs-mcp")
        
        # Register server handlers
        self._register_handlers()
        
        # Flag to track tool registration
        self._tools_registered = False
        
        # File system watcher (initialized later)
        self.file_watcher: Optional[FileWatcher] = None
        self._watcher_enabled = True  # Enable by default
        
        self.logger.info("MyDocsMCPServer initialized with configuration")
        self.logger.info(f"Transport: {self.config.transport}")
        self.logger.info(f"Log level: {self.config.log_level}")
    
    def _register_handlers(self) -> None:
        """Register all MCP protocol handlers."""
        self.logger.debug("Registering MCP protocol handlers")
        
        # Tool-related handlers
        self.server.list_tools = self._handle_list_tools
        self.server.call_tool = self._handle_call_tool
        
        # Resource handlers (for future use)
        self.server.list_resources = self._handle_list_resources
        self.server.read_resource = self._handle_read_resource
        
        # Prompt handlers (for future use) 
        self.server.list_prompts = self._handle_list_prompts
        self.server.get_prompt = self._handle_get_prompt
        
        self.logger.debug("MCP protocol handlers registered successfully")
    
    async def _initialize_tools(self) -> bool:
        """Initialize and register tools with the server."""
        if self._tools_registered:
            return True
        
        try:
            self.logger.info("Initializing mydocs-mcp tools")
            
            # Get database path from configuration
            database_path = str(self.config.get_database_path())
            
            # Register core tools
            success = await register_core_tools(
                tool_registry=self.tool_registry,
                database_path=database_path,
                logger=self.logger
            )
            
            if success:
                self._tools_registered = True
                tool_count = len(self.tool_registry.get_tool_names())
                self.logger.info(f"Successfully initialized {tool_count} tools")
            else:
                self.logger.error("Failed to initialize tools")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Tool initialization failed: {e}", exc_info=True)
            return False
    
    async def _initialize_watcher(self) -> bool:
        """Initialize and start the file system watcher."""
        if not self._watcher_enabled or self.file_watcher:
            return True
        
        try:
            self.logger.info("Initializing file system watcher")
            
            # Get the index tool and database manager from registry
            index_tool = self.tool_registry.get_tool("indexDocument")
            database_manager = getattr(index_tool, 'database_manager', None) if index_tool else None
            
            if not index_tool:
                self.logger.warning("indexDocument tool not available, file watcher disabled")
                self._watcher_enabled = False
                return False
            
            # Create watcher with default configuration
            self.file_watcher = create_default_watcher(
                index_tool=index_tool,
                database_manager=database_manager,
                logger=self.logger
            )
            
            # Start the watcher
            if await self.file_watcher.start():
                self.logger.info("File system watcher started successfully")
                return True
            else:
                self.logger.error("Failed to start file system watcher")
                self.file_watcher = None
                return False
                
        except Exception as e:
            self.logger.error(f"File system watcher initialization failed: {e}", exc_info=True)
            self.file_watcher = None
            return False
    
    async def _handle_list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """Handle list_tools requests from MCP clients."""
        self.logger.debug("Handling list_tools request")
        
        try:
            # Ensure tools are initialized
            if not self._tools_registered:
                await self._initialize_tools()
            
            # Get available tools from registry
            tools = self.tool_registry.get_available_tools()
            
            self.logger.debug(f"Found {len(tools)} available tools")
            return ListToolsResult(tools=tools)
            
        except Exception as e:
            self.logger.error(f"Error in list_tools handler: {e}")
            # Return empty tools list on error to maintain compatibility
            return ListToolsResult(tools=[])
    
    async def _handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle call_tool requests from MCP clients."""
        tool_name = request.params.name
        arguments = request.params.arguments or {}
        
        self.logger.debug(f"Handling call_tool request: {tool_name}")
        self.logger.debug(f"Arguments: {arguments}")
        
        try:
            # Ensure tools are initialized
            if not self._tools_registered:
                await self._initialize_tools()
            
            # Validate tool exists
            if not self.tool_registry.has_tool(tool_name):
                error_msg = f"Tool '{tool_name}' not found"
                self.logger.error(error_msg)
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {error_msg}")],
                    isError=True
                )
            
            # Execute the tool
            result = await self.tool_registry.execute_tool(tool_name, arguments)
            
            # Format result as MCP response
            if isinstance(result, dict) and "error" in result:
                self.logger.error(f"Tool execution error: {result['error']}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {result['error']}")],
                    isError=True
                )
            
            # Successful tool execution
            content_text = json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
            
            self.logger.debug(f"Tool '{tool_name}' executed successfully")
            return CallToolResult(
                content=[TextContent(type="text", text=content_text)],
                isError=False
            )
            
        except Exception as e:
            error_msg = f"Unexpected error executing tool '{tool_name}': {e}"
            self.logger.error(error_msg, exc_info=True)
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {error_msg}")],
                isError=True
            )
    
    async def _handle_list_resources(self, request: ListResourcesRequest) -> ListResourcesResult:
        """Handle list_resources requests (placeholder for future use)."""
        self.logger.debug("Handling list_resources request")
        
        # Currently no resources available
        return ListResourcesResult(resources=[])
    
    async def _handle_read_resource(self, request: ReadResourceRequest) -> ReadResourceResult:
        """Handle read_resource requests (placeholder for future use)."""
        self.logger.debug(f"Handling read_resource request: {request.params.uri}")
        
        # Currently no resources available
        return ReadResourceResult(
            contents=[TextContent(type="text", text="No resources available")]
        )
    
    async def _handle_list_prompts(self, request: ListPromptsRequest) -> ListPromptsResult:
        """Handle list_prompts requests (placeholder for future use)."""
        self.logger.debug("Handling list_prompts request")
        
        # Currently no prompts available
        return ListPromptsResult(prompts=[])
    
    async def _handle_get_prompt(self, request: GetPromptRequest) -> GetPromptResult:
        """Handle get_prompt requests (placeholder for future use)."""
        self.logger.debug(f"Handling get_prompt request: {request.params.name}")
        
        # Currently no prompts available
        return GetPromptResult(
            description="No prompts available",
            messages=[]
        )
    
    async def start_stdio_server(self) -> None:
        """Start the MCP server with STDIO transport."""
        self.logger.info("Starting mydocs-mcp server with STDIO transport")
        
        try:
            # Initialize tools first
            await self._initialize_tools()
            
            # Initialize file system watcher after tools are ready
            await self._initialize_watcher()
            
            # Run the STDIO server using the correct pattern
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream, 
                    write_stream,
                    InitializationOptions()
                )
            
        except KeyboardInterrupt:
            self.logger.info("Server shutdown requested by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}", exc_info=True)
            raise
        finally:
            # Ensure cleanup happens
            await self.stop()
    
    async def start(self) -> None:
        """Start the MCP server using configured transport."""
        transport = self.config.transport.lower()
        
        if transport == "stdio":
            await self.start_stdio_server()
        else:
            raise ValueError(f"Unsupported transport: {transport}")
    
    async def stop(self) -> None:
        """Stop the MCP server gracefully."""
        self.logger.info("Stopping mydocs-mcp server")
        
        try:
            # Stop file system watcher first
            if self.file_watcher:
                self.logger.info("Stopping file system watcher")
                await self.file_watcher.stop()
                self.file_watcher = None
        except Exception as e:
            self.logger.error(f"Error stopping file watcher: {e}")
        
        try:
            # Cleanup tool registry resources
            if hasattr(self.tool_registry, 'cleanup'):
                await self.tool_registry.cleanup()
        except Exception as e:
            self.logger.error(f"Error cleaning up tool registry: {e}")
        
        self.logger.info("Server stopped successfully")
    
    def get_watcher_status(self) -> Dict[str, Any]:
        """Get the current status of the file system watcher."""
        if not self.file_watcher:
            return {
                "enabled": self._watcher_enabled,
                "running": False,
                "status": "not_initialized"
            }
        
        try:
            stats = self.file_watcher.get_statistics()
            health = self.file_watcher.get_health_status()
            
            return {
                "enabled": self._watcher_enabled,
                "running": self.file_watcher.is_watching,
                "status": "healthy" if health['healthy'] else "unhealthy",
                "health": health,
                "statistics": stats
            }
        except Exception as e:
            return {
                "enabled": self._watcher_enabled,
                "running": False,
                "status": "error",
                "error": str(e)
            }
    
    async def restart_watcher(self) -> bool:
        """Restart the file system watcher."""
        try:
            # Stop existing watcher if running
            if self.file_watcher:
                await self.file_watcher.stop()
                self.file_watcher = None
            
            # Initialize and start new watcher
            return await self._initialize_watcher()
            
        except Exception as e:
            self.logger.error(f"Error restarting file watcher: {e}")
            return False


async def main() -> None:
    """Main entry point for the mydocs-mcp server."""
    try:
        # Load configuration
        config = ServerConfig.from_env()
        
        # Create and start server
        server = MyDocsMCPServer(config)
        await server.start()
        
    except KeyboardInterrupt:
        print("\nServer shutdown requested", file=sys.stderr)
    except Exception as e:
        print(f"Server startup failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())