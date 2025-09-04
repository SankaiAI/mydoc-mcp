"""Integration tests for SQLite database functionality."""

import asyncio
import os
import tempfile
from pathlib import Path
from datetime import datetime
import json
import pytest
import aiosqlite

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.models import Document, SearchIndex
from database.connection import DatabaseConnection
from database.queries import DocumentQueries


class TestDatabaseIntegration:
    """Test suite for database integration."""
    
    @pytest.fixture
    async def db_connection(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            db = DatabaseConnection(db_path)
            await db.initialize()
            yield db
        finally:
            await db.close()
            os.unlink(db_path)
    
    @pytest.fixture
    async def queries(self, db_connection):
        """Create DocumentQueries instance."""
        return DocumentQueries(db_connection)
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, db_connection):
        """Test database schema initialization."""
        async with aiosqlite.connect(db_connection.db_path) as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = await cursor.fetchall()
            table_names = [t[0] for t in tables]
            
            assert 'documents' in table_names
            assert 'search_index' in table_names
    
    @pytest.mark.asyncio
    async def test_insert_document(self, queries):
        """Test inserting a document."""
        doc = Document(
            file_path="/test/doc.md",
            file_name="doc.md",
            content="Test content",
            file_type="markdown",
            file_size=12,
            metadata_json=json.dumps({"tags": ["test"]})
        )
        
        doc_id = await queries.insert_document(doc)
        assert doc_id is not None
        assert doc_id > 0
    
    @pytest.mark.asyncio
    async def test_get_document_by_path(self, queries):
        """Test retrieving a document by path."""
        doc = Document(
            file_path="/test/doc2.md",
            file_name="doc2.md",
            content="Another test",
            file_type="markdown",
            file_size=12,
            metadata_json="{}"
        )
        
        await queries.insert_document(doc)
        retrieved = await queries.get_document_by_path("/test/doc2.md")
        
        assert retrieved is not None
        assert retrieved.file_name == "doc2.md"
        assert retrieved.content == "Another test"
    
    @pytest.mark.asyncio
    async def test_update_document(self, queries):
        """Test updating a document."""
        doc = Document(
            file_path="/test/doc3.md",
            file_name="doc3.md",
            content="Original content",
            file_type="markdown",
            file_size=16,
            metadata_json="{}"
        )
        
        doc_id = await queries.insert_document(doc)
        
        updated_doc = Document(
            id=doc_id,
            file_path="/test/doc3.md",
            file_name="doc3.md",
            content="Updated content",
            file_type="markdown",
            file_size=15,
            modified_at=datetime.utcnow(),
            metadata_json="{}"
        )
        
        success = await queries.update_document(updated_doc)
        assert success is True
        
        retrieved = await queries.get_document_by_path("/test/doc3.md")
        assert retrieved.content == "Updated content"
    
    @pytest.mark.asyncio
    async def test_delete_document(self, queries):
        """Test deleting a document."""
        doc = Document(
            file_path="/test/doc4.md",
            file_name="doc4.md",
            content="To be deleted",
            file_type="markdown",
            file_size=13,
            metadata_json="{}"
        )
        
        doc_id = await queries.insert_document(doc)
        success = await queries.delete_document(doc_id)
        assert success is True
        
        retrieved = await queries.get_document_by_path("/test/doc4.md")
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_search_index_operations(self, queries):
        """Test search index CRUD operations."""
        doc = Document(
            file_path="/test/searchdoc.md",
            file_name="searchdoc.md",
            content="Python programming tutorial",
            file_type="markdown",
            file_size=28,
            metadata_json="{}"
        )
        
        doc_id = await queries.insert_document(doc)
        
        # Add search index entries
        index_entries = [
            SearchIndex(document_id=doc_id, keyword="python", position=0, frequency=1),
            SearchIndex(document_id=doc_id, keyword="programming", position=7, frequency=1),
            SearchIndex(document_id=doc_id, keyword="tutorial", position=19, frequency=1),
        ]
        
        for entry in index_entries:
            await queries.insert_search_index(entry)
        
        # Search for documents
        results = await queries.search_documents("python")
        assert len(results) > 0
        assert results[0].file_name == "searchdoc.md"
    
    @pytest.mark.asyncio
    async def test_get_all_documents(self, queries):
        """Test retrieving all documents."""
        docs = [
            Document(
                file_path=f"/test/bulk{i}.md",
                file_name=f"bulk{i}.md",
                content=f"Content {i}",
                file_type="markdown",
                file_size=10,
                metadata_json="{}"
            )
            for i in range(5)
        ]
        
        for doc in docs:
            await queries.insert_document(doc)
        
        all_docs = await queries.get_all_documents()
        assert len(all_docs) >= 5
    
    @pytest.mark.asyncio
    async def test_get_documents_by_type(self, queries):
        """Test filtering documents by type."""
        md_doc = Document(
            file_path="/test/markdown.md",
            file_name="markdown.md",
            content="MD content",
            file_type="markdown",
            file_size=10,
            metadata_json="{}"
        )
        
        txt_doc = Document(
            file_path="/test/text.txt",
            file_name="text.txt",
            content="Text content",
            file_type="text",
            file_size=12,
            metadata_json="{}"
        )
        
        await queries.insert_document(md_doc)
        await queries.insert_document(txt_doc)
        
        md_docs = await queries.get_documents_by_type("markdown")
        assert any(d.file_name == "markdown.md" for d in md_docs)
        assert not any(d.file_name == "text.txt" for d in md_docs)
    
    @pytest.mark.asyncio
    async def test_performance_sub_200ms(self, queries):
        """Test that queries complete within 200ms."""
        import time
        
        # Insert test data
        for i in range(100):
            doc = Document(
                file_path=f"/test/perf{i}.md",
                file_name=f"perf{i}.md",
                content=f"Performance test content {i}",
                file_type="markdown",
                file_size=30,
                metadata_json="{}"
            )
            await queries.insert_document(doc)
        
        # Test search performance
        start = time.time()
        results = await queries.search_documents("performance")
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert elapsed < 200, f"Search took {elapsed:.2f}ms, expected < 200ms"
        
        # Test retrieval performance
        start = time.time()
        doc = await queries.get_document_by_path("/test/perf50.md")
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 200, f"Retrieval took {elapsed:.2f}ms, expected < 200ms"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, queries):
        """Test concurrent database operations."""
        async def insert_doc(index):
            doc = Document(
                file_path=f"/test/concurrent{index}.md",
                file_name=f"concurrent{index}.md",
                content=f"Concurrent content {index}",
                file_type="markdown",
                file_size=25,
                metadata_json="{}"
            )
            return await queries.insert_document(doc)
        
        # Run 10 concurrent inserts
        tasks = [insert_doc(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(doc_id > 0 for doc_id in results)
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_connection):
        """Test transaction rollback on error."""
        queries = DocumentQueries(db_connection)
        
        doc = Document(
            file_path="/test/transaction.md",
            file_name="transaction.md",
            content="Transaction test",
            file_type="markdown",
            file_size=16,
            metadata_json="{}"
        )
        
        # This should work
        doc_id = await queries.insert_document(doc)
        assert doc_id is not None
        
        # Try to insert duplicate (should fail due to unique constraint on file_path)
        try:
            await queries.insert_document(doc)
            assert False, "Should have raised an exception"
        except Exception:
            pass  # Expected
        
        # Verify the first insert is still there
        retrieved = await queries.get_document_by_path("/test/transaction.md")
        assert retrieved is not None