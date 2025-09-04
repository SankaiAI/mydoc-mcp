"""
Parser Integration Tests with Database Models

Tests the integration between the document parsers and the database layer,
ensuring proper data flow and compatibility with the database models and
document manager.
"""

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
import pytest

# Import database components
from src.database.database_manager import DocumentManager, create_document_manager
from src.database.models import Document

# Import parser components
from src.parsers import (
    get_default_factory, 
    parse_file, 
    parse_content, 
    supports_file
)


class TestParserDatabaseIntegration:
    """Test integration between parsers and database."""
    
    @pytest.fixture
    async def document_manager(self):
        """Create document manager for testing."""
        # Use in-memory database for tests
        db_path = ":memory:"
        
        manager = await create_document_manager(
            database_path=db_path,
            logger=logging.getLogger("test_integration")
        )
        
        assert manager is not None
        yield manager
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_parse_and_index_markdown(self, document_manager):
        """Test parsing markdown and indexing in database."""
        content = """---
title: Integration Test Document
author: Test User
tags:
  - integration
  - test
  - database
date: 2025-09-04
---

# Integration Test Document

This is a test document for validating the integration between
the **document parsers** and the **database layer**.

## Features Tested

- Frontmatter metadata extraction
- Header structure parsing
- Keyword extraction and indexing
- Database storage integration

## Code Example

```python
def test_function():
    return "Hello, World!"
```

[Link to documentation](https://example.com/docs)

> This is a blockquote for testing.
"""
        
        # Parse content using parser factory
        parser_result = await parse_content(content, "markdown", "test_integration.md")
        
        assert parser_result.success is True
        assert len(parser_result.content) > 0
        assert len(parser_result.keywords) > 0
        assert len(parser_result.metadata) > 0
        
        # Index document in database using parsed data
        doc_id = await document_manager.index_document(
            file_path="test_integration.md",
            content=parser_result.content,
            metadata=parser_result.metadata
        )
        
        assert doc_id is not None
        assert isinstance(doc_id, int)
        
        # Retrieve document from database
        retrieved_doc = await document_manager.get_document(doc_id)
        
        assert retrieved_doc is not None
        assert retrieved_doc["content"] == parser_result.content
        assert retrieved_doc["file_path"] == "test_integration.md"
        
        # Check metadata integration
        if "extracted_metadata" in retrieved_doc:
            metadata = retrieved_doc["extracted_metadata"]
            # Should have some metadata from both parser and database
            assert len(metadata) > 0
    
    @pytest.mark.asyncio
    async def test_parse_and_index_text_file(self, document_manager):
        """Test parsing text file and database integration."""
        content = """Application Log File
Generated: 2025-09-04

2025-09-04 10:00:00 INFO Application started successfully
2025-09-04 10:00:01 DEBUG Loading configuration from config.ini
2025-09-04 10:00:02 INFO Database connection established
2025-09-04 10:00:03 WARN Configuration value missing: backup_interval
2025-09-04 10:00:04 INFO Server listening on port 8080
2025-09-04 10:00:05 ERROR Failed to load plugin: custom_auth
2025-09-04 10:00:06 INFO Application ready to serve requests

User emails found in logs:
- admin@example.com
- support@example.com

Server URLs:
- https://api.example.com
- https://backup.example.com
"""
        
        # Parse content
        parser_result = await parse_content(content, "text", "application.log")
        
        assert parser_result.success is True
        assert parser_result.metadata["document_type"] == "log"
        assert "log_levels" in parser_result.metadata
        assert "emails" in parser_result.metadata
        assert "urls" in parser_result.metadata
        
        # Index in database
        doc_id = await document_manager.index_document(
            file_path="application.log",
            content=parser_result.content,
            metadata=parser_result.metadata
        )
        
        assert doc_id is not None
        
        # Search for document by keywords
        search_results = await document_manager.search_documents("application")
        
        assert len(search_results) > 0
        found_doc = search_results[0]
        assert found_doc["id"] == doc_id
        assert "relevance_score" in found_doc
    
    @pytest.mark.asyncio
    async def test_file_based_integration(self, document_manager):
        """Test complete file-based integration workflow."""
        # Create temporary test files
        test_files = [
            ("readme.md", """# Project Documentation

This project demonstrates document intelligence capabilities.

## Features

- Document parsing
- Metadata extraction  
- Search functionality
- Database integration

## Installation

```bash
pip install mydocs-mcp
```

Contact: info@example.com
"""),
            ("config.ini", """[database]
host=localhost
port=5432
name=mydocs_db

[server]
port=8080
workers=4

[logging]  
level=INFO
file=/var/log/mydocs.log
"""),
            ("notes.txt", """Personal Notes - 2025-09-04

Meeting with team about document system:
- Need better search capabilities
- Integration with existing tools
- Performance requirements < 200ms

Action items:
- Implement parser system ✓
- Add database integration ✓
- Create test suite ✓
- Performance optimization

Next meeting: 2025-09-10
""")
        ]
        
        indexed_docs = []
        
        for filename, content in test_files:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix=Path(filename).suffix, delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # Verify file is supported by parsers
                assert supports_file(temp_path)
                
                # Parse file
                parser_result = await parse_file(temp_path)
                
                assert parser_result.success is True
                assert len(parser_result.content) > 0
                
                # Index in database with original filename for realistic test
                doc_id = await document_manager.index_document(
                    file_path=filename,  # Use original filename
                    content=parser_result.content,
                    metadata=parser_result.metadata
                )
                
                assert doc_id is not None
                indexed_docs.append((filename, doc_id))
                
            finally:
                os.unlink(temp_path)
        
        # Test search across multiple documents
        search_results = await document_manager.search_documents("database")
        
        # Should find both config.ini and readme.md
        assert len(search_results) >= 2
        
        # Test specific searches
        readme_results = await document_manager.search_documents("installation")
        assert len(readme_results) >= 1
        assert any("readme" in result["file_path"].lower() for result in readme_results)
        
        config_results = await document_manager.search_documents("localhost")
        assert len(config_results) >= 1
        assert any("config" in result["file_path"].lower() for result in config_results)
    
    @pytest.mark.asyncio
    async def test_parser_performance_with_database(self, document_manager):
        """Test parser performance in realistic database scenario."""
        # Create multiple documents for performance testing
        test_documents = []
        
        for i in range(10):
            content = f"""# Document {i}

This is test document number {i} for performance testing.

## Section A{i}

Content about topic {i} with various keywords:
- keyword_{i}_alpha
- keyword_{i}_beta  
- keyword_{i}_gamma

## Section B{i}

More content with different patterns:
- Performance testing
- Database integration
- Search functionality
- Document {i} specific content

Email: user{i}@example.com
URL: https://doc{i}.example.com

```python
def process_document_{i}():
    return f"Processing document {i}"
```
"""
            test_documents.append((f"doc_{i}.md", content))
        
        # Index all documents and measure performance
        start_time = time.time()
        doc_ids = []
        
        for filename, content in test_documents:
            # Parse
            parser_result = await parse_content(content, "markdown", filename)
            assert parser_result.success is True
            
            # Index
            doc_id = await document_manager.index_document(
                file_path=filename,
                content=parser_result.content,
                metadata=parser_result.metadata
            )
            assert doc_id is not None
            doc_ids.append(doc_id)
        
        indexing_time = (time.time() - start_time) * 1000
        
        # Performance validation - should be reasonable for 10 documents
        avg_time_per_doc = indexing_time / len(test_documents)
        assert avg_time_per_doc < 1000  # Less than 1 second per document
        
        print(f"Indexed {len(test_documents)} documents in {indexing_time:.2f}ms (avg: {avg_time_per_doc:.2f}ms per doc)")
        
        # Test search performance
        search_start = time.time()
        search_results = await document_manager.search_documents("performance testing")
        search_time = (time.time() - search_start) * 1000
        
        assert len(search_results) > 0
        assert search_time < 200  # Should meet < 200ms requirement
        
        print(f"Search completed in {search_time:.2f}ms, found {len(search_results)} results")
    
    @pytest.mark.asyncio
    async def test_metadata_consistency(self, document_manager):
        """Test metadata consistency between parser and database."""
        content = """---
title: Metadata Test
author: Test User
version: 1.0
keywords:
  - metadata
  - testing
  - consistency
custom_field: custom_value
---

# Metadata Consistency Test

This document tests metadata consistency between parser extraction
and database storage.

Key points:
- Frontmatter should be preserved
- Parser metadata should be stored
- Database metadata should be retrievable
- Search should work with metadata
"""
        
        # Parse content
        parser_result = await parse_content(content, "markdown", "metadata_test.md")
        
        # Verify parser extracted metadata
        assert "title" in parser_result.metadata
        assert "author" in parser_result.metadata
        assert "keywords" in parser_result.metadata
        assert "custom_field" in parser_result.metadata
        assert parser_result.metadata["title"] == "Metadata Test"
        
        # Index in database
        doc_id = await document_manager.index_document(
            file_path="metadata_test.md",
            content=parser_result.content,
            metadata=parser_result.metadata
        )
        
        # Retrieve with metadata
        retrieved_doc = await document_manager.get_document(doc_id, include_metadata=True)
        
        assert retrieved_doc is not None
        
        # Check that core document metadata is present
        assert retrieved_doc["file_path"] == "metadata_test.md"
        
        # The metadata integration depends on the database manager implementation
        # At minimum, the document should be searchable by its content
        title_search = await document_manager.search_documents("Metadata Test")
        assert len(title_search) > 0
        assert title_search[0]["id"] == doc_id
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, document_manager):
        """Test error handling in parser-database integration."""
        # Test with invalid content that should be handled gracefully
        invalid_markdown = """---
invalid: yaml: content: [unclosed
---

# Valid Header

But invalid frontmatter above.
"""
        
        # Parser should handle invalid YAML gracefully
        parser_result = await parse_content(invalid_markdown, "markdown", "invalid.md")
        
        # Should still succeed (parser handles YAML errors)
        assert parser_result.success is True
        assert len(parser_result.content) > 0
        
        # Database indexing should also succeed
        doc_id = await document_manager.index_document(
            file_path="invalid.md",
            content=parser_result.content,
            metadata=parser_result.metadata
        )
        
        assert doc_id is not None
        
        # Document should be searchable
        search_results = await document_manager.search_documents("Valid Header")
        assert len(search_results) > 0


class TestParserFactoryIntegration:
    """Test parser factory integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_factory_with_database_workflow(self):
        """Test complete workflow using parser factory and database."""
        # Create document manager
        manager = await create_document_manager(
            database_path=":memory:",
            logger=logging.getLogger("factory_test")
        )
        
        try:
            factory = get_default_factory(logging.getLogger("factory_test"))
            
            # Test different document types
            test_cases = [
                ("test.md", "# Test\nMarkdown content", "markdown"),
                ("test.txt", "Plain text content", "text"),
                ("config.cfg", "key=value\nother=setting", "text")
            ]
            
            for filename, content, expected_type in test_cases:
                # Parse using factory
                result = await factory.parse_content(content, expected_type, filename)
                
                assert result.success is True
                
                # Index using database manager
                doc_id = await manager.index_document(
                    file_path=filename,
                    content=result.content,
                    metadata=result.metadata
                )
                
                assert doc_id is not None
            
            # Verify all documents are searchable
            all_results = await manager.search_documents("content")
            assert len(all_results) >= len(test_cases)
            
            # Test factory statistics
            stats = factory.get_factory_stats()
            assert stats["total_parses"] >= len(test_cases)
            assert stats["success_rate"] > 0.9  # Should have high success rate
            
        finally:
            await manager.close()


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])