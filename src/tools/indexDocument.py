"""
indexDocument MCP Tool Implementation

This module implements the indexDocument tool for mydocs-mcp, which allows
clients to index document files (.md, .txt) for search and retrieval.
The tool integrates with the parser system and database layer for efficient
document processing and storage.
"""

import os
import asyncio
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from .base import BaseMCPTool, ToolResult, ToolExecutionError
from ..parsers.parser_factory import ParserFactory
from ..database.database_manager import DocumentManager


class IndexDocumentTool(BaseMCPTool):
    """
    MCP Tool for indexing documents.
    
    This tool processes document files through the parser system,
    extracts content and metadata, and stores them in the database
    for search and retrieval operations.
    
    Features:
    - Support for .md and .txt files
    - Automatic content parsing and metadata extraction
    - Duplicate detection and handling
    - Force reindexing option
    - Performance monitoring
    """
    
    def get_tool_name(self) -> str:
        """Return the MCP tool name."""
        return "indexDocument"
    
    def get_tool_description(self) -> str:
        """Return the MCP tool description."""
        return (
            "Index a document file (.md or .txt) for search and retrieval. "
            "Parses content, extracts metadata, and stores in the document database. "
            "Supports force reindexing and automatic duplicate detection."
        )
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Full path to the document file to index",
                    "minLength": 1,
                    "maxLength": 1000
                },
                "force_reindex": {
                    "type": "boolean",
                    "description": "Force reindexing even if document is already indexed and up to date",
                    "default": False
                }
            },
            "required": ["file_path"],
            "additionalProperties": False
        }
    
    async def _execute_tool(self, validated_params: Dict[str, Any]) -> ToolResult:
        """
        Execute the indexDocument tool.
        
        Args:
            validated_params: Validated tool parameters
            
        Returns:
            ToolResult with indexing results
        """
        file_path = validated_params["file_path"]
        force_reindex = validated_params.get("force_reindex", False)
        
        try:
            # Validate file exists and is readable
            path_obj = Path(file_path)
            if not path_obj.exists():
                return ToolResult.error_result(
                    f"File not found: {file_path}"
                )
            
            if not path_obj.is_file():
                return ToolResult.error_result(
                    f"Path is not a file: {file_path}"
                )
            
            # Check file extension
            if not self._is_supported_file_type(file_path):
                return ToolResult.error_result(
                    f"Unsupported file type: {path_obj.suffix}. "
                    f"Supported types: .md, .txt"
                )
            
            # Check file size (limit to reasonable size for MVP)
            file_size = path_obj.stat().st_size
            max_file_size = 10 * 1024 * 1024  # 10MB limit
            if file_size > max_file_size:
                return ToolResult.error_result(
                    f"File too large: {file_size} bytes. Maximum size: {max_file_size} bytes"
                )
            
            # Check if already indexed
            existing_doc = await self.database_manager.doc_queries.get_document_by_path(file_path)
            
            if existing_doc and not force_reindex:
                # Check if file has been modified since last indexing
                file_mtime = datetime.fromtimestamp(path_obj.stat().st_mtime)
                if file_mtime <= existing_doc.modified_at:
                    return ToolResult.success_result({
                        "status": "already_indexed",
                        "document_id": existing_doc.id,
                        "message": "Document is already indexed and up to date",
                        "indexed_at": existing_doc.indexed_at.isoformat() if existing_doc.indexed_at else None,
                        "file_path": file_path
                    })
            
            # Parse the document
            parse_result = await self.parser_factory.parse_file(file_path)
            
            if not parse_result.success:
                return ToolResult.error_result(
                    f"Failed to parse document: {parse_result.error_message}"
                )
            
            # Prepare content and metadata
            content = parse_result.content or ""
            if not content.strip():
                return ToolResult.error_result(
                    "Document appears to be empty or contains no readable content"
                )
            
            # Combine metadata from parsing and file system
            combined_metadata = self._combine_metadata(parse_result, path_obj)
            
            # Index the document
            document_id = await self.database_manager.index_document(
                file_path=file_path,
                content=content,
                metadata=combined_metadata,
                extract_keywords=True
            )
            
            if document_id is None:
                return ToolResult.error_result(
                    "Failed to index document in database"
                )
            
            # Prepare success response
            response_data = {
                "status": "indexed" if not existing_doc else "reindexed",
                "document_id": document_id,
                "file_path": file_path,
                "file_size_bytes": file_size,
                "content_length": len(content),
                "indexed_at": datetime.now().isoformat(),
                "metadata_fields_extracted": len(combined_metadata),
                "parsing_stats": parse_result.parsing_stats or {}
            }
            
            # Add keywords information if available
            if parse_result.keywords:
                response_data["keywords_extracted"] = len(parse_result.keywords)
            
            return ToolResult.success_result(
                data=response_data,
                metadata={
                    "tool_version": "1.0",
                    "parser_type": parse_result.parsing_stats.get("parser_type", "unknown") if parse_result.parsing_stats else "unknown",
                    "force_reindex": force_reindex
                }
            )
            
        except Exception as e:
            self.logger.error(f"indexDocument tool execution failed: {e}", exc_info=True)
            return ToolResult.error_result(
                f"Tool execution failed: {str(e)}"
            )
    
    def _is_supported_file_type(self, file_path: str) -> bool:
        """
        Check if file type is supported for indexing.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file type is supported
        """
        supported_extensions = {'.md', '.txt'}
        file_extension = Path(file_path).suffix.lower()
        return file_extension in supported_extensions
    
    def _combine_metadata(self, parse_result, path_obj: Path) -> Dict[str, Any]:
        """
        Combine metadata from parsing result and file system.
        
        Args:
            parse_result: Result from document parsing
            path_obj: Path object for the file
            
        Returns:
            Combined metadata dictionary
        """
        # Start with file system metadata
        file_stat = path_obj.stat()
        metadata = {
            "file_name": path_obj.name,
            "file_extension": path_obj.suffix.lower(),
            "file_size_bytes": file_stat.st_size,
            "file_created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "file_modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "absolute_path": str(path_obj.absolute())
        }
        
        # Add parsing metadata if available
        if parse_result.metadata:
            # Merge parser metadata, avoiding conflicts
            for key, value in parse_result.metadata.items():
                # Prefix parser metadata to avoid conflicts
                parser_key = f"parser_{key}" if key not in metadata else f"parsed_{key}"
                metadata[parser_key] = value
        
        # Add keywords as metadata if available
        if parse_result.keywords:
            metadata["extracted_keywords"] = ", ".join(parse_result.keywords)
            metadata["keyword_count"] = str(len(parse_result.keywords))
        
        # Add parsing statistics
        if parse_result.parsing_stats:
            metadata["parsing_duration_ms"] = str(parse_result.parsing_stats.get("parsing_time", 0))
            metadata["parser_type"] = str(parse_result.parsing_stats.get("parser_type", "unknown"))
        
        # Generate content hash for change detection
        if parse_result.content:
            content_hash = hashlib.sha256(parse_result.content.encode('utf-8')).hexdigest()
            metadata["content_hash"] = content_hash
        
        # Ensure all metadata values are strings
        normalized_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                normalized_metadata[key] = str(value)
            else:
                normalized_metadata[key] = str(value)
        
        return normalized_metadata
    
    async def get_indexing_status(self, file_path: str) -> Dict[str, Any]:
        """
        Get indexing status for a specific file.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            Status information dictionary
        """
        try:
            existing_doc = await self.database_manager.doc_queries.get_document_by_path(file_path)
            
            if not existing_doc:
                return {
                    "indexed": False,
                    "file_path": file_path
                }
            
            # Check if file has been modified since indexing
            path_obj = Path(file_path)
            file_exists = path_obj.exists()
            needs_reindex = False
            
            if file_exists:
                file_mtime = datetime.fromtimestamp(path_obj.stat().st_mtime)
                needs_reindex = file_mtime > existing_doc.modified_at
            
            return {
                "indexed": True,
                "document_id": existing_doc.id,
                "file_path": file_path,
                "file_exists": file_exists,
                "needs_reindex": needs_reindex,
                "indexed_at": existing_doc.indexed_at.isoformat() if existing_doc.indexed_at else None,
                "last_modified": existing_doc.modified_at.isoformat(),
                "file_size_bytes": existing_doc.file_size
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get indexing status: {e}")
            return {
                "indexed": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def get_supported_file_types(self) -> list[str]:
        """
        Get list of supported file types.
        
        Returns:
            List of supported file extensions
        """
        return [".md", ".txt"]