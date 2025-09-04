"""
mydocs-mcp Database Layer

This package provides the complete database abstraction layer for the mydocs-mcp project.
It implements high-performance SQLite database operations with async support, proper
indexing for sub-200ms query response times, and comprehensive document storage.

Key Components:
- models.py: Database schema and models
- connection.py: Async connection management with pooling
- queries.py: Query functions for document operations
- migrations.py: Schema versioning and migration system
"""

from .models import (
    Document,
    DocumentMetadata,
    SearchIndex,
    SearchCache,
    DatabaseSchema
)

from .connection import (
    DatabaseConnection,
    ConnectionManager,
    get_database_connection
)

from .queries import (
    DocumentQueries,
    SearchQueries,
    MetadataQueries
)

from .database_manager import (
    DocumentManager,
    create_document_manager
)

from .migrations import (
    MigrationManager,
    initialize_database,
    get_database_status
)

__all__ = [
    # Models
    'Document',
    'DocumentMetadata', 
    'SearchIndex',
    'SearchCache',
    'DatabaseSchema',
    
    # Connection Management
    'DatabaseConnection',
    'ConnectionManager', 
    'get_database_connection',
    
    # Query Interfaces
    'DocumentQueries',
    'SearchQueries',
    'MetadataQueries',
    
    # Database Management
    'DocumentManager',
    'create_document_manager',
    
    # Migration System
    'MigrationManager',
    'initialize_database',
    'get_database_status'
]