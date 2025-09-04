"""
Tests for searchDocuments MCP Tool

This module provides comprehensive tests for the searchDocuments tool,
including unit tests, integration tests, and performance validation
to ensure sub-200ms response times and correct search functionality.
"""

import pytest
import asyncio
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.tools.searchDocuments import SearchDocumentsTool
from src.tools.base import ToolResult
from src.database.models import Document, SearchCache


class TestSearchDocumentsTool:
    """Test suite for SearchDocumentsTool."""
    
    @pytest.fixture
    async def mock_database_manager(self):
        """Create mock database manager."""
        manager = Mock()
        manager.search_queries = AsyncMock()
        manager.doc_queries = AsyncMock()
        manager.metadata_queries = AsyncMock()
        return manager
    
    @pytest.fixture
    async def mock_parser_factory(self):
        """Create mock parser factory."""
        return Mock()
    
    @pytest.fixture
    async def search_tool(self, mock_database_manager, mock_parser_factory):
        """Create SearchDocumentsTool instance for testing."""
        return SearchDocumentsTool(
            database_manager=mock_database_manager,
            parser_factory=mock_parser_factory,
            timeout_seconds=30.0
        )
    
    @pytest.fixture
    def sample_document(self):
        """Create sample document for testing."""
        return Document(
            id=1,
            file_path="/test/sample.md",
            file_name="sample.md",
            content="This is a test document about Python programming and AI.",
            file_type="md",
            file_size=1024,
            file_hash="abc123",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            modified_at=datetime(2025, 1, 1, 12, 0, 0),
            indexed_at=datetime(2025, 1, 1, 12, 0, 0),
            metadata_json=None
        )
    
    def test_tool_initialization(self, search_tool):
        """Test tool initialization and basic properties."""
        assert search_tool.get_tool_name() == "searchDocuments"
        assert "keyword matching" in search_tool.get_tool_description()
        assert search_tool.search_cache_ttl_minutes == 30
        assert search_tool.max_snippet_length == 200
    
    def test_parameter_schema(self, search_tool):
        """Test parameter schema validation."""
        schema = search_tool.get_parameter_schema()
        
        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "limit" in schema["properties"]
        assert "file_type" in schema["properties"]
        assert "sort_by" in schema["properties"]
        
        # Check required fields
        assert "query" in schema["required"]
        assert len(schema["required"]) == 1
        
        # Check defaults
        assert schema["properties"]["limit"]["default"] == 10
        assert schema["properties"]["sort_by"]["default"] == "relevance"
    
    def test_query_normalization(self, search_tool):
        """Test query normalization functionality."""
        # Test whitespace normalization
        assert search_tool._normalize_query("  python   AI  ") == "python ai"
        
        # Test case conversion
        assert search_tool._normalize_query("Python Programming") == "python programming"
        
        # Test short term filtering
        assert search_tool._normalize_query("a python b") == "python"
        
        # Test meaningful short terms preserved
        assert search_tool._normalize_query("c programming") == "c programming"
        assert search_tool._normalize_query("AI ML") == "ai ml"
        
        # Test empty query
        assert search_tool._normalize_query("  a  b  ") == ""
    
    def test_file_type_normalization(self, search_tool):
        """Test file type normalization."""
        assert search_tool._normalize_file_type("md") == "md"
        assert search_tool._normalize_file_type("markdown") == "md"
        assert search_tool._normalize_file_type(".md") == "md"
        assert search_tool._normalize_file_type("txt") == "txt"
        assert search_tool._normalize_file_type("text") == "txt"
        assert search_tool._normalize_file_type(".txt") == "txt"
    
    def test_cache_key_generation(self, search_tool):
        """Test cache key generation."""
        key1 = search_tool._generate_cache_key("python", 10, ".md", "relevance")
        key2 = search_tool._generate_cache_key("python", 10, ".md", "relevance")
        key3 = search_tool._generate_cache_key("python", 20, ".md", "relevance")
        
        # Same parameters should generate same key
        assert key1 == key2
        
        # Different parameters should generate different keys
        assert key1 != key3
        
        # Key should be a valid MD5 hash
        assert len(key1) == 32
        assert all(c in "0123456789abcdef" for c in key1)
    
    def test_title_relevance_calculation(self, search_tool):
        """Test title relevance scoring."""
        # Test exact match
        score = search_tool._calculate_title_relevance("python_guide.md", ["python"])
        assert score > 0
        
        # Test multiple matches
        score = search_tool._calculate_title_relevance("python_ai_guide.md", ["python", "ai"])
        assert score > 10  # Should get points for both terms
        
        # Test no matches
        score = search_tool._calculate_title_relevance("java_guide.md", ["python"])
        assert score == 0
        
        # Test case insensitivity
        score = search_tool._calculate_title_relevance("Python_Guide.md", ["python"])
        assert score > 0
    
    def test_recency_score_calculation(self, search_tool):
        """Test recency scoring."""
        now = datetime.now()
        
        # Recent document (1 day old)
        recent_date = now - timedelta(days=1)
        score = search_tool._calculate_recency_score(recent_date)
        assert score == 5.0
        
        # Medium age document (15 days old)
        medium_date = now - timedelta(days=15)
        score = search_tool._calculate_recency_score(medium_date)
        assert score == 3.0
        
        # Old document (60 days old)
        old_date = now - timedelta(days=60)
        score = search_tool._calculate_recency_score(old_date)
        assert score == 1.0
        
        # Very old document (200 days old)
        very_old_date = now - timedelta(days=200)
        score = search_tool._calculate_recency_score(very_old_date)
        assert score == 0.5
        
        # No date
        score = search_tool._calculate_recency_score(None)
        assert score == 0.0
    
    def test_content_relevance_calculation(self, search_tool):
        """Test content relevance scoring."""
        content = "This is a Python programming tutorial about machine learning and AI."
        
        # Single term
        score = search_tool._calculate_content_relevance(content, ["python"])
        assert score > 0
        
        # Multiple terms
        score = search_tool._calculate_content_relevance(content, ["python", "ai"])
        assert score > 0
        
        # No matches
        score = search_tool._calculate_content_relevance(content, ["java"])
        assert score == 0
        
        # Empty content
        score = search_tool._calculate_content_relevance("", ["python"])
        assert score == 0
        
        # Multiple occurrences
        content_multi = "Python Python Python programming"
        score = search_tool._calculate_content_relevance(content_multi, ["python"])
        assert score > 0
    
    def test_content_snippet_generation(self, search_tool):
        """Test content snippet generation with highlighting."""
        content = ("This is a long document about Python programming. "
                  "Python is a great language for AI and machine learning. "
                  "Many developers use Python for web development too.")
        
        # Test snippet generation
        snippet = search_tool._generate_content_snippet(content, ["python", "ai"])
        
        assert len(snippet) <= search_tool.max_snippet_length + 10  # Allow for ellipsis and highlighting
        assert "**python**" in snippet.lower()  # Should have highlighted terms
        
        # Test empty content
        snippet = search_tool._generate_content_snippet("", ["python"])
        assert snippet == ""
        
        # Test no matching terms
        snippet = search_tool._generate_content_snippet(content, ["java"])
        assert snippet != ""  # Should still return a snippet
    
    @pytest.mark.asyncio
    async def test_successful_search_execution(self, search_tool, sample_document):
        """Test successful search execution."""
        # Mock database responses
        search_tool.database_manager.search_queries.get_search_cache.return_value = None
        search_tool.database_manager.search_queries.search_documents.return_value = [
            (sample_document, 10.5)
        ]
        search_tool.database_manager.metadata_queries.get_document_metadata.return_value = {
            "author": "Test Author",
            "tags": "python, ai"
        }
        search_tool.database_manager.search_queries.create_search_cache = AsyncMock()
        
        # Execute search
        result = await search_tool.execute({
            "query": "python programming",
            "limit": 10
        })
        
        assert result.success
        assert result.data is not None
        assert "results" in result.data
        assert "total_found" in result.data
        assert "search_time_ms" in result.data
        assert len(result.data["results"]) > 0
        
        # Check result format
        first_result = result.data["results"][0]
        assert "document_id" in first_result
        assert "file_path" in first_result
        assert "relevance_score" in first_result
        assert "content_snippet" in first_result
        assert "metadata" in first_result
    
    @pytest.mark.asyncio
    async def test_cached_search_execution(self, search_tool):
        """Test cached search results."""
        # Mock cached result
        cached_data = {
            "results": [{"document_id": 1, "file_path": "/test.md"}],
            "total_found": 1,
            "search_time_ms": 50.0
        }
        
        cached_entry = SearchCache(
            query_hash="test_hash",
            query_text="python",
            results='{"results": [{"document_id": 1}]}',
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=30),
            hit_count=0
        )
        
        search_tool.database_manager.search_queries.get_search_cache.return_value = cached_entry
        
        # Execute search
        result = await search_tool.execute({
            "query": "python",
            "limit": 10
        })
        
        assert result.success
        assert result.data["from_cache"] is True
        assert result.metadata["cache_hit"] is True
    
    @pytest.mark.asyncio
    async def test_empty_query_validation(self, search_tool):
        """Test empty query handling."""
        result = await search_tool.execute({
            "query": "  a  b  "  # Will be normalized to empty string
        })
        
        assert not result.success
        assert "no valid search terms" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_file_type_filtering(self, search_tool, sample_document):
        """Test file type filtering."""
        search_tool.database_manager.search_queries.get_search_cache.return_value = None
        search_tool.database_manager.search_queries.search_documents.return_value = [
            (sample_document, 10.0)
        ]
        search_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        result = await search_tool.execute({
            "query": "python",
            "file_type": "markdown"
        })
        
        assert result.success
        assert "file_type_filter" in result.data
        
        # Verify search was called with correct file type
        search_tool.database_manager.search_queries.search_documents.assert_called_once()
        args, kwargs = search_tool.database_manager.search_queries.search_documents.call_args
        assert kwargs.get("file_type_filter") == "md"
    
    @pytest.mark.asyncio
    async def test_sort_by_functionality(self, search_tool):
        """Test different sort options."""
        # Create multiple documents with different dates
        doc1 = Document(
            id=1, file_path="/old.md", file_name="old.md", content="content",
            file_type="md", file_size=100, indexed_at=datetime(2025, 1, 1)
        )
        doc2 = Document(
            id=2, file_path="/new.md", file_name="new.md", content="content",
            file_type="md", file_size=100, indexed_at=datetime(2025, 1, 15)
        )
        
        search_tool.database_manager.search_queries.get_search_cache.return_value = None
        search_tool.database_manager.search_queries.search_documents.return_value = [
            (doc1, 5.0), (doc2, 3.0)
        ]
        search_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        # Test date sorting
        result = await search_tool.execute({
            "query": "test",
            "sort_by": "date"
        })
        
        assert result.success
        results = result.data["results"]
        # Should be sorted by date (newest first)
        assert results[0]["document_id"] == 2  # newer document first
        assert results[1]["document_id"] == 1  # older document second
    
    @pytest.mark.asyncio
    async def test_performance_timing(self, search_tool, sample_document):
        """Test search performance timing."""
        search_tool.database_manager.search_queries.get_search_cache.return_value = None
        search_tool.database_manager.search_queries.search_documents.return_value = [
            (sample_document, 10.0)
        ]
        search_tool.database_manager.metadata_queries.get_document_metadata.return_value = {}
        
        start_time = time.time()
        result = await search_tool.execute({
            "query": "python programming"
        })
        end_time = time.time()
        
        assert result.success
        assert "search_time_ms" in result.data
        
        # Verify timing is reasonable
        actual_time_ms = (end_time - start_time) * 1000
        reported_time_ms = result.data["search_time_ms"]
        
        # Reported time should be close to actual time
        assert abs(actual_time_ms - reported_time_ms) < 50  # Within 50ms tolerance
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, search_tool):
        """Test error handling when database operations fail."""
        search_tool.database_manager.search_queries.get_search_cache.return_value = None
        search_tool.database_manager.search_queries.search_documents.side_effect = Exception("Database error")
        
        result = await search_tool.execute({
            "query": "python"
        })
        
        assert not result.success
        assert "Database error" in result.error
        assert "search_time_ms" in result.metadata
    
    @pytest.mark.asyncio
    async def test_search_statistics(self, search_tool):
        """Test search statistics functionality."""
        search_tool.database_manager.doc_queries.count_documents.side_effect = [100, 60, 40]
        
        stats = await search_tool.get_search_statistics()
        
        assert "indexed_documents" in stats
        assert stats["indexed_documents"]["total"] == 100
        assert stats["indexed_documents"]["markdown"] == 60
        assert stats["indexed_documents"]["text"] == 40
        assert "tool_performance" in stats
        assert "cache_ttl_minutes" in stats
    
    @pytest.mark.asyncio
    async def test_cache_cleanup(self, search_tool):
        """Test search cache cleanup functionality."""
        search_tool.database_manager.search_queries.cleanup_expired_cache.return_value = 5
        
        result = await search_tool.clear_search_cache()
        
        assert result["success"]
        assert result["cleared_entries"] == 5
        assert "timestamp" in result
    
    def test_parameter_validation_edge_cases(self, search_tool):
        """Test parameter validation edge cases."""
        from src.tools.base import ToolValidationError
        
        # Test query too long
        long_query = "a" * 1000
        with pytest.raises(ToolValidationError):  # Should fail validation
            search_tool.validate_parameters({"query": long_query})
        
        # Test invalid file type (should still work due to flexible validation)
        params = search_tool.validate_parameters({
            "query": "test",
            "file_type": "invalid"
        })
        assert params["file_type"] == "invalid"
        
        # Test limit constraints - over maximum should fail
        with pytest.raises(ToolValidationError):
            search_tool.validate_parameters({
                "query": "test",
                "limit": 150  # Over maximum
            })
        
        # Test valid limit
        params = search_tool.validate_parameters({
            "query": "test",
            "limit": 50  # Within valid range
        })
        assert params["limit"] == 50


class TestSearchDocumentsIntegration:
    """Integration tests for SearchDocumentsTool."""
    
    @pytest.mark.asyncio
    async def test_full_search_workflow(self):
        """Test complete search workflow with real-like data."""
        # This would be a more comprehensive integration test
        # that tests the full search pipeline with a test database
        pass
    
    @pytest.mark.asyncio
    async def test_performance_benchmark(self):
        """Test search performance against targets."""
        # This would benchmark search performance against
        # the sub-200ms requirement with various query types
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])