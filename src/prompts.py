"""
MCP Prompts for mydocs-mcp server.

This module provides prompt definitions that allow Claude Code to automatically
use the MCP tools based on natural language requests.
"""

from typing import List, Dict, Any
from mcp.types import Prompt, PromptMessage, TextContent
from mcp.types import Role


def get_available_prompts() -> List[Prompt]:
    """
    Get list of available prompts for the MCP server.
    
    These prompts allow Claude Code to understand when to use the tools
    automatically based on user queries.
    """
    prompts = []
    
    # Index Document Prompt
    prompts.append(Prompt(
        name="index_document",
        description=(
            "Index a document file for searching. Use this when the user wants to "
            "add a document to the search index or make a document searchable."
        ),
        arguments=[
            {
                "name": "file_path",
                "description": "Path to the document file to index",
                "required": True
            }
        ]
    ))
    
    # Search Documents Prompt
    prompts.append(Prompt(
        name="search_documents",
        description=(
            "Search through indexed documents. Use this when the user wants to "
            "find information, search for content, or query documents."
        ),
        arguments=[
            {
                "name": "query",
                "description": "Search query text",
                "required": True
            },
            {
                "name": "limit",
                "description": "Maximum number of results to return",
                "required": False
            }
        ]
    ))
    
    # Get Document Prompt
    prompts.append(Prompt(
        name="get_document",
        description=(
            "Retrieve a specific document by ID. Use this when the user wants to "
            "read or view a specific document's content."
        ),
        arguments=[
            {
                "name": "document_id",
                "description": "ID of the document to retrieve",
                "required": True
            }
        ]
    ))
    
    return prompts


def create_index_prompt_messages(file_path: str) -> List[PromptMessage]:
    """Create prompt messages for indexing a document."""
    return [
        PromptMessage(
            role=Role.user,
            content=TextContent(
                type="text",
                text=f"Please index the document at: {file_path}"
            )
        ),
        PromptMessage(
            role=Role.assistant,
            content=TextContent(
                type="text",
                text=f"I'll index the document at {file_path} for you. This will make it searchable."
            )
        )
    ]


def create_search_prompt_messages(query: str, limit: int = 10) -> List[PromptMessage]:
    """Create prompt messages for searching documents."""
    return [
        PromptMessage(
            role=Role.user,
            content=TextContent(
                type="text",
                text=f"Search for: {query}"
            )
        ),
        PromptMessage(
            role=Role.assistant,
            content=TextContent(
                type="text",
                text=f"I'll search the indexed documents for '{query}' and return up to {limit} results."
            )
        )
    ]


def create_get_document_prompt_messages(document_id: str) -> List[PromptMessage]:
    """Create prompt messages for retrieving a document."""
    return [
        PromptMessage(
            role=Role.user,
            content=TextContent(
                type="text",
                text=f"Get document with ID: {document_id}"
            )
        ),
        PromptMessage(
            role=Role.assistant,
            content=TextContent(
                type="text",
                text=f"I'll retrieve the document with ID {document_id} for you."
            )
        )
    ]