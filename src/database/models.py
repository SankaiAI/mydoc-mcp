"""
mydocs-mcp Database Models and Schema

This module defines the complete database schema for document storage, search indexing,
and metadata management. Optimized for sub-200ms query performance with proper indexing.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import sqlite3
import aiosqlite


@dataclass
class Document:
    """
    Core document model representing a stored document.
    
    This model handles document content, metadata, and indexing information
    with proper validation and type safety.
    """
    id: Optional[int] = None
    file_path: str = ""
    file_name: str = ""
    content: str = ""
    file_type: str = ""
    file_size: int = 0
    file_hash: str = ""
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    metadata_json: str = "{}"
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.file_name and self.file_path:
            self.file_name = Path(self.file_path).name
            
        if not self.file_type and self.file_path:
            self.file_type = Path(self.file_path).suffix.lower().lstrip('.')
            
        if not self.file_hash and self.content:
            self.file_hash = self.calculate_content_hash()
    
    def calculate_content_hash(self) -> str:
        """Calculate SHA-256 hash of document content."""
        return hashlib.sha256(self.content.encode('utf-8')).hexdigest()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Parse and return document metadata."""
        try:
            return json.loads(self.metadata_json)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]):
        """Set document metadata with JSON serialization."""
        self.metadata_json = json.dumps(value, default=str)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for API responses."""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "metadata": self.metadata,
            "content_preview": self.content[:200] + "..." if len(self.content) > 200 else self.content
        }


@dataclass
class DocumentMetadata:
    """
    Document metadata model for extracted document information.
    
    Stores key-value pairs of extracted metadata such as title, author,
    creation date, and other document properties.
    """
    id: Optional[int] = None
    document_id: int = 0
    key: str = ""
    value: str = ""
    extracted_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "key": self.key,
            "value": self.value,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None
        }


@dataclass
class SearchIndex:
    """
    Search index model for keyword-based document search.
    
    Stores keywords extracted from documents with frequency counts,
    position data, and relevance scores for fast search operations.
    """
    id: Optional[int] = None
    document_id: int = 0
    keyword: str = ""
    frequency: int = 1
    position_data: str = "[]"  # JSON array of positions
    relevance_score: float = 0.0
    
    @property
    def positions(self) -> List[int]:
        """Parse and return keyword positions."""
        try:
            return json.loads(self.position_data)
        except (json.JSONDecodeError, TypeError):
            return []
    
    @positions.setter
    def positions(self, value: List[int]):
        """Set keyword positions with JSON serialization."""
        self.position_data = json.dumps(value)
    
    def calculate_relevance_score(self, document_length: int) -> float:
        """
        Calculate TF-IDF style relevance score.
        
        Args:
            document_length: Total number of words in the document
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        if document_length == 0:
            return 0.0
        
        # Simple TF calculation (frequency / document_length)
        tf = self.frequency / document_length
        
        # Boost score for keywords appearing multiple times
        frequency_boost = min(1.0, self.frequency / 5.0)
        
        # Calculate final relevance score
        self.relevance_score = tf * (1.0 + frequency_boost)
        return self.relevance_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert search index to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "keyword": self.keyword,
            "frequency": self.frequency,
            "positions": self.positions,
            "relevance_score": self.relevance_score
        }


@dataclass
class SearchCache:
    """
    Search result cache model for performance optimization.
    
    Caches search query results to improve response times for
    repeated queries.
    """
    id: Optional[int] = None
    query_hash: str = ""
    query_text: str = ""
    results: str = "[]"  # JSON array of results
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    hit_count: int = 0
    
    @property
    def search_results(self) -> List[Dict[str, Any]]:
        """Parse and return cached search results."""
        try:
            return json.loads(self.results)
        except (json.JSONDecodeError, TypeError):
            return []
    
    @search_results.setter
    def search_results(self, value: List[Dict[str, Any]]):
        """Set search results with JSON serialization."""
        self.results = json.dumps(value, default=str)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def calculate_query_hash(self, query: str, filters: Optional[Dict] = None) -> str:
        """Calculate consistent hash for query and filters."""
        query_data = {
            "query": query.lower().strip(),
            "filters": filters or {}
        }
        query_string = json.dumps(query_data, sort_keys=True)
        self.query_hash = hashlib.sha256(query_string.encode('utf-8')).hexdigest()
        return self.query_hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert search cache to dictionary."""
        return {
            "id": self.id,
            "query_hash": self.query_hash,
            "query_text": self.query_text,
            "results_count": len(self.search_results),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "hit_count": self.hit_count,
            "is_expired": self.is_expired()
        }


class DatabaseSchema:
    """
    Database schema definition with DDL statements and migrations.
    
    This class contains all SQL DDL statements for creating tables,
    indexes, and other database objects optimized for performance.
    """
    
    # Schema version for migrations
    SCHEMA_VERSION = 1
    
    # SQLite performance optimization pragmas
    PERFORMANCE_PRAGMAS = {
        'journal_mode': 'WAL',        # Write-ahead logging for better concurrency
        'synchronous': 'NORMAL',      # Balance between safety and performance
        'cache_size': -64000,         # 64MB cache size (negative = KB)
        'temp_store': 'MEMORY',       # Store temporary tables in memory
        'mmap_size': 268435456,       # 256MB memory-mapped I/O size
        'foreign_keys': 'ON',         # Enable foreign key constraints
        'optimize': None,             # Auto-optimize on close
    }
    
    # Core table creation DDL
    CREATE_DOCUMENTS_TABLE = """
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL UNIQUE,
        file_name TEXT NOT NULL,
        content TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER NOT NULL DEFAULT 0,
        file_hash TEXT NOT NULL,
        created_at DATETIME,
        modified_at DATETIME,
        indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        metadata_json TEXT DEFAULT '{}',
        
        -- Constraints
        CHECK (file_size >= 0),
        CHECK (LENGTH(file_hash) = 64)  -- SHA-256 hash length
    );
    """
    
    CREATE_DOCUMENT_METADATA_TABLE = """
    CREATE TABLE IF NOT EXISTS document_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign key constraint
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        
        -- Ensure unique key per document
        UNIQUE (document_id, key)
    );
    """
    
    CREATE_SEARCH_INDEX_TABLE = """
    CREATE TABLE IF NOT EXISTS search_index (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        keyword TEXT NOT NULL,
        frequency INTEGER NOT NULL DEFAULT 1,
        position_data TEXT DEFAULT '[]',  -- JSON array of positions
        relevance_score REAL DEFAULT 0.0,
        
        -- Foreign key constraint
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        
        -- Constraints
        CHECK (frequency > 0),
        CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
        
        -- Ensure unique keyword per document
        UNIQUE (document_id, keyword)
    );
    """
    
    CREATE_SEARCH_CACHE_TABLE = """
    CREATE TABLE IF NOT EXISTS search_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_hash TEXT NOT NULL UNIQUE,
        query_text TEXT NOT NULL,
        results TEXT NOT NULL DEFAULT '[]',  -- JSON array of results
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL,
        hit_count INTEGER DEFAULT 0,
        
        -- Constraints
        CHECK (hit_count >= 0),
        CHECK (expires_at > created_at)
    );
    """
    
    # High-performance indexes for sub-200ms queries
    CREATE_INDEXES = [
        # Primary search performance indexes
        "CREATE INDEX IF NOT EXISTS idx_documents_path ON documents(file_path);",
        "CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(file_type);",
        "CREATE INDEX IF NOT EXISTS idx_documents_modified ON documents(modified_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_documents_indexed ON documents(indexed_at DESC);",
        
        # Metadata search indexes
        "CREATE INDEX IF NOT EXISTS idx_metadata_key ON document_metadata(key);",
        "CREATE INDEX IF NOT EXISTS idx_metadata_value ON document_metadata(value);",
        "CREATE INDEX IF NOT EXISTS idx_metadata_document_key ON document_metadata(document_id, key);",
        
        # Search index optimization
        "CREATE INDEX IF NOT EXISTS idx_search_keyword ON search_index(keyword);",
        "CREATE INDEX IF NOT EXISTS idx_search_relevance ON search_index(relevance_score DESC);",
        "CREATE INDEX IF NOT EXISTS idx_search_keyword_relevance ON search_index(keyword, relevance_score DESC);",
        "CREATE INDEX IF NOT EXISTS idx_search_document_keyword ON search_index(document_id, keyword);",
        
        # Cache management indexes
        "CREATE INDEX IF NOT EXISTS idx_cache_hash ON search_cache(query_hash);",
        "CREATE INDEX IF NOT EXISTS idx_cache_expires ON search_cache(expires_at);",
        "CREATE INDEX IF NOT EXISTS idx_cache_created ON search_cache(created_at DESC);",
        
        # Compound indexes for complex queries
        "CREATE INDEX IF NOT EXISTS idx_documents_type_modified ON documents(file_type, modified_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_search_freq_score ON search_index(frequency DESC, relevance_score DESC);",
    ]
    
    # Full-text search virtual table for advanced search
    CREATE_FTS_TABLE = """
    CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
        file_name,
        content,
        file_type
    );
    """
    
    # Trigger to maintain FTS table sync
    CREATE_FTS_TRIGGERS = [
        """
        CREATE TRIGGER IF NOT EXISTS documents_fts_insert AFTER INSERT ON documents
        BEGIN
            INSERT INTO documents_fts(rowid, file_name, content, file_type)
            VALUES (NEW.id, NEW.file_name, NEW.content, NEW.file_type);
        END;
        """,
        
        """
        CREATE TRIGGER IF NOT EXISTS documents_fts_update AFTER UPDATE ON documents
        BEGIN
            UPDATE documents_fts 
            SET file_name = NEW.file_name, 
                content = NEW.content, 
                file_type = NEW.file_type
            WHERE rowid = NEW.id;
        END;
        """,
        
        """
        CREATE TRIGGER IF NOT EXISTS documents_fts_delete AFTER DELETE ON documents
        BEGIN
            DELETE FROM documents_fts WHERE rowid = OLD.id;
        END;
        """
    ]
    
    @classmethod
    def get_all_ddl_statements(cls) -> List[str]:
        """Get all DDL statements in proper order."""
        statements = [
            cls.CREATE_DOCUMENTS_TABLE,
            cls.CREATE_DOCUMENT_METADATA_TABLE,
            cls.CREATE_SEARCH_INDEX_TABLE,
            cls.CREATE_SEARCH_CACHE_TABLE,
            cls.CREATE_FTS_TABLE
        ]
        
        # Add all indexes
        statements.extend(cls.CREATE_INDEXES)
        
        # Add FTS triggers
        statements.extend(cls.CREATE_FTS_TRIGGERS)
        
        return statements
    
    @classmethod
    async def apply_performance_pragmas(cls, connection: aiosqlite.Connection) -> None:
        """Apply SQLite performance optimization pragmas."""
        for pragma, value in cls.PERFORMANCE_PRAGMAS.items():
            if value is not None:
                await connection.execute(f"PRAGMA {pragma}={value}")
            else:
                await connection.execute(f"PRAGMA {pragma}")
    
    @classmethod
    async def initialize_schema(cls, connection: aiosqlite.Connection) -> None:
        """Initialize the complete database schema."""
        # Apply performance pragmas first
        await cls.apply_performance_pragmas(connection)
        
        # Execute all DDL statements
        for statement in cls.get_all_ddl_statements():
            await connection.execute(statement)
        
        # Commit all changes
        await connection.commit()
    
    @classmethod
    async def get_schema_version(cls, connection: aiosqlite.Connection) -> int:
        """Get current schema version from database."""
        try:
            async with connection.execute("PRAGMA user_version") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
        except Exception:
            return 0
    
    @classmethod
    async def set_schema_version(cls, connection: aiosqlite.Connection, version: int) -> None:
        """Set schema version in database."""
        await connection.execute(f"PRAGMA user_version = {version}")
        await connection.commit()


# Type aliases for better code clarity
DocumentId = int
QueryHash = str
KeywordScore = float
DocumentContent = str