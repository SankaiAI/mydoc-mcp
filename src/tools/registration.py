"""
Tool Registration Module for mydocs-mcp

This module provides functionality to register MCP tools with the server
and handle the integration between tools and the MCP protocol.
"""

import logging
from typing import Optional

from .base import BaseMCPTool
from .indexDocument import IndexDocumentTool
from .searchDocuments import SearchDocumentsTool
from .getDocument import GetDocumentTool
from ..tool_registry import ToolRegistry
from ..database.database_manager import DocumentManager, create_document_manager
from ..parsers.parser_factory import get_default_factory


async def register_core_tools(
    tool_registry: ToolRegistry,
    database_path: str,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Register all core MCP tools with the tool registry.
    
    Args:
        tool_registry: ToolRegistry instance to register tools with
        database_path: Path to the database file
        logger: Optional logger instance
        
    Returns:
        True if all tools registered successfully, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        logger.info("Registering core mydocs-mcp tools")
        
        # Initialize database manager
        database_manager = await create_document_manager(
            database_path=database_path,
            logger=logger
        )
        
        if database_manager is None:
            logger.error("Failed to initialize database manager")
            return False
        
        # Get parser factory
        parser_factory = get_default_factory(logger)
        
        # Register indexDocument tool
        success = await register_index_document_tool(
            tool_registry, 
            database_manager, 
            parser_factory, 
            logger
        )
        
        if not success:
            logger.error("Failed to register indexDocument tool")
            await database_manager.close()
            return False
        
        # Register searchDocuments tool
        success = await register_search_documents_tool(
            tool_registry,
            database_manager,
            parser_factory,
            logger
        )
        
        if not success:
            logger.error("Failed to register searchDocuments tool")
            await database_manager.close()
            return False
        
        # Register getDocument tool
        success = await register_get_document_tool(
            tool_registry,
            database_manager,
            parser_factory,
            logger
        )
        
        if not success:
            logger.error("Failed to register getDocument tool")
            await database_manager.close()
            return False
        
        logger.info("Core mydocs-mcp tools registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register core tools: {e}", exc_info=True)
        return False


async def register_index_document_tool(
    tool_registry: ToolRegistry,
    database_manager: DocumentManager,
    parser_factory,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Register the indexDocument tool with the tool registry.
    
    Args:
        tool_registry: ToolRegistry instance
        database_manager: DocumentManager instance
        parser_factory: ParserFactory instance
        logger: Optional logger instance
        
    Returns:
        True if registration successful, False otherwise
    """
    try:
        # Create indexDocument tool instance
        index_tool = IndexDocumentTool(
            database_manager=database_manager,
            parser_factory=parser_factory,
            logger=logger
        )
        
        # Create wrapper function for tool registry
        async def index_document_handler(**kwargs):
            """Handler function for indexDocument tool."""
            result = await index_tool.execute(kwargs)
            
            # Convert ToolResult to registry-compatible format
            if result.success:
                return result.to_dict()
            else:
                return {"error": result.error, "success": False}
        
        # Register with tool registry
        tool_registry.register_tool(
            name=index_tool.get_tool_name(),
            description=index_tool.get_tool_description(),
            handler=index_document_handler,
            input_schema=index_tool.get_parameter_schema()
        )
        
        if logger:
            logger.info(f"Registered {index_tool.get_tool_name()} tool")
        
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"Failed to register indexDocument tool: {e}", exc_info=True)
        return False


async def register_search_documents_tool(
    tool_registry: ToolRegistry,
    database_manager: DocumentManager,
    parser_factory,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Register the searchDocuments tool with the tool registry.
    
    Args:
        tool_registry: ToolRegistry instance
        database_manager: DocumentManager instance
        parser_factory: ParserFactory instance (for compatibility)
        logger: Optional logger instance
        
    Returns:
        True if registration successful, False otherwise
    """
    try:
        # Create searchDocuments tool instance
        search_tool = SearchDocumentsTool(
            database_manager=database_manager,
            parser_factory=parser_factory,
            logger=logger
        )
        
        # Create wrapper function for tool registry
        async def search_documents_handler(**kwargs):
            """Handler function for searchDocuments tool."""
            result = await search_tool.execute(kwargs)
            
            # Convert ToolResult to registry-compatible format
            if result.success:
                return result.to_dict()
            else:
                return {"error": result.error, "success": False}
        
        # Register with tool registry
        tool_registry.register_tool(
            name=search_tool.get_tool_name(),
            description=search_tool.get_tool_description(),
            handler=search_documents_handler,
            input_schema=search_tool.get_parameter_schema()
        )
        
        if logger:
            logger.info(f"Registered {search_tool.get_tool_name()} tool")
        
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"Failed to register searchDocuments tool: {e}", exc_info=True)
        return False


async def register_get_document_tool(
    tool_registry: ToolRegistry,
    database_manager: DocumentManager,
    parser_factory,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Register the getDocument tool with the tool registry.
    
    Args:
        tool_registry: ToolRegistry instance
        database_manager: DocumentManager instance
        parser_factory: ParserFactory instance (for compatibility)
        logger: Optional logger instance
        
    Returns:
        True if registration successful, False otherwise
    """
    try:
        # Create getDocument tool instance
        get_document_tool = GetDocumentTool(
            database_manager=database_manager,
            parser_factory=parser_factory,
            logger=logger
        )
        
        # Create wrapper function for tool registry
        async def get_document_handler(**kwargs):
            """Handler function for getDocument tool."""
            result = await get_document_tool.execute(kwargs)
            
            # Convert ToolResult to registry-compatible format
            if result.success:
                return result.to_dict()
            else:
                return {"error": result.error, "success": False}
        
        # Register with tool registry
        tool_registry.register_tool(
            name=get_document_tool.get_tool_name(),
            description=get_document_tool.get_tool_description(),
            handler=get_document_handler,
            input_schema=get_document_tool.get_parameter_schema()
        )
        
        if logger:
            logger.info(f"Registered {get_document_tool.get_tool_name()} tool")
        
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"Failed to register getDocument tool: {e}", exc_info=True)
        return False


def create_mcp_tool_wrapper(tool: BaseMCPTool):
    """
    Create an MCP-compatible wrapper for a tool.
    
    Args:
        tool: BaseMCPTool instance to wrap
        
    Returns:
        Async function that can be registered with tool registry
    """
    async def tool_handler(**kwargs):
        """Generic tool handler wrapper."""
        try:
            result = await tool.execute(kwargs)
            return result.to_dict()
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }
    
    return tool_handler