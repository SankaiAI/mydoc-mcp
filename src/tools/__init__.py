"""
mydocs-mcp MCP Tools Package

This package contains all MCP tool implementations for the mydocs-mcp server.
Tools provide the core functionality that Claude Code and other MCP clients
can access for document intelligence operations.

Core Tools:
- indexDocument: Index documents for search and retrieval
- searchDocuments: Search through indexed documents
- getDocument: Retrieve document content and metadata
"""

from .base import BaseMCPTool, ToolResult, MCPToolError
from .indexDocument import IndexDocumentTool
from .searchDocuments import SearchDocumentsTool
from .getDocument import GetDocumentTool

__all__ = [
    'BaseMCPTool',
    'ToolResult', 
    'MCPToolError',
    'IndexDocumentTool',
    'SearchDocumentsTool',
    'GetDocumentTool'
]