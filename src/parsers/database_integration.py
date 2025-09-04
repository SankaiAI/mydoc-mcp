"""
Database Integration Utilities for mydocs-mcp Parsers

This module provides utilities for integrating parser results with the
database layer, handling data type conversions and ensuring compatibility
between parser output and database storage requirements.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .base import ParserResult
from ..database.models import Document


def normalize_metadata_for_database(metadata: Dict[str, Any]) -> Dict[str, str]:
    """
    Normalize parser metadata for database storage.
    
    The database stores metadata as key-value string pairs, so this function
    converts complex data types to JSON strings while preserving simple types.
    
    Args:
        metadata: Raw metadata dictionary from parser
        
    Returns:
        Dictionary with all values as strings suitable for database storage
    """
    normalized = {}
    
    for key, value in metadata.items():
        if value is None:
            continue  # Skip None values
        
        # Convert value to string representation
        if isinstance(value, str):
            normalized[key] = value
        elif isinstance(value, (int, float, bool)):
            normalized[key] = str(value)
        elif isinstance(value, datetime):
            normalized[key] = value.isoformat()
        elif isinstance(value, (list, dict)):
            # Serialize complex types as JSON
            normalized[key] = json.dumps(value, default=str)
        else:
            # Fallback to string conversion
            normalized[key] = str(value)
    
    return normalized


def create_document_from_parser_result(
    file_path: str,
    parser_result: ParserResult,
    created_at: Optional[datetime] = None,
    modified_at: Optional[datetime] = None
) -> Document:
    """
    Create a Document model instance from parser result.
    
    Args:
        file_path: Path to the document file
        parser_result: Result from document parsing
        created_at: Optional creation timestamp
        modified_at: Optional modification timestamp
        
    Returns:
        Document instance ready for database storage
    """
    # Normalize metadata for database storage
    normalized_metadata = normalize_metadata_for_database(parser_result.metadata)
    
    # Create document instance
    document = Document(
        file_path=file_path,
        content=parser_result.content,
        created_at=created_at or datetime.now(),
        modified_at=modified_at or datetime.now(),
        indexed_at=datetime.now()
    )
    
    # Set metadata using the property setter (converts to JSON)
    document.metadata = normalized_metadata
    
    return document


async def index_parsed_document(
    document_manager,
    file_path: str,
    parser_result: ParserResult,
    created_at: Optional[datetime] = None,
    modified_at: Optional[datetime] = None,
    logger: Optional[logging.Logger] = None
) -> Optional[int]:
    """
    Index a parsed document in the database manager.
    
    This function handles the integration between parser results and the
    database manager, ensuring proper data type conversion and error handling.
    
    Args:
        document_manager: DocumentManager instance
        file_path: Path to the document file
        parser_result: Result from document parsing
        created_at: Optional creation timestamp
        modified_at: Optional modification timestamp
        logger: Optional logger instance
        
    Returns:
        Document ID if successful, None if failed
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        if not parser_result.success:
            logger.error(f"Cannot index failed parse result for {file_path}: {parser_result.error_message}")
            return None
        
        # Normalize metadata for database compatibility
        normalized_metadata = normalize_metadata_for_database(parser_result.metadata)
        
        # Index document using database manager
        doc_id = await document_manager.index_document(
            file_path=file_path,
            content=parser_result.content,
            metadata=normalized_metadata,
            extract_keywords=True  # Let database manager handle keyword extraction too
        )
        
        if doc_id:
            logger.info(f"Successfully indexed parsed document: {file_path} (ID: {doc_id})")
        else:
            logger.error(f"Failed to index parsed document: {file_path}")
        
        return doc_id
        
    except Exception as e:
        logger.error(f"Error indexing parsed document {file_path}: {e}")
        return None


def extract_searchable_content(parser_result: ParserResult) -> str:
    """
    Extract searchable content from parser result.
    
    Combines document content with searchable metadata fields to create
    a comprehensive searchable text string.
    
    Args:
        parser_result: Result from document parsing
        
    Returns:
        Combined searchable content
    """
    searchable_parts = [parser_result.content]
    
    # Add searchable metadata
    for key, value in parser_result.metadata.items():
        if key in ['title', 'author', 'description', 'summary']:
            if isinstance(value, str):
                searchable_parts.append(value)
        elif key == 'tags' and isinstance(value, list):
            searchable_parts.extend([str(tag) for tag in value])
        elif key == 'headers' and isinstance(value, list):
            for header in value:
                if isinstance(header, dict) and 'text' in header:
                    searchable_parts.append(header['text'])
    
    # Add keywords
    if parser_result.keywords:
        searchable_parts.extend(parser_result.keywords)
    
    return ' '.join(searchable_parts)


def get_document_type_priority(parser_result: ParserResult) -> int:
    """
    Get priority score for document type detection.
    
    Used for resolving conflicts when multiple parsers could handle
    the same file type.
    
    Args:
        parser_result: Result from document parsing
        
    Returns:
        Priority score (higher = more confident)
    """
    doc_type = parser_result.metadata.get('document_type', 'unknown')
    
    # Priority mapping
    priority_map = {
        'markdown': 10,
        'code': 8,
        'log': 7,
        'config': 6,
        'structured_data': 5,
        'text': 3,
        'unknown': 1
    }
    
    return priority_map.get(doc_type, 1)


class DatabaseIntegrationHelper:
    """
    Helper class for parser-database integration operations.
    
    Provides a centralized interface for common integration tasks
    with consistent error handling and logging.
    """
    
    def __init__(self, document_manager, logger: Optional[logging.Logger] = None):
        """
        Initialize integration helper.
        
        Args:
            document_manager: DocumentManager instance
            logger: Optional logger instance
        """
        self.document_manager = document_manager
        self.logger = logger or logging.getLogger(__name__)
        
        # Statistics tracking
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
    
    async def index_parser_result(
        self,
        file_path: str,
        parser_result: ParserResult,
        **kwargs
    ) -> Optional[int]:
        """
        Index a parser result in the database.
        
        Args:
            file_path: Path to the document file
            parser_result: Result from document parsing
            **kwargs: Additional arguments for indexing
            
        Returns:
            Document ID if successful, None if failed
        """
        self.processed_count += 1
        
        try:
            doc_id = await index_parsed_document(
                self.document_manager,
                file_path,
                parser_result,
                logger=self.logger,
                **kwargs
            )
            
            if doc_id:
                self.success_count += 1
            else:
                self.error_count += 1
            
            return doc_id
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Integration helper error for {file_path}: {e}")
            return None
    
    async def batch_index_results(
        self,
        results: List[tuple[str, ParserResult]],
        max_concurrent: int = 5
    ) -> List[Optional[int]]:
        """
        Batch index multiple parser results.
        
        Args:
            results: List of (file_path, parser_result) tuples
            max_concurrent: Maximum concurrent indexing operations
            
        Returns:
            List of document IDs (None for failures)
        """
        import asyncio
        
        async def index_single(file_path: str, parser_result: ParserResult) -> Optional[int]:
            return await self.index_parser_result(file_path, parser_result)
        
        # Process in batches to avoid overwhelming the database
        doc_ids = []
        
        for i in range(0, len(results), max_concurrent):
            batch = results[i:i + max_concurrent]
            
            tasks = [
                index_single(file_path, parser_result)
                for file_path, parser_result in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Batch indexing error: {result}")
                    doc_ids.append(None)
                else:
                    doc_ids.append(result)
        
        return doc_ids
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics."""
        success_rate = (
            self.success_count / self.processed_count 
            if self.processed_count > 0 else 0.0
        )
        
        return {
            'processed_count': self.processed_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': success_rate
        }
    
    def reset_statistics(self) -> None:
        """Reset statistics counters."""
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0