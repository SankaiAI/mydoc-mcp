"""
getDocument MCP Tool Implementation

This module implements the getDocument tool for mydocs-mcp, which provides
document retrieval capabilities by document ID or file path with support for
multiple output formats and metadata inclusion. The tool integrates with the
document queries layer and provides sub-200ms response times for typical retrieval.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from .base import BaseMCPTool, ToolResult, ToolExecutionError
from ..database.models import Document


class GetDocumentTool(BaseMCPTool):
    """
    MCP Tool for retrieving documents by ID or file path.
    
    This tool provides comprehensive document retrieval capabilities including:
    - Document retrieval by document ID or file path
    - Multiple output formats (json, markdown, text)
    - Optional metadata inclusion
    - Content formatting and size management
    - Performance metrics and optimization
    
    Performance targets:
    - Sub-200ms response time for typical document retrieval
    - Support for documents up to 10MB with content management
    - Efficient metadata and content formatting
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize getDocument tool with format options."""
        super().__init__(*args, **kwargs)
        self.max_content_size = 5 * 1024 * 1024  # 5MB max content size for performance
        self.truncation_indicator = "\n\n[Content truncated due to size limits]\n"
    
    def get_tool_name(self) -> str:
        """Return the MCP tool name."""
        return "getDocument"
    
    def get_tool_description(self) -> str:
        """Return the MCP tool description."""
        return (
            "Retrieve a specific document by ID or file path with support for multiple "
            "output formats (json, markdown, text) and optional metadata inclusion. "
            "Optimized for sub-200ms retrieval times with content size management."
        )
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "integer",
                    "description": "Database document ID to retrieve",
                    "minimum": 1
                },
                "file_path": {
                    "type": "string",
                    "description": "File path of document to retrieve",
                    "minLength": 1,
                    "maxLength": 1000
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Include full document content in response",
                    "default": True
                },
                "format": {
                    "type": "string",
                    "description": "Output format for document content",
                    "enum": ["json", "markdown", "text"],
                    "default": "json"
                },
                "include_metadata": {
                    "type": "boolean",
                    "description": "Include document metadata in response",
                    "default": True
                },
                "max_content_length": {
                    "type": "integer",
                    "description": "Maximum content length to return (0 for no limit)",
                    "default": 0,
                    "minimum": 0,
                    "maximum": 10485760  # 10MB
                }
            },
            "oneOf": [
                {"required": ["document_id"]},
                {"required": ["file_path"]}
            ],
            "additionalProperties": False
        }
    
    async def _execute_tool(self, validated_params: Dict[str, Any]) -> ToolResult:
        """
        Execute the getDocument tool.
        
        Args:
            validated_params: Validated tool parameters
            
        Returns:
            ToolResult with document retrieval results
        """
        document_id = validated_params.get("document_id")
        file_path = validated_params.get("file_path")
        include_content = validated_params.get("include_content", True)
        format_type = validated_params.get("format", "json")
        include_metadata = validated_params.get("include_metadata", True)
        max_content_length = validated_params.get("max_content_length", 0)
        
        retrieval_start_time = time.time()
        
        try:
            # Validate that either document_id or file_path is provided
            if not document_id and not file_path:
                return ToolResult.error_result(
                    "Either 'document_id' or 'file_path' parameter is required"
                )
            
            if document_id and file_path:
                return ToolResult.error_result(
                    "Only one of 'document_id' or 'file_path' should be provided"
                )
            
            # Retrieve document from database
            document = None
            retrieval_method = ""
            
            if document_id:
                document = await self.database_manager.doc_queries.get_document(document_id)
                retrieval_method = "by_id"
                
                if not document:
                    return ToolResult.error_result(
                        f"Document with ID {document_id} not found",
                        metadata={"document_id": document_id, "retrieval_method": retrieval_method}
                    )
            
            elif file_path:
                document = await self.database_manager.doc_queries.get_document_by_path(file_path)
                retrieval_method = "by_path"
                
                if not document:
                    return ToolResult.error_result(
                        f"Document with path '{file_path}' not found",
                        metadata={"file_path": file_path, "retrieval_method": retrieval_method}
                    )
            
            # Prepare response data
            response_data = await self._format_document_response(
                document=document,
                include_content=include_content,
                format_type=format_type,
                include_metadata=include_metadata,
                max_content_length=max_content_length
            )
            
            retrieval_time_ms = (time.time() - retrieval_start_time) * 1000
            
            # Add retrieval metadata
            response_data["retrieval_time_ms"] = round(retrieval_time_ms, 2)
            response_data["retrieval_method"] = retrieval_method
            
            # Log retrieval performance
            self.logger.info(
                f"Document retrieved: id={document.id}, path='{document.file_path}', "
                f"method={retrieval_method}, time={retrieval_time_ms:.2f}ms"
            )
            
            return ToolResult.success_result(
                data=response_data,
                metadata={
                    "tool_version": "1.0",
                    "retrieval_method": retrieval_method,
                    "performance_target_met": retrieval_time_ms < 200.0,
                    "document_id": document.id,
                    "file_size_bytes": document.file_size
                }
            )
            
        except Exception as e:
            retrieval_time_ms = (time.time() - retrieval_start_time) * 1000
            self.logger.error(f"getDocument tool execution failed: {e}", exc_info=True)
            
            error_metadata = {
                "retrieval_time_ms": round(retrieval_time_ms, 2)
            }
            
            if document_id:
                error_metadata["document_id"] = document_id
            if file_path:
                error_metadata["file_path"] = file_path
            
            return ToolResult.error_result(
                f"Document retrieval failed: {str(e)}",
                metadata=error_metadata
            )
    
    async def _format_document_response(
        self,
        document: Document,
        include_content: bool,
        format_type: str,
        include_metadata: bool,
        max_content_length: int
    ) -> Dict[str, Any]:
        """
        Format document data for response.
        
        Args:
            document: Document instance from database
            include_content: Whether to include content
            format_type: Output format (json, markdown, text)
            include_metadata: Whether to include metadata
            max_content_length: Maximum content length
            
        Returns:
            Formatted document response dictionary
        """
        response = {
            "document_id": document.id,
            "file_path": document.file_path,
            "file_name": document.file_name,
            "file_type": document.file_type,
            "file_size_bytes": document.file_size,
            "file_hash": document.file_hash,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "modified_at": document.modified_at.isoformat() if document.modified_at else None,
            "indexed_at": document.indexed_at.isoformat() if document.indexed_at else None
        }
        
        # Add content if requested
        if include_content:
            if document.content:
                formatted_content = await self._format_content(
                    content=document.content,
                    format_type=format_type,
                    max_length=max_content_length
                )
                
                response["content"] = formatted_content["content"]
                response["content_length"] = formatted_content["length"]
                response["content_truncated"] = formatted_content["truncated"]
                response["content_format"] = format_type
            else:
                # Handle empty content
                response["content"] = ""
                response["content_length"] = 0
                response["content_truncated"] = False
                response["content_format"] = format_type
        else:
            # Content not requested - don't include content fields
            pass
        
        # Add metadata if requested
        if include_metadata:
            try:
                metadata = await self.database_manager.metadata_queries.get_document_metadata(
                    document.id
                )
                response["metadata"] = metadata
                
                # Add parsed metadata from JSON if available
                if document.metadata_json:
                    try:
                        parsed_metadata = json.loads(document.metadata_json)
                        response["parsed_metadata"] = parsed_metadata
                    except json.JSONDecodeError:
                        response["parsed_metadata"] = {}
                else:
                    response["parsed_metadata"] = {}
                
            except Exception as e:
                self.logger.warning(f"Failed to retrieve metadata for document {document.id}: {e}")
                response["metadata"] = {}
                response["parsed_metadata"] = {}
        
        # Add file statistics
        response["file_stats"] = await self._get_file_statistics(document)
        
        return response
    
    async def _format_content(
        self,
        content: str,
        format_type: str,
        max_length: int
    ) -> Dict[str, Any]:
        """
        Format document content according to specified format and size limits.
        
        Args:
            content: Raw document content
            format_type: Desired output format
            max_length: Maximum content length (0 for no limit)
            
        Returns:
            Dictionary with formatted content information
        """
        if not content:
            return {
                "content": "",
                "length": 0,
                "truncated": False
            }
        
        original_length = len(content)
        truncated = False
        
        # Apply size limits if specified
        if max_length > 0 and original_length > max_length:
            content = content[:max_length] + self.truncation_indicator
            truncated = True
        
        # Apply memory-based size limits
        elif original_length > self.max_content_size:
            content = content[:self.max_content_size] + self.truncation_indicator
            truncated = True
        
        # Format content based on type
        if format_type == "json":
            # Return as-is for JSON (will be properly escaped during serialization)
            formatted_content = content
        
        elif format_type == "markdown":
            # For markdown files, preserve formatting
            # For other files, wrap in code blocks
            if content.strip().startswith(('# ', '## ', '### ', '#### ', '##### ', '###### ')):
                formatted_content = content
            else:
                # Detect if content looks like markdown
                markdown_indicators = ['**', '*', '`', '##', '- ', '1. ', '[', '](']
                has_markdown = any(indicator in content for indicator in markdown_indicators)
                
                if has_markdown:
                    formatted_content = content
                else:
                    formatted_content = f"```\n{content}\n```"
        
        elif format_type == "text":
            # Strip markdown formatting for plain text
            formatted_content = self._strip_markdown(content)
        
        else:
            # Default to original content
            formatted_content = content
        
        return {
            "content": formatted_content,
            "length": len(formatted_content),
            "truncated": truncated,
            "original_length": original_length
        }
    
    def _strip_markdown(self, content: str) -> str:
        """
        Strip basic markdown formatting for plain text output.
        
        Args:
            content: Content with markdown formatting
            
        Returns:
            Plain text content
        """
        import re
        
        # Remove headers
        content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)
        
        # Remove bold/italic
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*([^*]+)\*', r'\1', content)      # Italic
        content = re.sub(r'__([^_]+)__', r'\1', content)      # Bold
        content = re.sub(r'_([^_]+)_', r'\1', content)        # Italic
        
        # Remove code blocks first (including markers)
        content = re.sub(r'```[^\n]*\n(.*?)\n```', r'\1', content, flags=re.DOTALL)
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)  # Handle single line code blocks
        
        # Remove inline code
        content = re.sub(r'`([^`]+)`', r'\1', content)
        content = re.sub(r'`', '', content)  # Remove any remaining backticks
        
        # Remove links (keep link text)
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        
        # Remove list markers
        content = re.sub(r'^\s*[-*+]\s+', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    async def _get_file_statistics(self, document: Document) -> Dict[str, Any]:
        """
        Get file statistics for the document.
        
        Args:
            document: Document instance
            
        Returns:
            Dictionary with file statistics
        """
        stats = {
            "size_bytes": document.file_size,
            "size_readable": self._format_file_size(document.file_size),
            "extension": Path(document.file_path).suffix,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "modified_at": document.modified_at.isoformat() if document.modified_at else None,
            "indexed_at": document.indexed_at.isoformat() if document.indexed_at else None
        }
        
        # Add content statistics if available
        if document.content:
            content_lines = document.content.count('\n') + 1
            content_words = len(document.content.split())
            content_chars = len(document.content)
            
            stats["content_statistics"] = {
                "lines": content_lines,
                "words": content_words,
                "characters": content_chars,
                "characters_no_spaces": len(document.content.replace(' ', ''))
            }
        
        return stats
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Human-readable size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    async def get_document_statistics(self) -> Dict[str, Any]:
        """
        Get document retrieval statistics.
        
        Returns:
            Dictionary with retrieval statistics
        """
        try:
            # Get document count by type
            total_docs = await self.database_manager.doc_queries.count_documents()
            md_docs = await self.database_manager.doc_queries.count_documents(".md")
            txt_docs = await self.database_manager.doc_queries.count_documents(".txt")
            
            return {
                "indexed_documents": {
                    "total": total_docs,
                    "markdown": md_docs,
                    "text": txt_docs
                },
                "tool_performance": self.get_tool_info()["performance"],
                "content_limits": {
                    "max_content_size_bytes": self.max_content_size,
                    "max_content_size_readable": self._format_file_size(self.max_content_size)
                },
                "supported_formats": ["json", "markdown", "text"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get document statistics: {e}")
            return {
                "error": str(e),
                "tool_performance": self.get_tool_info()["performance"]
            }