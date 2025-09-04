"""
Base Document Parser for mydocs-mcp

This module provides the abstract base class for all document parsers,
defining the interface and common functionality for document parsing
with metadata extraction and keyword generation.
"""

import asyncio
import hashlib
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import aiofiles


@dataclass
class ParserResult:
    """
    Result from document parsing operation.
    
    Contains parsed content, extracted metadata, keywords, and parsing statistics.
    """
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    file_info: Dict[str, Any] = field(default_factory=dict)
    parsing_stats: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization validation and defaults."""
        if not self.file_info:
            self.file_info = {}
        
        if not self.parsing_stats:
            self.parsing_stats = {
                "parse_time_ms": 0.0,
                "content_length": len(self.content),
                "keyword_count": len(self.keywords),
                "metadata_fields": len(self.metadata)
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parser result to dictionary for serialization."""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "keywords": self.keywords,
            "file_info": self.file_info,
            "parsing_stats": self.parsing_stats,
            "success": self.success,
            "error_message": self.error_message
        }


class DocumentParser(ABC):
    """
    Abstract base class for all document parsers.
    
    Defines the interface that all document parsers must implement,
    providing common functionality for file handling, validation,
    and basic text processing.
    """
    
    # Default stop words for keyword extraction
    STOP_WORDS = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'this', 'that', 'these', 'those', 'a', 'an', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'shall',
        'his', 'her', 'its', 'their', 'our', 'my', 'your', 'he', 'she', 'it', 'they',
        'we', 'i', 'you', 'me', 'us', 'him', 'them', 'who', 'what', 'when', 'where',
        'why', 'how', 'which', 'whom', 'whose', 'all', 'any', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now', 'get',
        'make', 'take', 'come', 'go', 'see', 'know', 'think', 'look', 'use', 'find',
        'give', 'tell', 'work', 'become', 'leave', 'feel', 'put', 'mean', 'keep',
        'let', 'begin', 'seem', 'help', 'talk', 'turn', 'start', 'show', 'hear',
        'play', 'run', 'move', 'like', 'live', 'believe', 'hold', 'bring', 'happen',
        'write', 'provide', 'sit', 'stand', 'lose', 'pay', 'meet', 'include', 'continue'
    }
    
    def __init__(self, 
                 logger: Optional[logging.Logger] = None,
                 min_keyword_length: int = 3,
                 max_keywords: int = 100,
                 enable_async: bool = True):
        """
        Initialize document parser.
        
        Args:
            logger: Optional logger instance
            min_keyword_length: Minimum length for extracted keywords
            max_keywords: Maximum number of keywords to extract
            enable_async: Whether to use async file operations
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.min_keyword_length = min_keyword_length
        self.max_keywords = max_keywords
        self.enable_async = enable_async
        
        # Parser configuration
        self.supported_extensions: Set[str] = set()
        self.parser_name = self.__class__.__name__
        
        # Performance tracking
        self._parse_count = 0
        self._total_parse_time = 0.0
        self._error_count = 0
    
    @abstractmethod
    def get_supported_extensions(self) -> Set[str]:
        """
        Get file extensions supported by this parser.
        
        Returns:
            Set of supported file extensions (e.g., {'.md', '.markdown'})
        """
        pass
    
    @abstractmethod
    async def parse_content(self, content: str, file_path: Optional[str] = None) -> ParserResult:
        """
        Parse document content and extract metadata.
        
        Args:
            content: Document content to parse
            file_path: Optional file path for context
            
        Returns:
            ParserResult containing parsed data
        """
        pass
    
    async def parse_file(self, file_path: Union[str, Path]) -> ParserResult:
        """
        Parse a document file from disk.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ParserResult containing parsed data
        """
        start_time = time.time()
        
        try:
            file_path = Path(file_path)
            
            # Validate file exists and is readable
            if not file_path.exists():
                return ParserResult(
                    success=False,
                    error_message=f"File does not exist: {file_path}"
                )
            
            if not file_path.is_file():
                return ParserResult(
                    success=False,
                    error_message=f"Path is not a file: {file_path}"
                )
            
            # Check file extension support
            if not self.supports_file(file_path):
                return ParserResult(
                    success=False,
                    error_message=f"Unsupported file type: {file_path.suffix}"
                )
            
            # Read file content
            if self.enable_async:
                content = await self._read_file_async(file_path)
            else:
                content = await self._read_file_sync(file_path)
            
            # Extract basic file information
            file_stat = file_path.stat()
            file_info = {
                "file_path": str(file_path.absolute()),
                "file_name": file_path.name,
                "file_size": file_stat.st_size,
                "file_extension": file_path.suffix.lower(),
                "created_at": datetime.fromtimestamp(file_stat.st_ctime),
                "modified_at": datetime.fromtimestamp(file_stat.st_mtime),
                "file_hash": self._calculate_file_hash(content)
            }
            
            # Parse content
            result = await self.parse_content(content, str(file_path))
            
            # Add file information to result
            result.file_info.update(file_info)
            
            # Update parsing statistics
            parse_time = (time.time() - start_time) * 1000
            result.parsing_stats.update({
                "parse_time_ms": parse_time,
                "parser_name": self.parser_name,
                "content_length": len(content),
                "keyword_count": len(result.keywords),
                "metadata_fields": len(result.metadata)
            })
            
            # Track performance metrics
            self._parse_count += 1
            self._total_parse_time += parse_time
            
            if result.success:
                self.logger.debug(f"Parsed {file_path.name} in {parse_time:.2f}ms")
            else:
                self._error_count += 1
                self.logger.warning(f"Parse failed for {file_path.name}: {result.error_message}")
            
            return result
            
        except Exception as e:
            self._error_count += 1
            error_msg = f"Failed to parse file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            
            return ParserResult(
                success=False,
                error_message=error_msg,
                parsing_stats={
                    "parse_time_ms": (time.time() - start_time) * 1000,
                    "parser_name": self.parser_name
                }
            )
    
    def supports_file(self, file_path: Union[str, Path]) -> bool:
        """
        Check if this parser supports the given file type.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file type is supported
        """
        extension = Path(file_path).suffix.lower()
        return extension in self.get_supported_extensions()
    
    async def _read_file_async(self, file_path: Path) -> str:
        """Read file content asynchronously."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                return await file.read()
        except UnicodeDecodeError:
            # Fallback to binary reading for encoding detection
            async with aiofiles.open(file_path, 'rb') as file:
                content_bytes = await file.read()
                # Try common encodings
                for encoding in ['utf-8', 'utf-16', 'latin-1', 'cp1252']:
                    try:
                        return content_bytes.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                # Final fallback - replace errors
                return content_bytes.decode('utf-8', errors='replace')
    
    async def _read_file_sync(self, file_path: Path) -> str:
        """Read file content synchronously (fallback)."""
        def _read():
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            except UnicodeDecodeError:
                with open(file_path, 'rb') as file:
                    content_bytes = file.read()
                    for encoding in ['utf-8', 'utf-16', 'latin-1', 'cp1252']:
                        try:
                            return content_bytes.decode(encoding)
                        except UnicodeDecodeError:
                            continue
                    return content_bytes.decode('utf-8', errors='replace')
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _read)
    
    def _calculate_file_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def extract_keywords(self, content: str, custom_stop_words: Optional[Set[str]] = None) -> List[str]:
        """
        Extract keywords from text content.
        
        Args:
            content: Text content to analyze
            custom_stop_words: Optional additional stop words to filter
            
        Returns:
            List of extracted keywords
        """
        if not content:
            return []
        
        # Combine default and custom stop words
        stop_words = self.STOP_WORDS.copy()
        if custom_stop_words:
            stop_words.update(custom_stop_words)
        
        # Extract words (alphanumeric, minimum length)
        words = re.findall(r'\b[a-zA-Z0-9_]+\b', content.lower())
        
        # Filter and count words
        word_freq = {}
        for word in words:
            if (len(word) >= self.min_keyword_length and 
                word not in stop_words and
                not word.isdigit()):
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and limit results
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in keywords[:self.max_keywords]]
    
    def get_parser_stats(self) -> Dict[str, Any]:
        """
        Get parser performance statistics.
        
        Returns:
            Dictionary containing parser statistics
        """
        avg_parse_time = (
            self._total_parse_time / self._parse_count 
            if self._parse_count > 0 else 0.0
        )
        
        return {
            "parser_name": self.parser_name,
            "supported_extensions": list(self.get_supported_extensions()),
            "total_parses": self._parse_count,
            "total_parse_time_ms": self._total_parse_time,
            "average_parse_time_ms": avg_parse_time,
            "error_count": self._error_count,
            "success_rate": (
                (self._parse_count - self._error_count) / self._parse_count
                if self._parse_count > 0 else 1.0
            )
        }
    
    def reset_stats(self) -> None:
        """Reset parser performance statistics."""
        self._parse_count = 0
        self._total_parse_time = 0.0
        self._error_count = 0
    
    def __str__(self) -> str:
        """String representation of parser."""
        extensions = ', '.join(self.get_supported_extensions())
        return f"{self.parser_name}({extensions})"
    
    def __repr__(self) -> str:
        """Detailed string representation of parser."""
        return (f"{self.__class__.__name__}("
                f"supported_extensions={self.get_supported_extensions()}, "
                f"min_keyword_length={self.min_keyword_length}, "
                f"max_keywords={self.max_keywords})")


class ParseError(Exception):
    """Exception raised when document parsing fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, parser_name: Optional[str] = None):
        super().__init__(message)
        self.file_path = file_path
        self.parser_name = parser_name
        self.message = message
    
    def __str__(self) -> str:
        if self.file_path and self.parser_name:
            return f"[{self.parser_name}] Failed to parse {self.file_path}: {self.message}"
        elif self.parser_name:
            return f"[{self.parser_name}] {self.message}"
        else:
            return self.message