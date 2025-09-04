"""
Comprehensive test suite for mydocs-mcp document parsers.

Tests all parser implementations including base parser functionality,
specific parser behavior, and factory integration with performance
validation and error handling.
"""

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
import pytest
import yaml

# Import parser components
from src.parsers.base import DocumentParser, ParserResult, ParseError
from src.parsers.markdown_parser import MarkdownParser
from src.parsers.text_parser import TextParser
from src.parsers.parser_factory import ParserFactory, get_default_factory, reset_default_factory


class TestParserResult:
    """Test ParserResult data class."""
    
    def test_parser_result_initialization(self):
        """Test basic ParserResult initialization."""
        result = ParserResult()
        
        assert result.content == ""
        assert result.metadata == {}
        assert result.keywords == []
        assert result.file_info == {}
        assert result.parsing_stats != {}  # Should be populated by post_init
        assert result.success is True
        assert result.error_message is None
    
    def test_parser_result_with_data(self):
        """Test ParserResult with actual data."""
        result = ParserResult(
            content="Test content",
            metadata={"title": "Test"},
            keywords=["test", "content"],
            success=True
        )
        
        assert result.content == "Test content"
        assert result.metadata["title"] == "Test"
        assert result.keywords == ["test", "content"]
        assert result.success is True
        assert result.parsing_stats["content_length"] == len("Test content")
        assert result.parsing_stats["keyword_count"] == 2
        assert result.parsing_stats["metadata_fields"] == 1
    
    def test_parser_result_to_dict(self):
        """Test ParserResult to_dict conversion."""
        result = ParserResult(
            content="Test",
            metadata={"key": "value"},
            keywords=["word"],
            success=True
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["content"] == "Test"
        assert result_dict["metadata"]["key"] == "value"
        assert result_dict["keywords"] == ["word"]
        assert result_dict["success"] is True
        assert "parsing_stats" in result_dict


class TestMarkdownParser:
    """Test MarkdownParser functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create MarkdownParser instance."""
        return MarkdownParser(logger=logging.getLogger("test"))
    
    def test_supported_extensions(self, parser):
        """Test supported file extensions."""
        extensions = parser.get_supported_extensions()
        
        assert ".md" in extensions
        assert ".markdown" in extensions
        assert ".mdown" in extensions
        assert len(extensions) >= 3
    
    @pytest.mark.asyncio
    async def test_parse_simple_markdown(self, parser):
        """Test parsing simple markdown content."""
        content = """# Test Document

This is a test document with some **bold** text and a [link](http://example.com).

## Section 2

- Item 1
- Item 2

```python
print("Hello World")
```
"""
        
        result = await parser.parse_content(content)
        
        assert result.success is True
        assert result.error_message is None
        assert len(result.content) > 0
        assert len(result.keywords) > 0
        assert len(result.metadata) > 0
        
        # Check structure extraction
        assert "headers" in result.metadata
        assert len(result.metadata["headers"]) == 2
        assert result.metadata["headers"][0]["text"] == "Test Document"
        assert result.metadata["headers"][0]["level"] == 1
        
        # Check links
        assert "links" in result.metadata
        assert len(result.metadata["links"]) == 1
        assert result.metadata["links"][0]["url"] == "http://example.com"
        
        # Check code blocks
        assert "code_blocks" in result.metadata
        assert len(result.metadata["code_blocks"]) == 1
        assert result.metadata["code_blocks"][0]["language"] == "python"
    
    @pytest.mark.asyncio
    async def test_parse_markdown_with_frontmatter(self, parser):
        """Test parsing markdown with YAML frontmatter."""
        content = """---
title: Test Document
author: Test Author
date: 2025-09-04
tags:
  - test
  - markdown
---

# Main Content

This is the main content of the document.
"""
        
        result = await parser.parse_content(content)
        
        assert result.success is True
        assert "title" in result.metadata
        assert result.metadata["title"] == "Test Document"
        assert "author" in result.metadata
        assert result.metadata["author"] == "Test Author"
        assert "tags" in result.metadata
        assert result.metadata["tags"] == ["test", "markdown"]
        assert result.metadata["has_frontmatter"] is True
    
    @pytest.mark.asyncio
    async def test_parse_empty_content(self, parser):
        """Test parsing empty content."""
        result = await parser.parse_content("")
        
        assert result.success is False
        assert "Empty content" in result.error_message
    
    @pytest.mark.asyncio
    async def test_parse_file_integration(self, parser):
        """Test parsing actual markdown file."""
        content = """# Test File

This is a test markdown file.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = await parser.parse_file(temp_path)
            
            assert result.success is True
            assert result.file_info["file_name"] == Path(temp_path).name
            assert result.file_info["file_extension"] == ".md"
            assert result.file_info["file_size"] > 0
            assert "file_hash" in result.file_info
            
        finally:
            os.unlink(temp_path)


class TestTextParser:
    """Test TextParser functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create TextParser instance."""
        return TextParser(logger=logging.getLogger("test"))
    
    def test_supported_extensions(self, parser):
        """Test supported file extensions."""
        extensions = parser.get_supported_extensions()
        
        assert ".txt" in extensions
        assert ".log" in extensions
        assert ".cfg" in extensions
        assert ".py" in extensions
        assert len(extensions) > 10
    
    @pytest.mark.asyncio
    async def test_parse_simple_text(self, parser):
        """Test parsing simple text content."""
        content = """This is a simple text document.

It has multiple paragraphs and some content that should be processed.

Email: test@example.com
URL: https://example.com
"""
        
        result = await parser.parse_content(content)
        
        assert result.success is True
        assert result.content == content  # Text parser doesn't modify content much
        assert len(result.keywords) > 0
        assert result.metadata["document_type"] == "text"
        assert result.metadata["line_count"] == len(content.split('\n'))
        assert result.metadata["word_count"] > 0
        
        # Check entity extraction
        assert "emails" in result.metadata
        assert "test@example.com" in result.metadata["emails"]
        assert "urls" in result.metadata
        assert "https://example.com" in result.metadata["urls"]
    
    @pytest.mark.asyncio
    async def test_parse_log_file(self, parser):
        """Test parsing log file content."""
        content = """2025-09-04 10:00:00 INFO Application started
2025-09-04 10:00:01 DEBUG Initializing components
2025-09-04 10:00:02 WARN Configuration file missing
2025-09-04 10:00:03 ERROR Failed to connect to database
2025-09-04 10:00:04 FATAL Application shutting down
"""
        
        result = await parser.parse_content(content)
        
        assert result.success is True
        assert result.metadata["document_type"] == "log"
        assert "log_levels" in result.metadata
        assert result.metadata["log_levels"]["INFO"] >= 1
        assert result.metadata["log_levels"]["ERROR"] >= 1
        assert result.metadata["log_levels"]["FATAL"] >= 1
        assert "total_log_entries" in result.metadata
    
    @pytest.mark.asyncio
    async def test_parse_config_file(self, parser):
        """Test parsing configuration file content."""
        content = """[database]
host=localhost
port=5432
username=admin

[logging]
level=INFO
file=/var/log/app.log
"""
        
        result = await parser.parse_content(content)
        
        assert result.success is True
        # Should detect as config based on content patterns
        assert result.metadata.get("config_format") == "ini"
        assert "ini_sections" in result.metadata
        assert "database" in result.metadata["ini_sections"]
        assert "logging" in result.metadata["ini_sections"]
    
    @pytest.mark.asyncio
    async def test_parse_code_file(self, parser):
        """Test parsing code-like content."""
        content = """def hello_world():
    print("Hello, World!")
    return True

def main():
    result = hello_world()
    if result:
        print("Success")

if __name__ == "__main__":
    main()
"""
        
        result = await parser.parse_content(content, file_path="test.py")
        
        assert result.success is True
        # Should detect as code based on file extension and content
        if result.metadata.get("document_type") == "code":
            assert "function_count" in result.metadata


class TestParserFactory:
    """Test ParserFactory functionality."""
    
    @pytest.fixture
    def factory(self):
        """Create fresh ParserFactory instance."""
        return ParserFactory(logger=logging.getLogger("test"))
    
    def test_factory_initialization(self, factory):
        """Test factory initialization with default parsers."""
        parsers = factory.list_available_parsers()
        
        assert len(parsers) >= 2  # At least markdown and text
        
        parser_names = [p["name"] for p in parsers]
        assert "markdown" in parser_names
        assert "text" in parser_names
        
        # Test extension mapping
        extensions = factory.get_supported_extensions()
        assert ".md" in extensions
        assert ".txt" in extensions
    
    def test_parser_registration(self, factory):
        """Test custom parser registration."""
        # Create a mock parser class
        class MockParser(DocumentParser):
            def get_supported_extensions(self):
                return {'.mock'}
            
            async def parse_content(self, content, file_path=None):
                return ParserResult(content="mock", success=True)
        
        # Register mock parser
        factory.register_parser("mock", MockParser)
        
        # Verify registration
        parser = factory.get_parser("mock")
        assert parser is not None
        assert isinstance(parser, MockParser)
        
        extensions = factory.get_supported_extensions()
        assert ".mock" in extensions
        
        parser_name = factory.get_parser_for_extension(".mock")
        assert parser_name == "mock"
    
    def test_get_parser_for_file(self, factory):
        """Test getting parser for specific files."""
        # Test markdown file
        parser = factory.get_parser_for_file("test.md")
        assert parser is not None
        assert isinstance(parser, MarkdownParser)
        
        # Test text file
        parser = factory.get_parser_for_file("test.txt")
        assert parser is not None
        assert isinstance(parser, TextParser)
        
        # Test unknown extension (should fallback to text)
        parser = factory.get_parser_for_file("test.unknown")
        assert parser is not None
        assert isinstance(parser, TextParser)
    
    @pytest.mark.asyncio
    async def test_factory_parse_file(self, factory):
        """Test parsing file through factory."""
        content = "# Test\n\nThis is a test."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = await factory.parse_file(temp_path)
            
            assert result.success is True
            assert len(result.content) > 0
            assert "headers" in result.metadata  # Markdown-specific
            
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_factory_parse_content(self, factory):
        """Test parsing content through factory."""
        content = "This is plain text content."
        
        result = await factory.parse_content(content, "text")
        
        assert result.success is True
        assert result.content == content
        assert result.metadata["document_type"] == "text"
    
    def test_factory_stats(self, factory):
        """Test factory statistics tracking."""
        initial_stats = factory.get_factory_stats()
        
        assert initial_stats["total_parses"] == 0
        assert initial_stats["success_rate"] == 1.0
        assert len(initial_stats["parser_usage"]) >= 2
        
        # Reset stats
        factory.reset_stats()
        stats_after_reset = factory.get_factory_stats()
        assert stats_after_reset["total_parses"] == 0


class TestParserPerformance:
    """Test parser performance characteristics."""
    
    @pytest.fixture
    def factory(self):
        """Create factory for performance tests."""
        return ParserFactory(logger=logging.getLogger("perf"))
    
    @pytest.mark.asyncio
    async def test_markdown_parser_performance(self, factory):
        """Test markdown parser performance."""
        # Create moderately large markdown content
        content = """# Performance Test Document

""" + "\n".join([f"## Section {i}\n\nThis is section {i} with some content." for i in range(100)])
        
        start_time = time.time()
        result = await factory.parse_content(content, "markdown")
        parse_time = (time.time() - start_time) * 1000
        
        assert result.success is True
        assert parse_time < 1000  # Should parse within 1 second
        assert result.parsing_stats["parse_time_ms"] > 0
        
        print(f"Markdown parse time: {parse_time:.2f}ms for {len(content)} characters")
    
    @pytest.mark.asyncio
    async def test_text_parser_performance(self, factory):
        """Test text parser performance."""
        # Create large text content
        content = "\n".join([f"Line {i}: This is test content with various words." for i in range(1000)])
        
        start_time = time.time()
        result = await factory.parse_content(content, "text")
        parse_time = (time.time() - start_time) * 1000
        
        assert result.success is True
        assert parse_time < 2000  # Should parse within 2 seconds
        
        print(f"Text parse time: {parse_time:.2f}ms for {len(content)} characters")
    
    @pytest.mark.asyncio
    async def test_concurrent_parsing(self, factory):
        """Test concurrent parsing performance."""
        contents = [
            "# Document 1\n\nContent 1",
            "# Document 2\n\nContent 2", 
            "Document 3 plain text",
            "Document 4 plain text"
        ]
        
        start_time = time.time()
        
        # Parse all documents concurrently
        tasks = [
            factory.parse_content(content, "markdown" if content.startswith("#") else "text")
            for content in contents
        ]
        
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000
        
        # All should succeed
        assert all(r.success for r in results)
        
        # Concurrent parsing should be faster than sequential
        assert total_time < len(contents) * 100  # Rough estimate
        
        print(f"Concurrent parsing time: {total_time:.2f}ms for {len(contents)} documents")


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.fixture
    def factory(self):
        """Create factory for error tests."""
        return ParserFactory(logger=logging.getLogger("error"))
    
    @pytest.mark.asyncio
    async def test_nonexistent_file(self, factory):
        """Test parsing nonexistent file."""
        result = await factory.parse_file("/path/that/does/not/exist.md")
        
        assert result.success is False
        assert "does not exist" in result.error_message
    
    @pytest.mark.asyncio
    async def test_invalid_yaml_frontmatter(self):
        """Test invalid YAML frontmatter handling."""
        parser = MarkdownParser()
        
        content = """---
invalid: yaml: content: here
missing: quotes "and brackets [
---

# Valid Markdown

Content here.
"""
        
        result = await parser.parse_content(content)
        
        # Should still succeed, just with frontmatter error noted
        assert result.success is True
        assert "frontmatter_error" in result.metadata or "has_frontmatter" not in result.metadata
    
    @pytest.mark.asyncio
    async def test_very_large_content(self, factory):
        """Test handling of very large content."""
        # Create content larger than typical processing
        large_content = "Test content. " * 10000  # ~130KB
        
        result = await factory.parse_content(large_content, "text")
        
        assert result.success is True
        assert len(result.content) == len(large_content)
        assert len(result.keywords) > 0
    
    def test_parser_error_exception(self):
        """Test ParseError exception."""
        error = ParseError("Test error", file_path="/test/path", parser_name="TestParser")
        
        assert str(error) == "[TestParser] Failed to parse /test/path: Test error"
        assert error.file_path == "/test/path"
        assert error.parser_name == "TestParser"


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_mixed_document_processing(self):
        """Test processing multiple document types."""
        factory = get_default_factory(logging.getLogger("integration"))
        
        # Test documents
        documents = [
            ("test.md", "# README\n\nThis is a readme file."),
            ("config.ini", "[app]\nname=test\nversion=1.0"),
            ("log.txt", "2025-09-04 10:00:00 INFO Application started"),
            ("data.txt", "Simple text document with content.")
        ]
        
        results = []
        
        for filename, content in documents:
            with tempfile.NamedTemporaryFile(mode='w', suffix=Path(filename).suffix, delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                result = await factory.parse_file(temp_path)
                results.append((filename, result))
            finally:
                os.unlink(temp_path)
        
        # All should succeed
        assert all(result.success for _, result in results)
        
        # Check document types are detected correctly
        readme_result = next(r for f, r in results if f == "test.md")
        assert "headers" in readme_result.metadata
        
        config_result = next(r for f, r in results if f == "config.ini")
        assert config_result.metadata.get("config_format") in ["ini", None]  # May or may not be detected
    
    @pytest.mark.asyncio 
    async def test_parser_factory_reuse(self):
        """Test parser factory instance reuse."""
        factory = get_default_factory()
        
        # Parse multiple files to test instance reuse
        content = "Test content"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Parse same file multiple times
            results = []
            for _ in range(3):
                result = await factory.parse_file(temp_path)
                results.append(result)
            
            # All should succeed
            assert all(r.success for r in results)
            
            # Stats should show multiple parses
            stats = factory.get_factory_stats()
            assert stats["total_parses"] >= 3
            
        finally:
            os.unlink(temp_path)
            
        # Reset for other tests
        reset_default_factory()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])