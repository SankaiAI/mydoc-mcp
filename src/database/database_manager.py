"""
mydocs-mcp Database Manager

This module provides a high-level database manager that coordinates all
database operations including initialization, document management, and
search functionality with optimized performance.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import hashlib
import re

from .connection import DatabaseConnection, get_database_connection
from .models import Document, DocumentMetadata, SearchIndex, SearchCache
from .queries import DocumentQueries, SearchQueries, MetadataQueries
from .migrations import MigrationManager, initialize_database


class DocumentManager:
    """
    High-level document management interface.
    
    This class provides a comprehensive API for document operations,
    combining storage, indexing, and search functionality with
    performance optimization and error handling.
    """
    
    def __init__(
        self,
        database_path: str,
        cache_ttl: int = 3600,  # 1 hour cache TTL
        max_search_results: int = 50,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize document manager.
        
        Args:
            database_path: Path to SQLite database file
            cache_ttl: Cache time-to-live in seconds
            max_search_results: Maximum search results per query
            logger: Optional logger instance
        """
        self.database_path = database_path
        self.cache_ttl = cache_ttl
        self.max_search_results = max_search_results
        self.logger = logger or logging.getLogger(__name__)
        
        # Database components (initialized in startup)
        self.db_connection: Optional[DatabaseConnection] = None
        self.doc_queries: Optional[DocumentQueries] = None
        self.search_queries: Optional[SearchQueries] = None
        self.metadata_queries: Optional[MetadataQueries] = None
        
        # Performance tracking
        self._query_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    async def initialize(self) -> bool:
        """
        Initialize database manager and ensure schema is up to date.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing document manager with database: {self.database_path}")
            
            # Initialize database with migrations
            success = await initialize_database(self.database_path, self.logger)
            if not success:
                self.logger.error("Database initialization failed")
                return False
            
            # Get database connection
            self.db_connection = await get_database_connection(self.database_path, logger=self.logger)
            
            # Initialize query interfaces
            self.doc_queries = DocumentQueries(self.db_connection, self.logger)
            self.search_queries = SearchQueries(self.db_connection, self.logger)
            self.metadata_queries = MetadataQueries(self.db_connection, self.logger)
            
            # Verify database health
            connection_info = await self.db_connection.get_connection_info()
            if connection_info.get("status") != "connected":
                self.logger.error(f"Database connection failed: {connection_info}")
                return False
            
            # Clean up expired cache entries
            await self._cleanup_expired_cache()
            
            self.logger.info("Document manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Document manager initialization failed: {e}")
            return False
    
    async def index_document(
        self,
        file_path: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        extract_keywords: bool = True
    ) -> Optional[int]:
        """
        Index a document with full-text search and metadata extraction.
        
        Args:
            file_path: Path to the document file
            content: Document content to index
            metadata: Optional metadata dictionary
            extract_keywords: Whether to extract keywords for search
            
        Returns:
            Document ID if successful, None otherwise
        """
        start_time = time.time()
        
        try:
            # Validate input
            if not file_path or not content:
                self.logger.error("File path and content are required")
                return None
            
            # Check if document already exists
            existing_doc = await self.doc_queries.get_document_by_path(file_path)
            
            # Create document model
            document = Document(
                file_path=file_path,
                content=content,
                file_size=len(content.encode('utf-8')),
                created_at=datetime.now(),
                modified_at=datetime.now(),
                indexed_at=datetime.now()
            )
            
            # Add metadata if provided
            if metadata:
                document.metadata = metadata
            
            # Create or update document
            if existing_doc:
                document.id = existing_doc.id
                document.created_at = existing_doc.created_at
                success = await self.doc_queries.update_document(document)
                if not success:
                    self.logger.error(f"Failed to update document: {file_path}")
                    return None
                document_id = document.id
            else:
                document_id = await self.doc_queries.create_document(document)
                if not document_id:
                    self.logger.error(f"Failed to create document: {file_path}")
                    return None
                document.id = document_id
            
            # Store extracted metadata
            if metadata:
                await self.metadata_queries.bulk_create_metadata(document_id, metadata)
            
            # Extract and index keywords for search
            if extract_keywords:
                await self._index_document_keywords(document_id, content)
            
            # Invalidate related search cache
            await self._invalidate_search_cache()
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.info(f"Indexed document {file_path} in {execution_time:.2f}ms")
            
            return document_id
            
        except Exception as e:
            self.logger.error(f"Failed to index document {file_path}: {e}")
            return None
    
    async def search_documents(
        self,
        query: str,
        file_type_filter: Optional[str] = None,
        limit: int = 50,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search documents using keyword search with caching.
        
        Args:
            query: Search query string
            file_type_filter: Optional file type filter
            limit: Maximum number of results
            use_cache: Whether to use search result caching
            
        Returns:
            List of search result dictionaries
        """
        start_time = time.time()
        
        try:
            # Validate query
            if not query or not query.strip():
                return []
            
            query = query.strip()
            limit = min(limit, self.max_search_results)
            
            # Check cache first if enabled
            cache_entry = None
            if use_cache:
                cache_entry = await self._get_search_cache(query, file_type_filter)
                if cache_entry:
                    self._query_stats["cache_hits"] += 1
                    execution_time = (time.time() - start_time) * 1000
                    self.logger.debug(f"Cache hit for query '{query}' in {execution_time:.2f}ms")
                    return cache_entry.search_results
            
            self._query_stats["cache_misses"] += 1
            
            # Perform search
            search_results = await self.search_queries.search_documents(
                query=query,
                limit=limit,
                file_type_filter=file_type_filter
            )
            
            # Format results
            formatted_results = []
            for document, relevance_score in search_results:
                result = {
                    **document.to_dict(),
                    "relevance_score": relevance_score,
                    "content_snippet": self._generate_content_snippet(document.content, query)
                }
                formatted_results.append(result)
            
            # Cache results if caching is enabled
            if use_cache and formatted_results:
                await self._cache_search_results(query, file_type_filter, formatted_results)
            
            # Track performance
            execution_time = (time.time() - start_time) * 1000
            self._query_stats["total_queries"] += 1
            
            if execution_time > 200:
                self._query_stats["slow_queries"] += 1
                self.logger.warning(f"Slow search query: '{query}' took {execution_time:.2f}ms")
            
            self.logger.debug(f"Search completed: '{query}' returned {len(formatted_results)} results in {execution_time:.2f}ms")
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Search failed for query '{query}': {e}")
            return []
    
    async def get_document(
        self,
        document_id: int,
        include_metadata: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get document by ID with optional metadata.
        
        Args:
            document_id: Document ID to retrieve
            include_metadata: Whether to include document metadata
            
        Returns:
            Document dictionary or None if not found
        """
        try:
            # Get document
            document = await self.doc_queries.get_document(document_id)
            if not document:
                return None
            
            # Convert to dictionary
            result = document.to_dict()
            result["content"] = document.content  # Include full content
            
            # Add metadata if requested
            if include_metadata:
                metadata = await self.metadata_queries.get_document_metadata(document_id)
                result["extracted_metadata"] = metadata
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get document {document_id}: {e}")
            return None
    
    async def delete_document(self, document_id: int) -> bool:
        """
        Delete document and all related data.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Delete search index entries
            await self.search_queries.delete_search_index_for_document(document_id)
            
            # Delete metadata entries
            await self.metadata_queries.delete_document_metadata(document_id)
            
            # Delete document (cascading deletes handle related data)
            success = await self.doc_queries.delete_document(document_id)
            
            if success:
                # Invalidate search cache
                await self._invalidate_search_cache()
                self.logger.info(f"Deleted document {document_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            # Document counts by type
            total_docs = await self.doc_queries.count_documents()
            
            # Get file type distribution
            file_types = {}
            documents = await self.doc_queries.list_documents(limit=1000)  # Sample for stats
            for doc in documents:
                file_type = doc.file_type or "unknown"
                file_types[file_type] = file_types.get(file_type, 0) + 1
            
            # Database connection info
            connection_info = await self.db_connection.get_connection_info()
            
            return {
                "documents": {
                    "total_count": total_docs,
                    "file_types": file_types
                },
                "performance": self._query_stats,
                "database": {
                    "path": self.database_path,
                    "size_bytes": connection_info.get("database_size", 0),
                    "status": connection_info.get("status", "unknown")
                },
                "cache": {
                    "ttl_seconds": self.cache_ttl,
                    "max_results": self.max_search_results
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}
    
    async def _index_document_keywords(self, document_id: int, content: str) -> None:
        """Extract and index keywords from document content."""
        try:
            # Clean up existing search index for this document
            await self.search_queries.delete_search_index_for_document(document_id)
            
            # Extract keywords (simple tokenization for MVP)
            keywords = self._extract_keywords(content)
            
            # Create search index entries
            search_entries = []
            document_length = len(content.split())
            
            for keyword, positions in keywords.items():
                search_index = SearchIndex(
                    document_id=document_id,
                    keyword=keyword.lower(),
                    frequency=len(positions)
                )
                search_index.positions = positions
                
                # Calculate relevance score
                search_index.calculate_relevance_score(document_length)
                search_entries.append(search_index)
            
            # Bulk insert for performance
            if search_entries:
                await self.search_queries.bulk_create_search_index(search_entries)
            
        except Exception as e:
            self.logger.error(f"Failed to index keywords for document {document_id}: {e}")
    
    def _extract_keywords(self, content: str) -> Dict[str, List[int]]:
        """
        Extract keywords from content with position tracking.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary mapping keywords to position lists
        """
        # Simple tokenization (can be enhanced with NLP libraries)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'this', 'that', 'these', 'those', 'a', 'an', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'shall'
        }
        
        keywords = {}
        for position, word in enumerate(words):
            if word not in stop_words and len(word) >= 3:
                if word not in keywords:
                    keywords[word] = []
                keywords[word].append(position)
        
        return keywords
    
    def _generate_content_snippet(self, content: str, query: str, snippet_length: int = 200) -> str:
        """
        Generate content snippet highlighting query terms.
        
        Args:
            content: Full document content
            query: Search query
            snippet_length: Maximum snippet length
            
        Returns:
            Content snippet with query highlighting
        """
        try:
            query_words = [word.lower() for word in query.split()]
            content_lower = content.lower()
            
            # Find best position to start snippet
            best_position = 0
            best_score = 0
            
            for word in query_words:
                position = content_lower.find(word)
                if position >= 0:
                    # Score based on how early the word appears
                    score = len(content) - position
                    if score > best_score:
                        best_score = score
                        best_position = max(0, position - snippet_length // 4)
            
            # Extract snippet
            snippet = content[best_position:best_position + snippet_length]
            
            # Add ellipsis if truncated
            if best_position > 0:
                snippet = "..." + snippet
            if best_position + snippet_length < len(content):
                snippet = snippet + "..."
            
            return snippet
            
        except Exception:
            # Fallback to beginning of content
            return content[:snippet_length] + ("..." if len(content) > snippet_length else "")
    
    async def _get_search_cache(self, query: str, file_type_filter: Optional[str] = None) -> Optional[SearchCache]:
        """Get cached search results if available and not expired."""
        try:
            # Calculate query hash
            cache_entry = SearchCache()
            query_hash = cache_entry.calculate_query_hash(query, {"file_type": file_type_filter})
            
            return await self.search_queries.get_search_cache(query_hash)
            
        except Exception as e:
            self.logger.debug(f"Cache lookup failed: {e}")
            return None
    
    async def _cache_search_results(
        self,
        query: str,
        file_type_filter: Optional[str],
        results: List[Dict[str, Any]]
    ) -> None:
        """Cache search results for performance."""
        try:
            # Create cache entry
            cache_entry = SearchCache(
                query_text=query,
                search_results=results,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=self.cache_ttl)
            )
            
            # Calculate query hash
            cache_entry.calculate_query_hash(query, {"file_type": file_type_filter})
            
            # Store in cache
            await self.search_queries.create_search_cache(cache_entry)
            
        except Exception as e:
            self.logger.debug(f"Cache storage failed: {e}")
    
    async def _invalidate_search_cache(self) -> None:
        """Invalidate search cache when documents change."""
        try:
            # For simplicity, clean up expired cache
            # In production, could implement more sophisticated invalidation
            await self.search_queries.cleanup_expired_cache()
            
        except Exception as e:
            self.logger.debug(f"Cache invalidation failed: {e}")
    
    async def _cleanup_expired_cache(self) -> None:
        """Clean up expired cache entries."""
        try:
            count = await self.search_queries.cleanup_expired_cache()
            if count > 0:
                self.logger.debug(f"Cleaned up {count} expired cache entries")
                
        except Exception as e:
            self.logger.debug(f"Cache cleanup failed: {e}")
    
    async def close(self) -> None:
        """Close database manager and cleanup resources."""
        try:
            if self.db_connection:
                await self.db_connection.close()
                self.logger.info("Document manager closed successfully")
                
        except Exception as e:
            self.logger.error(f"Error closing document manager: {e}")


# Convenience function for quick database setup
async def create_document_manager(
    database_path: str,
    cache_ttl: int = 3600,
    max_search_results: int = 50,
    logger: Optional[logging.Logger] = None
) -> Optional[DocumentManager]:
    """
    Create and initialize document manager.
    
    Args:
        database_path: Path to SQLite database file
        cache_ttl: Cache time-to-live in seconds
        max_search_results: Maximum search results per query
        logger: Optional logger instance
        
    Returns:
        Initialized DocumentManager or None if failed
    """
    manager = DocumentManager(database_path, cache_ttl, max_search_results, logger)
    
    success = await manager.initialize()
    if success:
        return manager
    else:
        await manager.close()
        return None