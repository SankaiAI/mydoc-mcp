"""Document parsers for mydocs-mcp."""

from .base import DocumentParser, ParserResult, ParseError
from .markdown_parser import MarkdownParser
from .text_parser import TextParser
from .parser_factory import (
    ParserFactory, 
    get_default_factory, 
    parse_file, 
    parse_content, 
    supports_file, 
    get_supported_extensions
)
from .database_integration import (
    normalize_metadata_for_database,
    create_document_from_parser_result,
    index_parsed_document,
    extract_searchable_content,
    DatabaseIntegrationHelper
)

__all__ = [
    'DocumentParser',
    'ParserResult', 
    'ParseError',
    'MarkdownParser',
    'TextParser',
    'ParserFactory',
    'get_default_factory',
    'parse_file',
    'parse_content', 
    'supports_file',
    'get_supported_extensions',
    'normalize_metadata_for_database',
    'create_document_from_parser_result',
    'index_parsed_document',
    'extract_searchable_content',
    'DatabaseIntegrationHelper'
]