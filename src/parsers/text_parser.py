"""
Text Document Parser for mydocs-mcp

This module provides specialized parsing for plain text documents,
extracting basic metadata, structure analysis, and content processing
optimized for various text file formats.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path

from .base import DocumentParser, ParserResult, ParseError


class TextParser(DocumentParser):
    """
    Specialized parser for plain text documents.
    
    Extracts document structure, analyzes content patterns,
    detects document types, and provides optimized text processing
    for various plain text formats including logs, configuration files,
    and general text documents.
    """
    
    # Patterns for text analysis
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    URL_PATTERN = re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w)*)?)?')
    PHONE_PATTERN = re.compile(r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})')
    DATE_PATTERN = re.compile(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b')
    TIME_PATTERN = re.compile(r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:[AP]M)?\b', re.IGNORECASE)
    
    # Log file patterns
    LOG_LEVEL_PATTERN = re.compile(r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE)\b', re.IGNORECASE)
    LOG_TIMESTAMP_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}')
    
    # Configuration file patterns
    CONFIG_KEY_VALUE_PATTERN = re.compile(r'^([^=:\s]+)\s*[=:]\s*(.+)$', re.MULTILINE)
    INI_SECTION_PATTERN = re.compile(r'^\[([^\]]+)\]$', re.MULTILINE)
    
    # Code-like patterns
    FUNCTION_PATTERN = re.compile(r'\b\w+\s*\([^)]*\)\s*{?', re.MULTILINE)
    VARIABLE_ASSIGNMENT_PATTERN = re.compile(r'^\s*\w+\s*=\s*.+$', re.MULTILINE)
    
    def __init__(self, 
                 logger=None,
                 detect_document_type: bool = True,
                 extract_entities: bool = True,
                 analyze_structure: bool = True,
                 max_line_sample: int = 1000):
        """
        Initialize text parser.
        
        Args:
            logger: Optional logger instance
            detect_document_type: Whether to detect specific document types
            extract_entities: Whether to extract entities (emails, URLs, etc.)
            analyze_structure: Whether to analyze document structure
            max_line_sample: Maximum lines to sample for type detection
        """
        super().__init__(logger=logger)
        self.detect_document_type = detect_document_type
        self.extract_entities = extract_entities
        self.analyze_structure = analyze_structure
        self.max_line_sample = max_line_sample
        
        # Text-specific stop words
        self.text_stop_words = {
            'txt', 'text', 'file', 'document', 'doc', 'log', 'config',
            'conf', 'cfg', 'ini', 'properties', 'settings', 'prefs',
            'data', 'output', 'input', 'temp', 'tmp', 'backup', 'bak'
        }
    
    def get_supported_extensions(self) -> Set[str]:
        """Get file extensions supported by this parser."""
        return {
            '.txt', '.text', '.log', '.cfg', '.conf', '.config', '.ini',
            '.properties', '.env', '.dat', '.csv', '.tsv', '.json', '.xml',
            '.yaml', '.yml', '.sql', '.py', '.js', '.css', '.html', '.htm',
            '.sh', '.bat', '.cmd', '.ps1', '.dockerfile', '.gitignore',
            '.license', '.changelog', '.authors', '.contributors', '.install',
            '.readme', '.todo', '.fixme', '.notes'
        }
    
    async def parse_content(self, content: str, file_path: Optional[str] = None) -> ParserResult:
        """
        Parse text content and extract metadata.
        
        Args:
            content: Text content to parse
            file_path: Optional file path for context
            
        Returns:
            ParserResult containing parsed text data
        """
        try:
            result = ParserResult()
            
            if not content:
                return ParserResult(
                    success=False,
                    error_message="Empty content provided"
                )
            
            # Basic text statistics
            basic_stats = self._calculate_basic_stats(content)
            result.metadata.update(basic_stats)
            
            # Detect document type
            if self.detect_document_type:
                doc_type_info = self._detect_document_type(content, file_path)
                result.metadata.update(doc_type_info)
            
            # Extract entities (emails, URLs, etc.)
            if self.extract_entities:
                entities = self._extract_entities(content)
                result.metadata.update(entities)
            
            # Analyze document structure
            if self.analyze_structure:
                structure_info = self._analyze_structure(content)
                result.metadata.update(structure_info)
            
            # Extract type-specific metadata
            document_type = result.metadata.get('document_type', 'text')
            if document_type == 'log':
                log_metadata = self._extract_log_metadata(content)
                result.metadata.update(log_metadata)
            elif document_type == 'config':
                config_metadata = self._extract_config_metadata(content)
                result.metadata.update(config_metadata)
            elif document_type in ['code', 'script']:
                code_metadata = self._extract_code_metadata(content)
                result.metadata.update(code_metadata)
            
            # Set content for indexing (usually unchanged for text)
            result.content = self._clean_content_for_indexing(content)
            
            # Extract keywords
            result.keywords = self.extract_keywords(
                result.content, 
                custom_stop_words=self.text_stop_words
            )
            
            # Add document type as keyword
            if document_type and document_type != 'text':
                result.keywords.insert(0, document_type)
            
            result.success = True
            
            self.logger.debug(
                f"Parsed text content ({document_type}): {len(result.content)} chars, "
                f"{len(result.keywords)} keywords, {len(result.metadata)} metadata fields"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to parse text content: {str(e)}"
            self.logger.error(error_msg)
            
            return ParserResult(
                success=False,
                error_message=error_msg
            )
    
    def _calculate_basic_stats(self, content: str) -> Dict[str, Any]:
        """
        Calculate basic text statistics.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary containing basic statistics
        """
        lines = content.split('\n')
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        words = content.split()
        
        # Character analysis
        char_counts = {
            'alphabetic': sum(1 for c in content if c.isalpha()),
            'numeric': sum(1 for c in content if c.isdigit()),
            'whitespace': sum(1 for c in content if c.isspace()),
            'punctuation': sum(1 for c in content if c in '.,!?;:'),
            'special': sum(1 for c in content if not (c.isalnum() or c.isspace()))
        }
        
        return {
            'character_count': len(content),
            'word_count': len(words),
            'line_count': len(lines),
            'paragraph_count': len(paragraphs),
            'empty_line_count': len([line for line in lines if not line.strip()]),
            'average_line_length': sum(len(line) for line in lines) / len(lines) if lines else 0,
            'average_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'character_distribution': char_counts,
            'text_type': 'text'
        }
    
    def _detect_document_type(self, content: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect the type of text document based on content and file path.
        
        Args:
            content: Text content to analyze
            file_path: Optional file path for hints
            
        Returns:
            Dictionary containing document type information
        """
        doc_info = {'document_type': 'text'}
        
        try:
            # Sample content for analysis (performance optimization)
            lines = content.split('\n')
            sample_lines = lines[:self.max_line_sample]
            sample_content = '\n'.join(sample_lines)
            
            # File extension hints
            if file_path:
                path_obj = Path(file_path)
                extension = path_obj.suffix.lower()
                filename = path_obj.stem.lower()
                
                # Check by extension
                if extension in {'.log', '.out', '.err'}:
                    doc_info['document_type'] = 'log'
                elif extension in {'.cfg', '.conf', '.config', '.ini', '.properties', '.env'}:
                    doc_info['document_type'] = 'config'
                elif extension in {'.py', '.js', '.css', '.html', '.htm', '.sh', '.bat', '.cmd', '.ps1'}:
                    doc_info['document_type'] = 'code'
                elif extension in {'.csv', '.tsv'}:
                    doc_info['document_type'] = 'data'
                elif extension in {'.json', '.xml', '.yaml', '.yml'}:
                    doc_info['document_type'] = 'structured_data'
                elif extension in {'.sql'}:
                    doc_info['document_type'] = 'sql'
                
                # Check by filename
                if filename in {'readme', 'changelog', 'license', 'authors', 'contributors'}:
                    doc_info['document_type'] = filename
                elif 'todo' in filename or 'fixme' in filename:
                    doc_info['document_type'] = 'todo'
                elif 'notes' in filename:
                    doc_info['document_type'] = 'notes'
            
            # Content-based detection (override extension-based if confident)
            log_indicators = len(self.LOG_LEVEL_PATTERN.findall(sample_content))
            timestamp_indicators = len(self.LOG_TIMESTAMP_PATTERN.findall(sample_content))
            
            if log_indicators > 5 or timestamp_indicators > 3:
                doc_info['document_type'] = 'log'
                doc_info['log_confidence'] = min(1.0, (log_indicators + timestamp_indicators) / 10.0)
            
            # Configuration file detection
            config_patterns = len(self.CONFIG_KEY_VALUE_PATTERN.findall(sample_content))
            ini_sections = len(self.INI_SECTION_PATTERN.findall(sample_content))
            
            if config_patterns > 5 or ini_sections > 0:
                if doc_info['document_type'] == 'text':  # Don't override file extension hints
                    doc_info['document_type'] = 'config'
                doc_info['config_confidence'] = min(1.0, (config_patterns + ini_sections * 3) / 15.0)
            
            # Code-like content detection
            function_patterns = len(self.FUNCTION_PATTERN.findall(sample_content))
            variable_patterns = len(self.VARIABLE_ASSIGNMENT_PATTERN.findall(sample_content))
            
            if function_patterns > 2 or variable_patterns > 5:
                if doc_info['document_type'] == 'text':
                    doc_info['document_type'] = 'code'
                doc_info['code_confidence'] = min(1.0, (function_patterns * 2 + variable_patterns) / 12.0)
            
            # Structured data detection
            if sample_content.strip().startswith(('{', '[', '<')):
                doc_info['document_type'] = 'structured_data'
                doc_info['structured_confidence'] = 0.8
            
        except Exception as e:
            self.logger.debug(f"Document type detection failed: {e}")
        
        return doc_info
    
    def _extract_entities(self, content: str) -> Dict[str, Any]:
        """
        Extract entities like emails, URLs, phone numbers, dates.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary containing extracted entities
        """
        entities = {}
        
        try:
            # Extract emails
            emails = self.EMAIL_PATTERN.findall(content)
            if emails:
                entities['emails'] = list(set(emails))  # Remove duplicates
                entities['email_count'] = len(entities['emails'])
            
            # Extract URLs
            urls = self.URL_PATTERN.findall(content)
            if urls:
                entities['urls'] = list(set(urls))
                entities['url_count'] = len(entities['urls'])
            
            # Extract phone numbers
            phones = self.PHONE_PATTERN.findall(content)
            if phones:
                entities['phone_numbers'] = list(set(phones))
                entities['phone_count'] = len(entities['phone_numbers'])
            
            # Extract dates
            dates = self.DATE_PATTERN.findall(content)
            if dates:
                entities['dates'] = list(set(dates))
                entities['date_count'] = len(entities['dates'])
            
            # Extract times
            times = self.TIME_PATTERN.findall(content)
            if times:
                entities['times'] = list(set(times))
                entities['time_count'] = len(entities['times'])
            
        except Exception as e:
            self.logger.debug(f"Entity extraction failed: {e}")
        
        return entities
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """
        Analyze document structure and patterns.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary containing structure analysis
        """
        structure = {}
        
        try:
            lines = content.split('\n')
            
            # Line length analysis
            line_lengths = [len(line) for line in lines]
            if line_lengths:
                structure.update({
                    'min_line_length': min(line_lengths),
                    'max_line_length': max(line_lengths),
                    'avg_line_length': sum(line_lengths) / len(line_lengths)
                })
            
            # Indentation analysis
            indented_lines = [line for line in lines if line.startswith((' ', '\t'))]
            if indented_lines:
                structure['indented_line_count'] = len(indented_lines)
                structure['indentation_percentage'] = len(indented_lines) / len(lines) * 100
            
            # Common prefixes (for structured text like logs)
            prefixes = {}
            for line in lines[:100]:  # Sample first 100 lines
                if line.strip():
                    # Check for timestamp prefix
                    if self.LOG_TIMESTAMP_PATTERN.match(line):
                        prefixes['timestamp'] = prefixes.get('timestamp', 0) + 1
                    # Check for log level prefix
                    elif self.LOG_LEVEL_PATTERN.search(line[:20]):
                        prefixes['log_level'] = prefixes.get('log_level', 0) + 1
                    # Check for bullet points
                    elif line.strip().startswith(('-', '*', '+')):
                        prefixes['bullet'] = prefixes.get('bullet', 0) + 1
                    # Check for numbers
                    elif re.match(r'^\d+\.', line.strip()):
                        prefixes['numbered'] = prefixes.get('numbered', 0) + 1
            
            if prefixes:
                structure['common_prefixes'] = prefixes
            
            # Section detection (lines that look like headers)
            potential_headers = []
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if line_stripped and len(line_stripped) < 100:
                    # Check if line is all caps (possible header)
                    if line_stripped.isupper() and len(line_stripped) > 3:
                        potential_headers.append({'line': i + 1, 'text': line_stripped, 'type': 'caps'})
                    # Check if line is followed by dashes or equals (underlined header)
                    elif (i + 1 < len(lines) and 
                          lines[i + 1].strip() and 
                          all(c in '-=' for c in lines[i + 1].strip())):
                        potential_headers.append({'line': i + 1, 'text': line_stripped, 'type': 'underlined'})
            
            if potential_headers:
                structure['potential_headers'] = potential_headers
                structure['header_count'] = len(potential_headers)
            
        except Exception as e:
            self.logger.debug(f"Structure analysis failed: {e}")
        
        return structure
    
    def _extract_log_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata specific to log files.
        
        Args:
            content: Log content to analyze
            
        Returns:
            Dictionary containing log-specific metadata
        """
        log_metadata = {}
        
        try:
            lines = content.split('\n')
            
            # Count log levels
            level_counts = {}
            timestamps = []
            
            for line in lines:
                # Extract log levels
                level_matches = self.LOG_LEVEL_PATTERN.findall(line)
                for level in level_matches:
                    level_upper = level.upper()
                    level_counts[level_upper] = level_counts.get(level_upper, 0) + 1
                
                # Extract timestamps
                timestamp_matches = self.LOG_TIMESTAMP_PATTERN.findall(line)
                timestamps.extend(timestamp_matches)
            
            if level_counts:
                log_metadata['log_levels'] = level_counts
                log_metadata['total_log_entries'] = sum(level_counts.values())
                
                # Determine log severity distribution
                error_count = level_counts.get('ERROR', 0) + level_counts.get('FATAL', 0)
                warning_count = level_counts.get('WARN', 0) + level_counts.get('WARNING', 0)
                total_entries = sum(level_counts.values())
                
                if total_entries > 0:
                    log_metadata['error_percentage'] = (error_count / total_entries) * 100
                    log_metadata['warning_percentage'] = (warning_count / total_entries) * 100
            
            if timestamps:
                log_metadata['timestamp_count'] = len(timestamps)
                log_metadata['first_timestamp'] = min(timestamps)
                log_metadata['last_timestamp'] = max(timestamps)
            
        except Exception as e:
            self.logger.debug(f"Log metadata extraction failed: {e}")
        
        return log_metadata
    
    def _extract_config_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata specific to configuration files.
        
        Args:
            content: Configuration file content
            
        Returns:
            Dictionary containing config-specific metadata
        """
        config_metadata = {}
        
        try:
            # Extract key-value pairs
            kv_pairs = self.CONFIG_KEY_VALUE_PATTERN.findall(content)
            if kv_pairs:
                config_metadata['config_keys'] = [key.strip() for key, _ in kv_pairs]
                config_metadata['config_key_count'] = len(kv_pairs)
            
            # Extract INI sections
            sections = self.INI_SECTION_PATTERN.findall(content)
            if sections:
                config_metadata['ini_sections'] = sections
                config_metadata['ini_section_count'] = len(sections)
            
            # Detect configuration type
            if '.env' in content or 'export ' in content:
                config_metadata['config_format'] = 'environment'
            elif sections:
                config_metadata['config_format'] = 'ini'
            elif kv_pairs:
                config_metadata['config_format'] = 'properties'
            else:
                config_metadata['config_format'] = 'unknown'
            
        except Exception as e:
            self.logger.debug(f"Config metadata extraction failed: {e}")
        
        return config_metadata
    
    def _extract_code_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata specific to code files.
        
        Args:
            content: Code content to analyze
            
        Returns:
            Dictionary containing code-specific metadata
        """
        code_metadata = {}
        
        try:
            # Count functions/methods
            functions = self.FUNCTION_PATTERN.findall(content)
            if functions:
                code_metadata['function_count'] = len(functions)
            
            # Count variable assignments
            variables = self.VARIABLE_ASSIGNMENT_PATTERN.findall(content)
            if variables:
                code_metadata['variable_assignment_count'] = len(variables)
            
            # Count comments (basic detection)
            comment_patterns = [
                r'//.*$',      # C-style comments
                r'#.*$',       # Python/shell comments
                r'/\*.*?\*/',  # Multi-line C comments
                r'<!--.*?-->'  # HTML comments
            ]
            
            total_comments = 0
            for pattern in comment_patterns:
                total_comments += len(re.findall(pattern, content, re.MULTILINE | re.DOTALL))
            
            if total_comments > 0:
                code_metadata['comment_count'] = total_comments
            
        except Exception as e:
            self.logger.debug(f"Code metadata extraction failed: {e}")
        
        return code_metadata
    
    def _clean_content_for_indexing(self, content: str) -> str:
        """
        Clean text content for search indexing.
        
        Args:
            content: Raw text content
            
        Returns:
            Cleaned content suitable for indexing
        """
        try:
            # For plain text, minimal cleaning is needed
            # Remove excessive whitespace
            cleaned = re.sub(r'\n{3,}', '\n\n', content)  # Multiple newlines
            cleaned = re.sub(r'[ \t]+', ' ', cleaned)     # Multiple spaces/tabs
            cleaned = cleaned.strip()
            
            return cleaned
            
        except Exception as e:
            self.logger.warning(f"Content cleaning failed: {e}")
            return content