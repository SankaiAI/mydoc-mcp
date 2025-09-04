"""
Tests for getDocument MCP Tool

Comprehensive test suite for the getDocument tool covering:
- Document retrieval by ID and file path
- Parameter validation and error handling  
- Content formatting (json, markdown, text)
- Metadata inclusion and exclusion
- Performance requirements (sub-200ms)
- Content size management and truncation
- File statistics and content analysis
"""

import pytest
import asyncio
import tempfile
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.tools.getDocument import GetDocumentTool
from src.tools.base import ToolResult
from src.database.models import Document


class TestGetDocumentTool:
    """Test suite for GetDocumentTool."""
    
    @pytest.fixture
    async def mock_database_manager(self):
        """Create mock database manager."""
        manager = AsyncMock()
        manager.doc_queries = AsyncMock()
        manager.metadata_queries = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_parser_factory(self):
        """Create mock parser factory."""
        return MagicMock()
    
    @pytest.fixture
    def sample_document(self):
        """Create sample document for testing."""
        return Document(
            id=1,
            file_path="/test/sample.md",
            file_name="sample.md",
            content="# Test Document\n\nThis is a **test** document with some content.\n\n- Item 1\n- Item 2",
            file_type="md",
            file_size=85,
            file_hash="abc123",
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            modified_at=datetime(2025, 1, 1, 12, 0, 0),
            indexed_at=datetime(2025, 1, 1, 12, 30, 0),
            metadata_json='{"title": "Test Document", "author": "Test Author"}'
        )
    
    @pytest.fixture
    async def get_document_tool(self, mock_database_manager, mock_parser_factory):
        """Create GetDocumentTool instance."""
        tool = GetDocumentTool(
            database_manager=mock_database_manager,
            parser_factory=mock_parser_factory
        )
        return tool
    
    def test_tool_metadata(self, get_document_tool):
        """Test tool metadata and schema."""
        assert get_document_tool.get_tool_name() == "getDocument"
        
        description = get_document_tool.get_tool_description()
        assert "retrieve" in description.lower()
        assert "document" in description.lower()
        
        schema = get_document_tool.get_parameter_schema()
        assert schema["type"] == "object"
        assert "properties" in schema
        
        # Check required parameters structure
        assert "oneOf" in schema
        required_options = schema["oneOf"]
        assert len(required_options) == 2
        assert {"required": ["document_id"]} in required_options
        assert {"required": ["file_path"]} in required_options
        
        # Check parameter properties
        properties = schema["properties"]
        assert "document_id" in properties
        assert "file_path" in properties
        assert "include_content" in properties
        assert "format" in properties
        assert "include_metadata" in properties
        assert "max_content_length" in properties
        
        # Check format enum
        assert properties["format"]["enum"] == ["json", "markdown", "text"]
    
    @pytest.mark.asyncio
    async def test_retrieve_document_by_id_success(self, get_document_tool, sample_document):
        """Test successful document retrieval by ID."""
        # Setup mock
        get_document_tool.database_manager.doc_queries.get_document.return_value = sample_document
        get_document_tool.database_manager.metadata_queries.get_document_metadata.return_value = {
            "title": "Test Document",
            "author": "Test Author"
        }
        
        # Execute tool
        result = await get_document_tool.execute({
            "document_id": 1,
            "include_content": True,
            "format": "json",
            "include_metadata": True
        })
        
        # Verify result
        assert result.success is True
        assert result.data is not None
        
        data = result.data
        assert data["document_id"] == 1
        assert data["file_path"] == "/test/sample.md"
        assert data["file_name"] == "sample.md"
        assert data["file_type"] == "md"
        assert data["file_size_bytes"] == 85
        assert data["retrieval_method"] == "by_id"
        
        # Check content
        assert "content" in data
        assert "Test Document" in data["content"]
        assert data["content_format"] == "json"
        assert data["content_truncated"] is False
        
        # Check metadata
        assert "metadata" in data
        assert data["metadata"]["title"] == "Test Document"
        assert data["parsed_metadata"]["title"] == "Test Document"
        
        # Check file stats
        assert "file_stats" in data
        assert data["file_stats"]["size_bytes"] == 85
        assert "content_statistics" in data["file_stats"]
        
        # Verify database calls
        get_document_tool.database_manager.doc_queries.get_document.assert_called_once_with(1)
        get_document_tool.database_manager.metadata_queries.get_document_metadata.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_retrieve_document_by_path_success(self, get_document_tool, sample_document):
        """Test successful document retrieval by file path."""
        # Setup mock
        get_document_tool.database_manager.doc_queries.get_document_by_path.return_value = sample_document
        get_document_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        # Execute tool
        result = await get_document_tool.execute({
            "file_path": "/test/sample.md",
            "include_content": True,
            "format": "markdown"
        })
        
        # Verify result
        assert result.success is True
        assert result.data["retrieval_method"] == "by_path"
        assert result.data["content_format"] == "markdown"
        
        # Verify database call
        get_document_tool.database_manager.doc_queries.get_document_by_path.assert_called_once_with("/test/sample.md")
    
    @pytest.mark.asyncio
    async def test_document_not_found_by_id(self, get_document_tool):
        """Test handling when document not found by ID."""
        # Setup mock to return None
        get_document_tool.database_manager.doc_queries.get_document.return_value = None
        
        # Execute tool
        result = await get_document_tool.execute({
            "document_id": 999
        })
        
        # Verify error result
        assert result.success is False
        assert "not found" in result.error
        assert "999" in result.error
        
        # Verify metadata
        assert result.metadata["document_id"] == 999
        assert result.metadata["retrieval_method"] == "by_id"
    
    @pytest.mark.asyncio
    async def test_document_not_found_by_path(self, get_document_tool):
        """Test handling when document not found by path."""
        # Setup mock to return None
        get_document_tool.database_manager.doc_queries.get_document_by_path.return_value = None
        
        # Execute tool
        result = await get_document_tool.execute({
            "file_path": "/nonexistent/file.md"
        })
        
        # Verify error result
        assert result.success is False
        assert "not found" in result.error
        assert "/nonexistent/file.md" in result.error
        
        # Verify metadata
        assert result.metadata["file_path"] == "/nonexistent/file.md"
        assert result.metadata["retrieval_method"] == "by_path"
    
    @pytest.mark.asyncio
    async def test_parameter_validation_errors(self, get_document_tool):
        """Test parameter validation error cases."""
        
        # Test missing both parameters
        result = await get_document_tool.execute({})
        assert result.success is False
        assert "required" in result.error
        
        # Test both parameters provided
        result = await get_document_tool.execute({
            "document_id": 1,
            "file_path": "/test/file.md"
        })
        assert result.success is False
        assert "Only one" in result.error
    
    @pytest.mark.asyncio
    async def test_content_formatting_options(self, get_document_tool, sample_document):
        """Test different content formatting options."""
        get_document_tool.database_manager.doc_queries.get_document.return_value = sample_document
        get_document_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        # Test JSON format (default)
        result = await get_document_tool.execute({
            "document_id": 1,
            "format": "json"
        })
        assert result.success is True
        assert result.data["content_format"] == "json"
        assert "**test**" in result.data["content"]  # Markdown preserved
        
        # Test markdown format
        result = await get_document_tool.execute({
            "document_id": 1,
            "format": "markdown"
        })
        assert result.success is True
        assert result.data["content_format"] == "markdown"
        
        # Test text format (markdown stripped)
        result = await get_document_tool.execute({
            "document_id": 1,
            "format": "text"
        })
        assert result.success is True
        assert result.data["content_format"] == "text"
        # Should strip markdown formatting
        assert "**test**" not in result.data["content"]
        assert "test" in result.data["content"]
    
    @pytest.mark.asyncio
    async def test_content_exclusion(self, get_document_tool, sample_document):
        """Test excluding content from response."""
        get_document_tool.database_manager.doc_queries.get_document.return_value = sample_document
        get_document_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        result = await get_document_tool.execute({
            "document_id": 1,
            "include_content": False
        })
        
        assert result.success is True
        # Content fields should not be present when content not requested
        assert "content" not in result.data
        assert "content_length" not in result.data
        assert "content_truncated" not in result.data
    
    @pytest.mark.asyncio
    async def test_metadata_exclusion(self, get_document_tool, sample_document):
        """Test excluding metadata from response."""
        get_document_tool.database_manager.doc_queries.get_document.return_value = sample_document
        
        result = await get_document_tool.execute({
            "document_id": 1,
            "include_metadata": False
        })
        
        assert result.success is True
        assert "metadata" not in result.data
        assert "parsed_metadata" not in result.data
        
        # Should not call metadata queries
        get_document_tool.database_manager.metadata_queries.get_document_metadata.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_content_size_limiting(self, get_document_tool, sample_document):
        """Test content size limiting and truncation."""
        # Create document with large content
        large_content = "A" * 1000 + "B" * 500  # 1500 characters
        sample_document.content = large_content
        
        get_document_tool.database_manager.doc_queries.get_document.return_value = sample_document
        get_document_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        # Test content truncation with limit
        result = await get_document_tool.execute({
            "document_id": 1,
            "max_content_length": 100
        })
        
        assert result.success is True
        assert result.data["content_truncated"] is True
        assert len(result.data["content"]) > 100  # Includes truncation indicator
        assert "[Content truncated due to size limits]" in result.data["content"]
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, get_document_tool, sample_document):
        """Test performance tracking and timing."""
        get_document_tool.database_manager.doc_queries.get_document.return_value = sample_document
        get_document_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        result = await get_document_tool.execute({
            "document_id": 1
        })
        
        assert result.success is True
        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 0  # Can be 0.0 for very fast operations
        
        # Check performance metadata
        assert result.metadata["performance_target_met"] is not None
        assert result.data["retrieval_time_ms"] is not None
        assert result.data["retrieval_time_ms"] >= 0  # Can be 0.0 for very fast operations
    
    @pytest.mark.asyncio
    async def test_file_statistics_generation(self, get_document_tool, sample_document):
        """Test file statistics generation."""
        get_document_tool.database_manager.doc_queries.get_document.return_value = sample_document
        get_document_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        result = await get_document_tool.execute({
            "document_id": 1
        })
        
        assert result.success is True
        
        # Check file stats
        file_stats = result.data["file_stats"]
        assert file_stats["size_bytes"] == 85
        assert file_stats["size_readable"] == "85.0 B"
        assert file_stats["extension"] == ".md"
        
        # Check content statistics
        content_stats = file_stats["content_statistics"]
        assert content_stats["lines"] > 0
        assert content_stats["words"] > 0
        assert content_stats["characters"] > 0  # Should have some characters
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, get_document_tool):
        """Test handling of database errors."""
        # Setup mock to raise exception
        get_document_tool.database_manager.doc_queries.get_document.side_effect = Exception("Database error")
        
        result = await get_document_tool.execute({
            "document_id": 1
        })
        
        assert result.success is False
        assert "Database error" in result.error
        assert result.execution_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_metadata_error_handling(self, get_document_tool, sample_document):
        """Test handling of metadata retrieval errors."""
        get_document_tool.database_manager.doc_queries.get_document.return_value = sample_document
        get_document_tool.database_manager.metadata_queries.get_document_metadata.side_effect = Exception("Metadata error")
        
        result = await get_document_tool.execute({
            "document_id": 1,
            "include_metadata": True
        })
        
        # Should still succeed with empty metadata
        assert result.success is True
        assert result.data["metadata"] == {}
        assert result.data["parsed_metadata"] == {}
    
    def test_markdown_stripping(self, get_document_tool):
        """Test markdown formatting removal for text format."""
        test_content = "# Header\n\n**Bold text** and *italic text*\n\n`code` and ```\ncode block\n```\n\n[Link](url)\n\n- List item"
        
        stripped = get_document_tool._strip_markdown(test_content)
        
        # Should remove markdown formatting
        assert "# " not in stripped
        assert "**" not in stripped
        assert "*" not in stripped
        assert "`" not in stripped
        assert "[" not in stripped
        assert "- " not in stripped
        
        # Should preserve text content
        assert "Header" in stripped
        assert "Bold text" in stripped
        assert "italic text" in stripped
        assert "code" in stripped
        assert "Link" in stripped
        assert "List item" in stripped
    
    def test_file_size_formatting(self, get_document_tool):
        """Test human-readable file size formatting."""
        assert get_document_tool._format_file_size(500) == "500.0 B"
        assert get_document_tool._format_file_size(1500) == "1.5 KB"
        assert get_document_tool._format_file_size(2048000) == "2.0 MB"
        assert get_document_tool._format_file_size(1073741824) == "1.0 GB"
    
    @pytest.mark.asyncio
    async def test_empty_content_handling(self, get_document_tool, sample_document):
        """Test handling of documents with empty content."""
        sample_document.content = ""
        
        get_document_tool.database_manager.doc_queries.get_document.return_value = sample_document
        get_document_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        result = await get_document_tool.execute({
            "document_id": 1,
            "include_content": True
        })
        
        assert result.success is True
        assert result.data["content"] == ""
        assert result.data["content_length"] == 0
        assert result.data["content_truncated"] is False
    
    @pytest.mark.asyncio
    async def test_invalid_json_metadata_handling(self, get_document_tool, sample_document):
        """Test handling of invalid JSON in metadata field."""
        sample_document.metadata_json = "invalid json {"
        
        get_document_tool.database_manager.doc_queries.get_document.return_value = sample_document
        get_document_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        result = await get_document_tool.execute({
            "document_id": 1,
            "include_metadata": True
        })
        
        assert result.success is True
        assert result.data["parsed_metadata"] == {}  # Should default to empty dict
    
    @pytest.mark.asyncio
    async def test_tool_statistics(self, get_document_tool):
        """Test tool statistics retrieval."""
        get_document_tool.database_manager.doc_queries.count_documents.side_effect = [100, 60, 40]  # total, md, txt
        
        stats = await get_document_tool.get_document_statistics()
        
        assert stats["indexed_documents"]["total"] == 100
        assert stats["indexed_documents"]["markdown"] == 60
        assert stats["indexed_documents"]["text"] == 40
        assert "tool_performance" in stats
        assert "content_limits" in stats
        assert stats["supported_formats"] == ["json", "markdown", "text"]
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, get_document_tool, sample_document):
        """Test handling of concurrent document retrieval requests."""
        get_document_tool.database_manager.doc_queries.get_document.return_value = sample_document
        get_document_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        # Execute multiple concurrent requests
        tasks = [
            get_document_tool.execute({"document_id": i})
            for i in range(1, 6)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert result.success is True
            assert result.execution_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_performance_requirements(self, get_document_tool, sample_document):
        """Test that tool meets sub-200ms performance requirements."""
        get_document_tool.database_manager.doc_queries.get_document.return_value = sample_document
        get_document_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        # Run multiple tests to check consistency
        execution_times = []
        
        for _ in range(5):
            result = await get_document_tool.execute({
                "document_id": 1,
                "include_content": True,
                "include_metadata": True
            })
            
            assert result.success is True
            execution_times.append(result.execution_time_ms)
        
        # Check that most executions are under 200ms
        fast_executions = [t for t in execution_times if t < 200.0]
        assert len(fast_executions) >= 4  # At least 4 out of 5 should be fast
        
        # Check average performance
        avg_time = sum(execution_times) / len(execution_times)
        assert avg_time < 200.0  # Average should be under 200ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])