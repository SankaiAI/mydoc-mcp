"""
Parser Factory for mydocs-mcp

This module provides a factory pattern for creating and managing
document parsers, with automatic parser selection based on file
types and content analysis.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Type, Union

from .base import DocumentParser, ParserResult, ParseError
from .markdown_parser import MarkdownParser
from .text_parser import TextParser


class ParserFactory:
    """
    Factory for creating and managing document parsers.
    
    Provides automatic parser selection, parser registration,
    and centralized parser management with performance optimization
    and error handling.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize parser factory.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Registry of available parsers
        self._parsers: Dict[str, Type[DocumentParser]] = {}
        self._parser_instances: Dict[str, DocumentParser] = {}
        self._extension_mapping: Dict[str, str] = {}
        
        # Performance tracking
        self._parser_usage_stats: Dict[str, int] = {}
        self._total_parses = 0
        self._failed_parses = 0
        
        # Initialize with default parsers
        self._register_default_parsers()
    
    def _register_default_parsers(self) -> None:
        """Register the default set of parsers."""
        self.register_parser('markdown', MarkdownParser)
        self.register_parser('text', TextParser)
        
        self.logger.info(f"Registered {len(self._parsers)} default parsers")
    
    def register_parser(self, name: str, parser_class: Type[DocumentParser]) -> None:
        """
        Register a new parser class.
        
        Args:
            name: Unique name for the parser
            parser_class: Parser class to register
            
        Raises:
            ValueError: If parser name already exists or parser is invalid
        """
        if not issubclass(parser_class, DocumentParser):
            raise ValueError(f"Parser class must inherit from DocumentParser: {parser_class}")
        
        if name in self._parsers:
            self.logger.warning(f"Overriding existing parser: {name}")
        
        self._parsers[name] = parser_class
        self._parser_usage_stats[name] = 0
        
        # Create instance to get supported extensions
        try:
            temp_instance = parser_class(logger=self.logger)
            extensions = temp_instance.get_supported_extensions()
            
            # Map extensions to parser name
            for ext in extensions:
                if ext in self._extension_mapping:
                    self.logger.debug(f"Extension {ext} already mapped to {self._extension_mapping[ext]}, overriding with {name}")
                self._extension_mapping[ext] = name
            
            self.logger.info(f"Registered parser '{name}' for extensions: {', '.join(extensions)}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize parser '{name}': {e}")
            raise ValueError(f"Invalid parser class: {e}")
    
    def unregister_parser(self, name: str) -> bool:
        """
        Unregister a parser.
        
        Args:
            name: Name of parser to unregister
            
        Returns:
            True if parser was unregistered, False if not found
        """
        if name not in self._parsers:
            return False
        
        # Remove from instances cache
        if name in self._parser_instances:
            del self._parser_instances[name]
        
        # Remove extension mappings
        parser_class = self._parsers[name]
        try:
            temp_instance = parser_class(logger=self.logger)
            extensions = temp_instance.get_supported_extensions()
            for ext in extensions:
                if self._extension_mapping.get(ext) == name:
                    del self._extension_mapping[ext]
        except Exception as e:
            self.logger.warning(f"Error during parser cleanup: {e}")
        
        # Remove parser
        del self._parsers[name]
        if name in self._parser_usage_stats:
            del self._parser_usage_stats[name]
        
        self.logger.info(f"Unregistered parser: {name}")
        return True
    
    def get_parser_for_file(self, file_path: Union[str, Path]) -> Optional[DocumentParser]:
        """
        Get appropriate parser for a file based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Parser instance or None if no suitable parser found
        """
        try:
            path_obj = Path(file_path)
            extension = path_obj.suffix.lower()
            
            # Find parser by extension
            parser_name = self._extension_mapping.get(extension)
            
            if not parser_name:
                # Fallback to text parser for unknown extensions
                parser_name = 'text'
                self.logger.debug(f"No specific parser for {extension}, using text parser")
            
            return self.get_parser(parser_name)
            
        except Exception as e:
            self.logger.error(f"Failed to get parser for file {file_path}: {e}")
            return None
    
    def get_parser(self, parser_name: str) -> Optional[DocumentParser]:
        """
        Get parser instance by name.
        
        Args:
            parser_name: Name of the parser
            
        Returns:
            Parser instance or None if not found
        """
        if parser_name not in self._parsers:
            self.logger.error(f"Unknown parser: {parser_name}")
            return None
        
        # Use cached instance or create new one
        if parser_name not in self._parser_instances:
            try:
                parser_class = self._parsers[parser_name]
                self._parser_instances[parser_name] = parser_class(logger=self.logger)
                self.logger.debug(f"Created new instance of parser: {parser_name}")
            except Exception as e:
                self.logger.error(f"Failed to create parser instance '{parser_name}': {e}")
                return None
        
        return self._parser_instances[parser_name]
    
    async def parse_file(self, file_path: Union[str, Path]) -> ParserResult:
        """
        Parse a file using the appropriate parser.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            ParserResult containing parsed data
        """
        self._total_parses += 1
        
        try:
            # Get appropriate parser
            parser = self.get_parser_for_file(file_path)
            
            if not parser:
                self._failed_parses += 1
                return ParserResult(
                    success=False,
                    error_message=f"No suitable parser found for file: {file_path}"
                )
            
            # Update usage stats
            parser_name = parser.__class__.__name__.replace('Parser', '').lower()
            if parser_name in self._parser_usage_stats:
                self._parser_usage_stats[parser_name] += 1
            
            # Parse the file
            result = await parser.parse_file(file_path)
            
            if not result.success:
                self._failed_parses += 1
                self.logger.warning(f"Parse failed for {file_path}: {result.error_message}")
            else:
                self.logger.debug(f"Successfully parsed {file_path} using {parser_name} parser")
            
            # Add parser information to result metadata
            if result.parsing_stats:
                result.parsing_stats['factory_parser'] = parser_name
            
            return result
            
        except Exception as e:
            self._failed_parses += 1
            error_msg = f"Factory parse failed for {file_path}: {str(e)}"
            self.logger.error(error_msg)
            
            return ParserResult(
                success=False,
                error_message=error_msg
            )
    
    async def parse_content(self, 
                           content: str, 
                           content_type: str = 'text',
                           file_path: Optional[str] = None) -> ParserResult:
        """
        Parse content using specified parser type.
        
        Args:
            content: Content to parse
            content_type: Type of content ('text', 'markdown', etc.)
            file_path: Optional file path for context
            
        Returns:
            ParserResult containing parsed data
        """
        self._total_parses += 1
        
        try:
            # Get parser by type
            parser = self.get_parser(content_type)
            
            if not parser:
                self._failed_parses += 1
                return ParserResult(
                    success=False,
                    error_message=f"No parser available for content type: {content_type}"
                )
            
            # Update usage stats
            if content_type in self._parser_usage_stats:
                self._parser_usage_stats[content_type] += 1
            
            # Parse the content
            result = await parser.parse_content(content, file_path)
            
            if not result.success:
                self._failed_parses += 1
                self.logger.warning(f"Content parse failed: {result.error_message}")
            else:
                self.logger.debug(f"Successfully parsed content using {content_type} parser")
            
            # Add parser information to result metadata
            if result.parsing_stats:
                result.parsing_stats['factory_parser'] = content_type
            
            return result
            
        except Exception as e:
            self._failed_parses += 1
            error_msg = f"Factory content parse failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ParserResult(
                success=False,
                error_message=error_msg
            )
    
    def get_supported_extensions(self) -> Set[str]:
        """
        Get all supported file extensions across all parsers.
        
        Returns:
            Set of supported extensions
        """
        return set(self._extension_mapping.keys())
    
    def get_parser_for_extension(self, extension: str) -> Optional[str]:
        """
        Get parser name for a specific file extension.
        
        Args:
            extension: File extension (e.g., '.md')
            
        Returns:
            Parser name or None if not supported
        """
        return self._extension_mapping.get(extension.lower())
    
    def list_available_parsers(self) -> List[Dict[str, any]]:
        """
        List all available parsers with their information.
        
        Returns:
            List of parser information dictionaries
        """
        parser_info = []
        
        for name, parser_class in self._parsers.items():
            try:
                # Get parser instance to access information
                parser = self.get_parser(name)
                if parser:
                    extensions = parser.get_supported_extensions()
                    stats = parser.get_parser_stats() if hasattr(parser, 'get_parser_stats') else {}
                    
                    info = {
                        'name': name,
                        'class_name': parser_class.__name__,
                        'supported_extensions': list(extensions),
                        'usage_count': self._parser_usage_stats.get(name, 0),
                        'stats': stats
                    }
                    parser_info.append(info)
                    
            except Exception as e:
                self.logger.debug(f"Error getting info for parser {name}: {e}")
        
        return parser_info
    
    def supports_file(self, file_path: Union[str, Path]) -> bool:
        """
        Check if any parser supports the given file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is supported
        """
        extension = Path(file_path).suffix.lower()
        return extension in self._extension_mapping
    
    def get_factory_stats(self) -> Dict[str, any]:
        """
        Get factory performance and usage statistics.
        
        Returns:
            Dictionary containing factory statistics
        """
        success_rate = (
            (self._total_parses - self._failed_parses) / self._total_parses
            if self._total_parses > 0 else 1.0
        )
        
        return {
            'total_parses': self._total_parses,
            'successful_parses': self._total_parses - self._failed_parses,
            'failed_parses': self._failed_parses,
            'success_rate': success_rate,
            'registered_parsers': len(self._parsers),
            'supported_extensions': len(self._extension_mapping),
            'parser_usage': self._parser_usage_stats.copy(),
            'extension_mapping': self._extension_mapping.copy()
        }
    
    def reset_stats(self) -> None:
        """Reset factory statistics."""
        self._total_parses = 0
        self._failed_parses = 0
        self._parser_usage_stats = {name: 0 for name in self._parsers.keys()}
        
        # Reset individual parser stats
        for parser in self._parser_instances.values():
            if hasattr(parser, 'reset_stats'):
                parser.reset_stats()
    
    def clear_parser_cache(self) -> None:
        """Clear cached parser instances."""
        self._parser_instances.clear()
        self.logger.debug("Cleared parser instance cache")
    
    def __str__(self) -> str:
        """String representation of factory."""
        return f"ParserFactory(parsers={len(self._parsers)}, extensions={len(self._extension_mapping)})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        parsers = list(self._parsers.keys())
        extensions = list(self._extension_mapping.keys())
        return (f"ParserFactory("
                f"parsers={parsers}, "
                f"extensions={extensions}, "
                f"total_parses={self._total_parses})")


# Global factory instance for convenience
_default_factory: Optional[ParserFactory] = None


def get_default_factory(logger: Optional[logging.Logger] = None) -> ParserFactory:
    """
    Get or create the default parser factory instance.
    
    Args:
        logger: Optional logger for factory
        
    Returns:
        Default ParserFactory instance
    """
    global _default_factory
    
    if _default_factory is None:
        _default_factory = ParserFactory(logger=logger)
    
    return _default_factory


def reset_default_factory() -> None:
    """Reset the default factory instance (useful for testing)."""
    global _default_factory
    _default_factory = None


# Convenience functions using the default factory
async def parse_file(file_path: Union[str, Path], 
                    logger: Optional[logging.Logger] = None) -> ParserResult:
    """
    Parse a file using the default factory.
    
    Args:
        file_path: Path to file to parse
        logger: Optional logger
        
    Returns:
        ParserResult containing parsed data
    """
    factory = get_default_factory(logger)
    return await factory.parse_file(file_path)


async def parse_content(content: str, 
                       content_type: str = 'text',
                       file_path: Optional[str] = None,
                       logger: Optional[logging.Logger] = None) -> ParserResult:
    """
    Parse content using the default factory.
    
    Args:
        content: Content to parse
        content_type: Type of content
        file_path: Optional file path for context
        logger: Optional logger
        
    Returns:
        ParserResult containing parsed data
    """
    factory = get_default_factory(logger)
    return await factory.parse_content(content, content_type, file_path)


def supports_file(file_path: Union[str, Path], 
                 logger: Optional[logging.Logger] = None) -> bool:
    """
    Check if a file is supported using the default factory.
    
    Args:
        file_path: Path to check
        logger: Optional logger
        
    Returns:
        True if file is supported
    """
    factory = get_default_factory(logger)
    return factory.supports_file(file_path)


def get_supported_extensions(logger: Optional[logging.Logger] = None) -> Set[str]:
    """
    Get all supported extensions using the default factory.
    
    Args:
        logger: Optional logger
        
    Returns:
        Set of supported extensions
    """
    factory = get_default_factory(logger)
    return factory.get_supported_extensions()