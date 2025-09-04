"""
mydocs-mcp Database Query Functions

This module provides comprehensive query functions for all database operations
including document storage, search indexing, metadata management, and caching.
Optimized for sub-200ms response times.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

from .models import Document, DocumentMetadata, SearchIndex, SearchCache
from .connection import DatabaseConnection, monitor_query_performance


class DocumentQueries:
    """
    Document-related database operations.
    
    Handles all CRUD operations for documents with performance optimization
    and proper error handling.
    """
    
    def __init__(self, connection: DatabaseConnection, logger: Optional[logging.Logger] = None):
        """
        Initialize document queries.
        
        Args:
            connection: Database connection instance
            logger: Optional logger instance
        """
        self.db = connection
        self.logger = logger or logging.getLogger(__name__)
    
    @monitor_query_performance
    async def create_document(self, document: Document) -> int:
        """
        Create new document in database.
        
        Args:
            document: Document instance to create
            
        Returns:
            ID of created document
            
        Raises:
            QueryError: If document creation fails
        """
        sql = """
        INSERT INTO documents (
            file_path, file_name, content, file_type, file_size, file_hash,
            created_at, modified_at, indexed_at, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            async with self.db.transaction() as conn:
                cursor = await conn.execute(sql, (
                    document.file_path,
                    document.file_name,
                    document.content,
                    document.file_type,
                    document.file_size,
                    document.file_hash,
                    document.created_at,
                    document.modified_at,
                    document.indexed_at or datetime.now(),
                    document.metadata_json
                ))
                
                document_id = cursor.lastrowid
                self.logger.debug(f"Created document with ID: {document_id}")
                return document_id
                
        except Exception as e:
            self.logger.error(f"Failed to create document: {e}")
            raise
    
    @monitor_query_performance
    async def get_document(self, document_id: int) -> Optional[Document]:
        """
        Retrieve document by ID.
        
        Args:
            document_id: Document ID to retrieve
            
        Returns:
            Document instance or None if not found
        """
        sql = """
        SELECT id, file_path, file_name, content, file_type, file_size, file_hash,
               created_at, modified_at, indexed_at, metadata_json
        FROM documents
        WHERE id = ?
        """
        
        try:
            row = await self.db.fetch_one(sql, (document_id,))
            
            if row:
                return Document(
                    id=row[0],
                    file_path=row[1],
                    file_name=row[2],
                    content=row[3],
                    file_type=row[4],
                    file_size=row[5],
                    file_hash=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    modified_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    indexed_at=datetime.fromisoformat(row[9]) if row[9] else None,
                    metadata_json=row[10]
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get document {document_id}: {e}")
            raise
    
    @monitor_query_performance
    async def get_document_by_path(self, file_path: str) -> Optional[Document]:
        """
        Retrieve document by file path.
        
        Args:
            file_path: File path to search for
            
        Returns:
            Document instance or None if not found
        """
        sql = """
        SELECT id, file_path, file_name, content, file_type, file_size, file_hash,
               created_at, modified_at, indexed_at, metadata_json
        FROM documents
        WHERE file_path = ?
        """
        
        try:
            row = await self.db.fetch_one(sql, (file_path,))
            
            if row:
                return Document(
                    id=row[0],
                    file_path=row[1],
                    file_name=row[2],
                    content=row[3],
                    file_type=row[4],
                    file_size=row[5],
                    file_hash=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    modified_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    indexed_at=datetime.fromisoformat(row[9]) if row[9] else None,
                    metadata_json=row[10]
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get document by path {file_path}: {e}")
            raise
    
    @monitor_query_performance
    async def update_document(self, document: Document) -> bool:
        """
        Update existing document.
        
        Args:
            document: Document instance with updated data
            
        Returns:
            True if update successful, False otherwise
        """
        sql = """
        UPDATE documents 
        SET file_path = ?, file_name = ?, content = ?, file_type = ?, 
            file_size = ?, file_hash = ?, created_at = ?, modified_at = ?, 
            indexed_at = ?, metadata_json = ?
        WHERE id = ?
        """
        
        try:
            async with self.db.transaction() as conn:
                cursor = await conn.execute(sql, (
                    document.file_path,
                    document.file_name,
                    document.content,
                    document.file_type,
                    document.file_size,
                    document.file_hash,
                    document.created_at,
                    document.modified_at,
                    document.indexed_at,
                    document.metadata_json,
                    document.id
                ))
                
                success = cursor.rowcount > 0
                if success:
                    self.logger.debug(f"Updated document ID: {document.id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to update document {document.id}: {e}")
            raise
    
    @monitor_query_performance
    async def delete_document(self, document_id: int) -> bool:
        """
        Delete document by ID.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        sql = "DELETE FROM documents WHERE id = ?"
        
        try:
            async with self.db.transaction() as conn:
                cursor = await conn.execute(sql, (document_id,))
                
                success = cursor.rowcount > 0
                if success:
                    self.logger.debug(f"Deleted document ID: {document_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete document {document_id}: {e}")
            raise
    
    @monitor_query_performance
    async def list_documents(
        self,
        file_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "indexed_at DESC"
    ) -> List[Document]:
        """
        List documents with filtering and pagination.
        
        Args:
            file_type: Optional file type filter
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            order_by: ORDER BY clause
            
        Returns:
            List of Document instances
        """
        # Build query with optional filtering
        base_sql = """
        SELECT id, file_path, file_name, content, file_type, file_size, file_hash,
               created_at, modified_at, indexed_at, metadata_json
        FROM documents
        """
        
        where_clause = ""
        params = []
        
        if file_type:
            where_clause = "WHERE file_type = ?"
            params.append(file_type)
        
        sql = f"{base_sql} {where_clause} ORDER BY {order_by} LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        try:
            rows = await self.db.fetch_all(sql, tuple(params))
            
            documents = []
            for row in rows:
                documents.append(Document(
                    id=row[0],
                    file_path=row[1],
                    file_name=row[2],
                    content=row[3],
                    file_type=row[4],
                    file_size=row[5],
                    file_hash=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    modified_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    indexed_at=datetime.fromisoformat(row[9]) if row[9] else None,
                    metadata_json=row[10]
                ))
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Failed to list documents: {e}")
            raise
    
    @monitor_query_performance
    async def count_documents(self, file_type: Optional[str] = None) -> int:
        """
        Count total number of documents.
        
        Args:
            file_type: Optional file type filter
            
        Returns:
            Total document count
        """
        if file_type:
            sql = "SELECT COUNT(*) FROM documents WHERE file_type = ?"
            params = (file_type,)
        else:
            sql = "SELECT COUNT(*) FROM documents"
            params = ()
        
        try:
            row = await self.db.fetch_one(sql, params)
            return row[0] if row else 0
            
        except Exception as e:
            self.logger.error(f"Failed to count documents: {e}")
            raise


class SearchQueries:
    """
    Search-related database operations.
    
    Handles search index management, keyword search, and search result caching
    for optimal search performance.
    """
    
    def __init__(self, connection: DatabaseConnection, logger: Optional[logging.Logger] = None):
        """
        Initialize search queries.
        
        Args:
            connection: Database connection instance
            logger: Optional logger instance
        """
        self.db = connection
        self.logger = logger or logging.getLogger(__name__)
    
    @monitor_query_performance
    async def create_search_index_entry(self, search_index: SearchIndex) -> int:
        """
        Create search index entry.
        
        Args:
            search_index: SearchIndex instance to create
            
        Returns:
            ID of created search index entry
        """
        sql = """
        INSERT OR REPLACE INTO search_index (
            document_id, keyword, frequency, position_data, relevance_score
        ) VALUES (?, ?, ?, ?, ?)
        """
        
        try:
            async with self.db.transaction() as conn:
                cursor = await conn.execute(sql, (
                    search_index.document_id,
                    search_index.keyword,
                    search_index.frequency,
                    search_index.position_data,
                    search_index.relevance_score
                ))
                
                index_id = cursor.lastrowid
                self.logger.debug(f"Created search index entry with ID: {index_id}")
                return index_id
                
        except Exception as e:
            self.logger.error(f"Failed to create search index entry: {e}")
            raise
    
    @monitor_query_performance
    async def bulk_create_search_index(self, search_entries: List[SearchIndex]) -> int:
        """
        Bulk create search index entries for performance.
        
        Args:
            search_entries: List of SearchIndex instances
            
        Returns:
            Number of entries created
        """
        sql = """
        INSERT OR REPLACE INTO search_index (
            document_id, keyword, frequency, position_data, relevance_score
        ) VALUES (?, ?, ?, ?, ?)
        """
        
        try:
            params_list = [
                (
                    entry.document_id,
                    entry.keyword,
                    entry.frequency,
                    entry.position_data,
                    entry.relevance_score
                )
                for entry in search_entries
            ]
            
            async with self.db.transaction() as conn:
                cursor = await conn.executemany(sql, params_list)
                
                count = len(search_entries)
                self.logger.debug(f"Bulk created {count} search index entries")
                return count
                
        except Exception as e:
            self.logger.error(f"Failed to bulk create search index entries: {e}")
            raise
    
    @monitor_query_performance
    async def search_documents(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0,
        file_type_filter: Optional[str] = None
    ) -> List[Tuple[Document, float]]:
        """
        Search documents using keyword matching.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of results to skip
            file_type_filter: Optional file type filter
            
        Returns:
            List of (Document, relevance_score) tuples
        """
        # Split query into keywords and normalize
        keywords = [kw.lower().strip() for kw in query.split() if kw.strip()]
        
        if not keywords:
            return []
        
        # Build search query with keyword matching
        keyword_placeholders = ",".join("?" for _ in keywords)
        
        base_sql = """
        SELECT DISTINCT d.id, d.file_path, d.file_name, d.content, d.file_type, 
               d.file_size, d.file_hash, d.created_at, d.modified_at, 
               d.indexed_at, d.metadata_json,
               SUM(si.relevance_score * si.frequency) as total_score
        FROM documents d
        JOIN search_index si ON d.id = si.document_id
        WHERE si.keyword IN ({})
        """.format(keyword_placeholders)
        
        params = list(keywords)
        
        # Add file type filter if specified
        if file_type_filter:
            base_sql += " AND d.file_type = ?"
            params.append(file_type_filter)
        
        # Group by document and order by relevance
        sql = f"""
        {base_sql}
        GROUP BY d.id
        ORDER BY total_score DESC, d.indexed_at DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        
        try:
            rows = await self.db.fetch_all(sql, tuple(params))
            
            results = []
            for row in rows:
                document = Document(
                    id=row[0],
                    file_path=row[1],
                    file_name=row[2],
                    content=row[3],
                    file_type=row[4],
                    file_size=row[5],
                    file_hash=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    modified_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    indexed_at=datetime.fromisoformat(row[9]) if row[9] else None,
                    metadata_json=row[10]
                )
                
                relevance_score = float(row[11]) if row[11] else 0.0
                results.append((document, relevance_score))
            
            self.logger.debug(f"Found {len(results)} search results for query: {query}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search documents: {e}")
            raise
    
    @monitor_query_performance
    async def full_text_search(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Tuple[Document, float]]:
        """
        Full-text search using SQLite FTS5.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of (Document, relevance_score) tuples
        """
        sql = """
        SELECT d.id, d.file_path, d.file_name, d.content, d.file_type,
               d.file_size, d.file_hash, d.created_at, d.modified_at,
               d.indexed_at, d.metadata_json, fts.rank
        FROM documents_fts fts
        JOIN documents d ON fts.rowid = d.id
        WHERE documents_fts MATCH ?
        ORDER BY fts.rank
        LIMIT ? OFFSET ?
        """
        
        try:
            rows = await self.db.fetch_all(sql, (query, limit, offset))
            
            results = []
            for row in rows:
                document = Document(
                    id=row[0],
                    file_path=row[1],
                    file_name=row[2],
                    content=row[3],
                    file_type=row[4],
                    file_size=row[5],
                    file_hash=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    modified_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    indexed_at=datetime.fromisoformat(row[9]) if row[9] else None,
                    metadata_json=row[10]
                )
                
                # FTS5 rank is negative, convert to positive relevance score
                relevance_score = abs(float(row[11])) if row[11] else 0.0
                results.append((document, relevance_score))
            
            self.logger.debug(f"Found {len(results)} FTS results for query: {query}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to perform full-text search: {e}")
            raise
    
    @monitor_query_performance
    async def delete_search_index_for_document(self, document_id: int) -> int:
        """
        Delete all search index entries for a document.
        
        Args:
            document_id: Document ID to clean up
            
        Returns:
            Number of entries deleted
        """
        sql = "DELETE FROM search_index WHERE document_id = ?"
        
        try:
            async with self.db.transaction() as conn:
                cursor = await conn.execute(sql, (document_id,))
                
                count = cursor.rowcount
                self.logger.debug(f"Deleted {count} search index entries for document {document_id}")
                return count
                
        except Exception as e:
            self.logger.error(f"Failed to delete search index for document {document_id}: {e}")
            raise
    
    @monitor_query_performance
    async def get_search_cache(self, query_hash: str) -> Optional[SearchCache]:
        """
        Get cached search results.
        
        Args:
            query_hash: Hash of search query
            
        Returns:
            SearchCache instance or None if not found/expired
        """
        sql = """
        SELECT id, query_hash, query_text, results, created_at, expires_at, hit_count
        FROM search_cache
        WHERE query_hash = ? AND expires_at > datetime('now')
        """
        
        try:
            row = await self.db.fetch_one(sql, (query_hash,))
            
            if row:
                cache_entry = SearchCache(
                    id=row[0],
                    query_hash=row[1],
                    query_text=row[2],
                    results=row[3],
                    created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    expires_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    hit_count=row[6]
                )
                
                # Update hit count
                await self._update_cache_hit_count(cache_entry.id)
                
                return cache_entry
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get search cache: {e}")
            raise
    
    @monitor_query_performance
    async def create_search_cache(self, cache_entry: SearchCache) -> int:
        """
        Create search cache entry.
        
        Args:
            cache_entry: SearchCache instance to create
            
        Returns:
            ID of created cache entry
        """
        sql = """
        INSERT OR REPLACE INTO search_cache (
            query_hash, query_text, results, created_at, expires_at, hit_count
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        
        try:
            async with self.db.transaction() as conn:
                cursor = await conn.execute(sql, (
                    cache_entry.query_hash,
                    cache_entry.query_text,
                    cache_entry.results,
                    cache_entry.created_at or datetime.now(),
                    cache_entry.expires_at,
                    cache_entry.hit_count
                ))
                
                cache_id = cursor.lastrowid
                self.logger.debug(f"Created search cache entry with ID: {cache_id}")
                return cache_id
                
        except Exception as e:
            self.logger.error(f"Failed to create search cache entry: {e}")
            raise
    
    async def _update_cache_hit_count(self, cache_id: int) -> None:
        """Update cache hit count."""
        sql = "UPDATE search_cache SET hit_count = hit_count + 1 WHERE id = ?"
        
        try:
            await self.db.execute(sql, (cache_id,))
            await self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to update cache hit count: {e}")
    
    @monitor_query_performance
    async def cleanup_expired_cache(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of entries deleted
        """
        sql = "DELETE FROM search_cache WHERE expires_at <= datetime('now')"
        
        try:
            async with self.db.transaction() as conn:
                cursor = await conn.execute(sql)
                
                count = cursor.rowcount
                self.logger.debug(f"Cleaned up {count} expired cache entries")
                return count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired cache: {e}")
            raise


class MetadataQueries:
    """
    Document metadata-related database operations.
    
    Handles metadata extraction, storage, and retrieval operations
    for enhanced document search and filtering.
    """
    
    def __init__(self, connection: DatabaseConnection, logger: Optional[logging.Logger] = None):
        """
        Initialize metadata queries.
        
        Args:
            connection: Database connection instance
            logger: Optional logger instance
        """
        self.db = connection
        self.logger = logger or logging.getLogger(__name__)
    
    @monitor_query_performance
    async def create_metadata(self, metadata: DocumentMetadata) -> int:
        """
        Create document metadata entry.
        
        Args:
            metadata: DocumentMetadata instance to create
            
        Returns:
            ID of created metadata entry
        """
        sql = """
        INSERT OR REPLACE INTO document_metadata (
            document_id, key, value, extracted_at
        ) VALUES (?, ?, ?, ?)
        """
        
        try:
            async with self.db.transaction() as conn:
                cursor = await conn.execute(sql, (
                    metadata.document_id,
                    metadata.key,
                    metadata.value,
                    metadata.extracted_at or datetime.now()
                ))
                
                metadata_id = cursor.lastrowid
                self.logger.debug(f"Created metadata entry with ID: {metadata_id}")
                return metadata_id
                
        except Exception as e:
            self.logger.error(f"Failed to create metadata entry: {e}")
            raise
    
    @monitor_query_performance
    async def bulk_create_metadata(
        self,
        document_id: int,
        metadata_dict: Dict[str, str]
    ) -> int:
        """
        Bulk create metadata entries for a document.
        
        Args:
            document_id: Document ID
            metadata_dict: Dictionary of key-value metadata pairs
            
        Returns:
            Number of metadata entries created
        """
        sql = """
        INSERT OR REPLACE INTO document_metadata (
            document_id, key, value, extracted_at
        ) VALUES (?, ?, ?, ?)
        """
        
        try:
            current_time = datetime.now()
            params_list = [
                (document_id, key, value, current_time)
                for key, value in metadata_dict.items()
            ]
            
            async with self.db.transaction() as conn:
                await conn.executemany(sql, params_list)
                
                count = len(params_list)
                self.logger.debug(f"Bulk created {count} metadata entries for document {document_id}")
                return count
                
        except Exception as e:
            self.logger.error(f"Failed to bulk create metadata: {e}")
            raise
    
    @monitor_query_performance
    async def get_document_metadata(self, document_id: int) -> Dict[str, str]:
        """
        Get all metadata for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary of metadata key-value pairs
        """
        sql = """
        SELECT key, value
        FROM document_metadata
        WHERE document_id = ?
        ORDER BY key
        """
        
        try:
            rows = await self.db.fetch_all(sql, (document_id,))
            
            metadata = {}
            for row in rows:
                metadata[row[0]] = row[1]
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to get document metadata: {e}")
            raise
    
    @monitor_query_performance
    async def search_by_metadata(
        self,
        metadata_filters: Dict[str, str],
        limit: int = 50,
        offset: int = 0
    ) -> List[Document]:
        """
        Search documents by metadata criteria.
        
        Args:
            metadata_filters: Dictionary of metadata filters
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of Document instances
        """
        if not metadata_filters:
            return []
        
        # Build dynamic query based on metadata filters
        filter_conditions = []
        params = []
        
        for key, value in metadata_filters.items():
            filter_conditions.append("(dm.key = ? AND dm.value = ?)")
            params.extend([key, value])
        
        where_clause = " OR ".join(filter_conditions)
        
        sql = f"""
        SELECT DISTINCT d.id, d.file_path, d.file_name, d.content, d.file_type,
               d.file_size, d.file_hash, d.created_at, d.modified_at,
               d.indexed_at, d.metadata_json
        FROM documents d
        JOIN document_metadata dm ON d.id = dm.document_id
        WHERE {where_clause}
        ORDER BY d.indexed_at DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        
        try:
            rows = await self.db.fetch_all(sql, tuple(params))
            
            documents = []
            for row in rows:
                documents.append(Document(
                    id=row[0],
                    file_path=row[1],
                    file_name=row[2],
                    content=row[3],
                    file_type=row[4],
                    file_size=row[5],
                    file_hash=row[6],
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    modified_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    indexed_at=datetime.fromisoformat(row[9]) if row[9] else None,
                    metadata_json=row[10]
                ))
            
            self.logger.debug(f"Found {len(documents)} documents matching metadata filters")
            return documents
            
        except Exception as e:
            self.logger.error(f"Failed to search by metadata: {e}")
            raise
    
    @monitor_query_performance
    async def delete_document_metadata(self, document_id: int) -> int:
        """
        Delete all metadata for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Number of metadata entries deleted
        """
        sql = "DELETE FROM document_metadata WHERE document_id = ?"
        
        try:
            async with self.db.transaction() as conn:
                cursor = await conn.execute(sql, (document_id,))
                
                count = cursor.rowcount
                self.logger.debug(f"Deleted {count} metadata entries for document {document_id}")
                return count
                
        except Exception as e:
            self.logger.error(f"Failed to delete document metadata: {e}")
            raise