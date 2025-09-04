"""
Unit tests for indexDocument MCP tool.

This test suite covers the indexDocument tool functionality,
parameter validation, error handling, and integration with
the parser and database systems.
"""

import asyncio
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.tools.indexDocument import IndexDocumentTool
from src.tools.base import ToolResult, ToolValidationError, ToolExecutionError
from src.database.database_manager import DocumentManager
from src.parsers.parser_factory import ParserFactory
from src.parsers.base import ParserResult


class TestIndexDocumentTool:
    """Test suite for IndexDocumentTool."""
    
    @pytest.fixture
    async def mock_database_manager(self):
        """Create a mock database manager."""
        mock_dm = AsyncMock(spec=DocumentManager)
        mock_dm.doc_queries = AsyncMock()
        mock_dm.doc_queries.get_document_by_path = AsyncMock()
        mock_dm.index_document = AsyncMock()
        return mock_dm
    
    @pytest.fixture
    def mock_parser_factory(self):
        """Create a mock parser factory."""
        mock_pf = MagicMock(spec=ParserFactory)
        mock_pf.parse_file = AsyncMock()
        return mock_pf
    
    @pytest.fixture
    def index_tool(self, mock_database_manager, mock_parser_factory):
        """Create IndexDocumentTool instance with mocked dependencies."""
        return IndexDocumentTool(
            database_manager=mock_database_manager,
            parser_factory=mock_parser_factory
        )
    
    @pytest.fixture
    def temp_text_file(self):
        """Create a temporary text file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document with some content.")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def temp_markdown_file(self):
        """Create a temporary markdown file for testing."""
        content = """# Test Document

This is a **test** markdown document with:
- Lists
- And other content

## Section 2
More content here.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_tool_metadata(self, index_tool):
        """Test tool metadata properties."""
        assert index_tool.get_tool_name() == "indexDocument"
        assert "Index a document file" in index_tool.get_tool_description()
        
        schema = index_tool.get_parameter_schema()
        assert schema["type"] == "object"
        assert "file_path" in schema["required"]
        assert "file_path" in schema["properties"]
        assert "force_reindex" in schema["properties"]

    def test_parameter_validation_valid(self, index_tool):
        """Test parameter validation with valid parameters."""
        params = {"file_path": "/path/to/file.txt"}
        validated = index_tool.validate_parameters(params)
        assert validated["file_path"] == "/path/to/file.txt"
        assert validated["force_reindex"] is False  # Default value

    def test_parameter_validation_with_force_reindex(self, index_tool):
        """Test parameter validation with force_reindex."""
        params = {"file_path": "/path/to/file.txt", "force_reindex": True}
        validated = index_tool.validate_parameters(params)
        assert validated["file_path"] == "/path/to/file.txt"
        assert validated["force_reindex"] is True

    def test_parameter_validation_missing_required(self, index_tool):
        """Test parameter validation with missing required parameter."""
        params = {"force_reindex": True}  # Missing file_path
        
        with pytest.raises(ToolValidationError) as exc_info:
            index_tool.validate_parameters(params)
        
        assert "Missing required parameter: file_path" in str(exc_info.value)

    def test_parameter_validation_invalid_type(self, index_tool):
        """Test parameter validation with invalid type."""
        params = {"file_path": 123}  # Should be string
        
        with pytest.raises(ToolValidationError) as exc_info:
            index_tool.validate_parameters(params)
        
        assert "must be of type string" in str(exc_info.value)

    def test_supported_file_types(self, index_tool):
        """Test supported file type detection."""
        assert index_tool._is_supported_file_type("test.txt")
        assert index_tool._is_supported_file_type("test.md")
        assert index_tool._is_supported_file_type("TEST.MD")  # Case insensitive
        assert not index_tool._is_supported_file_type("test.pdf")
        assert not index_tool._is_supported_file_type("test.docx")

    @pytest.mark.asyncio
    async def test_execute_file_not_found(self, index_tool):
        """Test execution with non-existent file."""
        params = {"file_path": "/non/existent/file.txt"}
        
        result = await index_tool.execute(params)
        
        assert not result.success
        assert "File not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_unsupported_file_type(self, index_tool):
        """Test execution with unsupported file type."""
        # Create temp file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            params = {"file_path": temp_path}
            result = await index_tool.execute(params)
            
            assert not result.success
            assert "Unsupported file type" in result.error
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_execute_file_too_large(self, index_tool):
        """Test execution with file that's too large."""
        # Create a large temporary file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            # Write more than 10MB
            f.write("x" * (11 * 1024 * 1024))
            temp_path = f.name
        
        try:
            params = {"file_path": temp_path}
            result = await index_tool.execute(params)
            
            assert not result.success
            assert "File too large" in result.error
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_execute_successful_indexing(self, index_tool, mock_database_manager, mock_parser_factory, temp_text_file):
        """Test successful document indexing."""
        # Setup mocks
        mock_parser_factory.parse_file.return_value = ParserResult(
            success=True,
            content="This is a test document with some content.",
            metadata={"title": "Test Document"},
            extracted_data={"keywords": ["test", "document", "content"]},
            parsing_stats={"parser_type": "text", "parsing_time": 10}
        )
        
        mock_database_manager.doc_queries.get_document_by_path.return_value = None
        mock_database_manager.index_document.return_value = 123
        
        params = {"file_path": temp_text_file}
        result = await index_tool.execute(params)
        
        assert result.success
        assert result.data["status"] == "indexed"
        assert result.data["document_id"] == 123
        assert result.data["file_path"] == temp_text_file
        assert "content_length" in result.data
        assert "keywords_extracted" in result.data

    @pytest.mark.asyncio
    async def test_execute_already_indexed_no_changes(self, index_tool, mock_database_manager, mock_parser_factory, temp_text_file):
        """Test execution with already indexed file that hasn't changed."""
        # Mock existing document
        mock_doc = MagicMock()
        mock_doc.id = 456
        mock_doc.modified_at = datetime.now()  # Recent modification
        mock_doc.indexed_at = datetime.now()
        
        mock_database_manager.doc_queries.get_document_by_path.return_value = mock_doc
        
        params = {"file_path": temp_text_file}
        result = await index_tool.execute(params)
        
        assert result.success
        assert result.data["status"] == "already_indexed"
        assert result.data["document_id"] == 456
        
        # Should not call parse_file or index_document
        mock_parser_factory.parse_file.assert_not_called()
        mock_database_manager.index_document.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_force_reindex(self, index_tool, mock_database_manager, mock_parser_factory, temp_text_file):
        """Test execution with force_reindex=True."""
        # Mock existing document
        mock_doc = MagicMock()
        mock_doc.id = 456
        mock_doc.created_at = datetime.now()
        mock_doc.modified_at = datetime.now()
        
        mock_database_manager.doc_queries.get_document_by_path.return_value = mock_doc
        
        # Setup parser mock
        mock_parser_factory.parse_file.return_value = ParserResult(
            success=True,
            content="Updated content",
            metadata={"title": "Updated Document"}
        )
        
        mock_database_manager.index_document.return_value = 456
        
        params = {"file_path": temp_text_file, "force_reindex": True}
        result = await index_tool.execute(params)
        
        assert result.success
        assert result.data["status"] == "reindexed"
        
        # Should call parse_file and index_document even with existing doc
        mock_parser_factory.parse_file.assert_called_once()
        mock_database_manager.index_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_parse_failure(self, index_tool, mock_database_manager, mock_parser_factory, temp_text_file):
        """Test execution when parsing fails."""
        mock_database_manager.doc_queries.get_document_by_path.return_value = None
        
        mock_parser_factory.parse_file.return_value = ParserResult(
            success=False,
            error_message="Failed to parse document"
        )
        
        params = {"file_path": temp_text_file}
        result = await index_tool.execute(params)
        
        assert not result.success
        assert "Failed to parse document" in result.error

    @pytest.mark.asyncio
    async def test_execute_empty_content(self, index_tool, mock_database_manager, mock_parser_factory, temp_text_file):
        """Test execution with empty document content."""
        mock_database_manager.doc_queries.get_document_by_path.return_value = None
        
        mock_parser_factory.parse_file.return_value = ParserResult(
            success=True,
            content="   ",  # Only whitespace
            metadata={}
        )
        
        params = {"file_path": temp_text_file}
        result = await index_tool.execute(params)
        
        assert not result.success
        assert "empty or contains no readable content" in result.error

    @pytest.mark.asyncio
    async def test_execute_database_failure(self, index_tool, mock_database_manager, mock_parser_factory, temp_text_file):
        """Test execution when database indexing fails."""
        mock_database_manager.doc_queries.get_document_by_path.return_value = None
        
        mock_parser_factory.parse_file.return_value = ParserResult(
            success=True,
            content="Valid content",
            metadata={}
        )
        
        mock_database_manager.index_document.return_value = None  # Failure
        
        params = {"file_path": temp_text_file}
        result = await index_tool.execute(params)
        
        assert not result.success
        assert "Failed to index document in database" in result.error

    def test_combine_metadata(self, index_tool):
        """Test metadata combination from parsing result and file system."""
        temp_path = Path(__file__)  # Use this file for testing
        
        parse_result = ParserResult(
            success=True,
            content="Test content",
            metadata={"title": "Test Title", "author": "Test Author"},
            extracted_data={"keywords": ["test", "content"]},
            parsing_stats={"parser_type": "markdown", "parsing_time": 15}
        )
        
        combined = index_tool._combine_metadata(parse_result, temp_path)
        
        # Check file system metadata
        assert "file_name" in combined
        assert "file_extension" in combined
        assert "file_size_bytes" in combined
        assert "absolute_path" in combined
        
        # Check parser metadata with prefix
        assert "parser_title" in combined
        assert "parser_author" in combined
        
        # Check extracted data
        assert "extracted_keywords" in combined
        
        # Check parsing stats
        assert "parser_type" in combined
        assert "parsing_duration_ms" in combined

    @pytest.mark.asyncio
    async def test_get_indexing_status_not_indexed(self, index_tool, mock_database_manager):
        """Test getting indexing status for non-indexed file."""
        mock_database_manager.doc_queries.get_document_by_path.return_value = None
        
        status = await index_tool.get_indexing_status("/path/to/file.txt")
        
        assert not status["indexed"]
        assert status["file_path"] == "/path/to/file.txt"

    @pytest.mark.asyncio
    async def test_get_indexing_status_indexed(self, index_tool, mock_database_manager):
        """Test getting indexing status for indexed file."""
        mock_doc = MagicMock()
        mock_doc.id = 123
        mock_doc.indexed_at = datetime.now()
        mock_doc.modified_at = datetime.now()
        mock_doc.file_size = 1024
        
        mock_database_manager.doc_queries.get_document_by_path.return_value = mock_doc
        
        status = await index_tool.get_indexing_status(__file__)  # This file exists
        
        assert status["indexed"]
        assert status["document_id"] == 123
        assert status["file_exists"]
        assert "indexed_at" in status

    def test_get_supported_file_types(self, index_tool):
        """Test getting supported file types."""
        types = index_tool.get_supported_file_types()
        assert ".md" in types
        assert ".txt" in types
        assert len(types) == 2

    @pytest.mark.asyncio
    async def test_tool_performance_metrics(self, index_tool, mock_database_manager, mock_parser_factory, temp_text_file):
        """Test that tool tracks performance metrics correctly."""
        # Setup successful execution
        mock_parser_factory.parse_file.return_value = ParserResult(
            success=True,
            content="Test content",
            metadata={}
        )
        
        mock_database_manager.doc_queries.get_document_by_path.return_value = None
        mock_database_manager.index_document.return_value = 123
        
        # Execute tool
        params = {"file_path": temp_text_file}
        result = await index_tool.execute(params)
        
        # Check performance tracking
        info = index_tool.get_tool_info()
        assert info["performance"]["execution_count"] == 1
        assert info["performance"]["error_count"] == 0
        assert info["performance"]["total_execution_time_ms"] > 0
        assert result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_tool_error_tracking(self, index_tool):
        """Test that tool tracks errors correctly."""
        # Execute with invalid parameters to trigger error
        params = {}  # Missing required file_path
        result = await index_tool.execute(params)
        
        assert not result.success
        
        # Check error tracking
        info = index_tool.get_tool_info()
        assert info["performance"]["execution_count"] == 1
        assert info["performance"]["error_count"] == 1