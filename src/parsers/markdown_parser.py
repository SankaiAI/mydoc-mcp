"""
Markdown Document Parser for mydocs-mcp

This module provides specialized parsing for Markdown documents,
extracting frontmatter metadata, headers, links, and other
Markdown-specific content with optimized performance.
"""

import re
import yaml
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path

from .base import DocumentParser, ParserResult, ParseError


class MarkdownParser(DocumentParser):
    """
    Specialized parser for Markdown documents.
    
    Extracts frontmatter metadata, document structure (headers, lists),
    links, code blocks, and other Markdown-specific elements with
    high performance for real-time indexing.
    """
    
    # Regex patterns for Markdown parsing
    FRONTMATTER_PATTERN = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL | re.MULTILINE)
    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    CODE_BLOCK_PATTERN = re.compile(r'```(\w*)\n(.*?)\n```', re.DOTALL)
    INLINE_CODE_PATTERN = re.compile(r'`([^`]+)`')
    LIST_ITEM_PATTERN = re.compile(r'^[\s]*[-*+]\s+(.+)$', re.MULTILINE)
    NUMBERED_LIST_PATTERN = re.compile(r'^[\s]*\d+\.\s+(.+)$', re.MULTILINE)
    BLOCKQUOTE_PATTERN = re.compile(r'^>\s+(.+)$', re.MULTILINE)
    TABLE_PATTERN = re.compile(r'^\|(.+)\|$', re.MULTILINE)
    
    def __init__(self, 
                 logger=None,
                 extract_frontmatter: bool = True,
                 extract_links: bool = True,
                 extract_structure: bool = True,
                 preserve_code_blocks: bool = True):
        """
        Initialize Markdown parser.
        
        Args:
            logger: Optional logger instance
            extract_frontmatter: Whether to extract YAML frontmatter
            extract_links: Whether to extract links and references
            extract_structure: Whether to extract document structure
            preserve_code_blocks: Whether to preserve code block content
        """
        super().__init__(logger=logger)
        self.extract_frontmatter = extract_frontmatter
        self.extract_links = extract_links
        self.extract_structure = extract_structure
        self.preserve_code_blocks = preserve_code_blocks
        
        # Markdown-specific stop words (in addition to base stop words)
        self.markdown_stop_words = {
            'markdown', 'md', 'readme', 'doc', 'docs', 'note', 'notes',
            'todo', 'fixme', 'hack', 'xxx', 'img', 'image', 'link',
            'href', 'url', 'http', 'https', 'www', 'com', 'org', 'net'
        }
    
    def get_supported_extensions(self) -> Set[str]:
        """Get file extensions supported by this parser."""
        return {'.md', '.markdown', '.mdown', '.mkd', '.mkdn'}
    
    async def parse_content(self, content: str, file_path: Optional[str] = None) -> ParserResult:
        """
        Parse Markdown content and extract metadata.
        
        Args:
            content: Markdown content to parse
            file_path: Optional file path for context
            
        Returns:
            ParserResult containing parsed Markdown data
        """
        try:
            result = ParserResult()
            
            if not content:
                return ParserResult(
                    success=False,
                    error_message="Empty content provided"
                )
            
            # Extract frontmatter metadata
            frontmatter_data = {}
            clean_content = content
            
            if self.extract_frontmatter:
                frontmatter_data, clean_content = self._extract_frontmatter(content)
                result.metadata.update(frontmatter_data)
            
            # Extract document structure
            if self.extract_structure:
                structure_data = self._extract_structure(clean_content)
                result.metadata.update(structure_data)
            
            # Extract links and references
            if self.extract_links:
                link_data = self._extract_links(clean_content)
                result.metadata.update(link_data)
            
            # Extract additional Markdown-specific metadata
            markdown_metadata = self._extract_markdown_metadata(clean_content, file_path)
            result.metadata.update(markdown_metadata)
            
            # Generate content for indexing (cleaned of Markdown syntax)
            result.content = self._clean_content_for_indexing(clean_content)
            
            # Extract keywords from cleaned content
            result.keywords = self.extract_keywords(
                result.content, 
                custom_stop_words=self.markdown_stop_words
            )
            
            # Add Markdown-specific keywords from structure
            structure_keywords = self._extract_structure_keywords(clean_content)
            result.keywords.extend(structure_keywords)
            
            # Remove duplicates while preserving order
            result.keywords = list(dict.fromkeys(result.keywords))
            
            result.success = True
            
            self.logger.debug(
                f"Parsed Markdown content: {len(result.content)} chars, "
                f"{len(result.keywords)} keywords, {len(result.metadata)} metadata fields"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to parse Markdown content: {str(e)}"
            self.logger.error(error_msg)
            
            return ParserResult(
                success=False,
                error_message=error_msg
            )
    
    def _extract_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Extract YAML frontmatter from Markdown content.
        
        Args:
            content: Markdown content with potential frontmatter
            
        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter)
        """
        frontmatter_data = {}
        
        try:
            match = self.FRONTMATTER_PATTERN.match(content)
            if match:
                yaml_content = match.group(1)
                remaining_content = content[match.end():]
                
                # Parse YAML frontmatter
                try:
                    frontmatter_data = yaml.safe_load(yaml_content) or {}
                    
                    # Ensure frontmatter is a dictionary
                    if not isinstance(frontmatter_data, dict):
                        self.logger.warning("Frontmatter is not a dictionary, ignoring")
                        frontmatter_data = {}
                    else:
                        # Convert datetime objects to ISO strings
                        for key, value in frontmatter_data.items():
                            if isinstance(value, datetime):
                                frontmatter_data[key] = value.isoformat()
                            elif isinstance(value, list):
                                # Handle list values (tags, categories, etc.)
                                frontmatter_data[key] = [str(item) for item in value]
                        
                        # Add frontmatter indicator
                        frontmatter_data['has_frontmatter'] = True
                        
                except yaml.YAMLError as e:
                    self.logger.warning(f"Failed to parse YAML frontmatter: {e}")
                    frontmatter_data = {'frontmatter_error': str(e)}
                
                return frontmatter_data, remaining_content
            
        except Exception as e:
            self.logger.debug(f"Frontmatter extraction failed: {e}")
        
        return frontmatter_data, content
    
    def _extract_structure(self, content: str) -> Dict[str, Any]:
        """
        Extract document structure (headers, lists, etc.).
        
        Args:
            content: Markdown content to analyze
            
        Returns:
            Dictionary containing structure metadata
        """
        structure_data = {}
        
        try:
            # Extract headers
            headers = []
            header_matches = self.HEADER_PATTERN.findall(content)
            
            for level_markers, header_text in header_matches:
                level = len(level_markers)
                headers.append({
                    'level': level,
                    'text': header_text.strip(),
                    'anchor': self._generate_anchor(header_text.strip())
                })
            
            if headers:
                structure_data['headers'] = headers
                structure_data['header_count'] = len(headers)
                structure_data['max_header_level'] = max(h['level'] for h in headers)
                structure_data['title'] = headers[0]['text'] if headers else None
            
            # Extract list items
            list_items = []
            
            # Unordered list items
            unordered_items = self.LIST_ITEM_PATTERN.findall(content)
            list_items.extend([{'type': 'unordered', 'text': item.strip()} for item in unordered_items])
            
            # Ordered list items
            ordered_items = self.NUMBERED_LIST_PATTERN.findall(content)
            list_items.extend([{'type': 'ordered', 'text': item.strip()} for item in ordered_items])
            
            if list_items:
                structure_data['list_items'] = list_items
                structure_data['list_item_count'] = len(list_items)
            
            # Extract blockquotes
            blockquotes = self.BLOCKQUOTE_PATTERN.findall(content)
            if blockquotes:
                structure_data['blockquotes'] = [quote.strip() for quote in blockquotes]
                structure_data['blockquote_count'] = len(blockquotes)
            
            # Extract tables
            table_rows = self.TABLE_PATTERN.findall(content)
            if table_rows:
                structure_data['table_row_count'] = len(table_rows)
                structure_data['has_tables'] = True
            
        except Exception as e:
            self.logger.debug(f"Structure extraction failed: {e}")
        
        return structure_data
    
    def _extract_links(self, content: str) -> Dict[str, Any]:
        """
        Extract links and references from Markdown content.
        
        Args:
            content: Markdown content to analyze
            
        Returns:
            Dictionary containing link metadata
        """
        link_data = {}
        
        try:
            # Extract regular links
            links = []
            link_matches = self.LINK_PATTERN.findall(content)
            
            for link_text, link_url in link_matches:
                links.append({
                    'text': link_text.strip(),
                    'url': link_url.strip(),
                    'type': 'internal' if not link_url.startswith(('http://', 'https://')) else 'external'
                })
            
            if links:
                link_data['links'] = links
                link_data['link_count'] = len(links)
                link_data['external_link_count'] = sum(1 for link in links if link['type'] == 'external')
                link_data['internal_link_count'] = sum(1 for link in links if link['type'] == 'internal')
            
            # Extract images
            images = []
            image_matches = self.IMAGE_PATTERN.findall(content)
            
            for alt_text, image_url in image_matches:
                images.append({
                    'alt_text': alt_text.strip(),
                    'url': image_url.strip()
                })
            
            if images:
                link_data['images'] = images
                link_data['image_count'] = len(images)
            
        except Exception as e:
            self.logger.debug(f"Link extraction failed: {e}")
        
        return link_data
    
    def _extract_markdown_metadata(self, content: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract additional Markdown-specific metadata.
        
        Args:
            content: Markdown content to analyze
            file_path: Optional file path for context
            
        Returns:
            Dictionary containing Markdown-specific metadata
        """
        metadata = {}
        
        try:
            # Extract code blocks
            code_blocks = []
            code_matches = self.CODE_BLOCK_PATTERN.findall(content)
            
            for language, code_content in code_matches:
                code_blocks.append({
                    'language': language.strip() if language else 'text',
                    'content': code_content.strip() if self.preserve_code_blocks else '',
                    'line_count': len(code_content.strip().split('\n')) if code_content else 0
                })
            
            if code_blocks:
                metadata['code_blocks'] = code_blocks
                metadata['code_block_count'] = len(code_blocks)
                metadata['code_languages'] = list(set(block['language'] for block in code_blocks))
            
            # Extract inline code
            inline_code = self.INLINE_CODE_PATTERN.findall(content)
            if inline_code:
                metadata['inline_code_count'] = len(inline_code)
                metadata['has_inline_code'] = True
            
            # Document statistics
            lines = content.split('\n')
            metadata.update({
                'line_count': len(lines),
                'paragraph_count': len([line for line in lines if line.strip() and not line.strip().startswith('#')]),
                'character_count': len(content),
                'word_count': len(content.split()),
                'markdown_type': 'markdown'
            })
            
            # Infer document type from file path or content
            if file_path:
                file_name = Path(file_path).stem.lower()
                if 'readme' in file_name:
                    metadata['document_type'] = 'readme'
                elif 'changelog' in file_name or 'change' in file_name:
                    metadata['document_type'] = 'changelog'
                elif 'todo' in file_name:
                    metadata['document_type'] = 'todo'
                else:
                    metadata['document_type'] = 'document'
            
        except Exception as e:
            self.logger.debug(f"Markdown metadata extraction failed: {e}")
        
        return metadata
    
    def _clean_content_for_indexing(self, content: str) -> str:
        """
        Clean Markdown content for search indexing.
        
        Args:
            content: Raw Markdown content
            
        Returns:
            Cleaned content suitable for indexing
        """
        try:
            # Remove code blocks (preserve content but remove markup)
            cleaned = self.CODE_BLOCK_PATTERN.sub(r'\2', content)
            
            # Remove inline code formatting
            cleaned = self.INLINE_CODE_PATTERN.sub(r'\1', cleaned)
            
            # Remove image syntax, keep alt text
            cleaned = self.IMAGE_PATTERN.sub(r'\1', cleaned)
            
            # Remove link syntax, keep link text
            cleaned = self.LINK_PATTERN.sub(r'\1', cleaned)
            
            # Remove header markers
            cleaned = self.HEADER_PATTERN.sub(r'\2', cleaned)
            
            # Remove blockquote markers
            cleaned = self.BLOCKQUOTE_PATTERN.sub(r'\1', cleaned)
            
            # Remove list markers
            cleaned = self.LIST_ITEM_PATTERN.sub(r'\1', cleaned)
            cleaned = self.NUMBERED_LIST_PATTERN.sub(r'\1', cleaned)
            
            # Remove table formatting
            cleaned = re.sub(r'\|', ' ', cleaned)
            cleaned = re.sub(r'^\s*[-:]+\s*$', '', cleaned, flags=re.MULTILINE)
            
            # Remove emphasis markers
            cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)  # Bold
            cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)      # Italic
            cleaned = re.sub(r'__([^_]+)__', r'\1', cleaned)      # Bold
            cleaned = re.sub(r'_([^_]+)_', r'\1', cleaned)        # Italic
            cleaned = re.sub(r'~~([^~]+)~~', r'\1', cleaned)      # Strikethrough
            
            # Clean up whitespace
            cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Multiple newlines
            cleaned = re.sub(r'[ \t]+', ' ', cleaned)     # Multiple spaces/tabs
            cleaned = cleaned.strip()
            
            return cleaned
            
        except Exception as e:
            self.logger.warning(f"Content cleaning failed: {e}")
            return content
    
    def _extract_structure_keywords(self, content: str) -> List[str]:
        """
        Extract keywords from document structure elements.
        
        Args:
            content: Markdown content
            
        Returns:
            List of structure-based keywords
        """
        keywords = []
        
        try:
            # Extract keywords from headers
            header_matches = self.HEADER_PATTERN.findall(content)
            for _, header_text in header_matches:
                # Split header text into potential keywords
                header_words = re.findall(r'\b[a-zA-Z0-9_]+\b', header_text.lower())
                keywords.extend([
                    word for word in header_words 
                    if len(word) >= 3 and word not in self.STOP_WORDS
                ])
            
            # Extract keywords from link text
            link_matches = self.LINK_PATTERN.findall(content)
            for link_text, _ in link_matches:
                link_words = re.findall(r'\b[a-zA-Z0-9_]+\b', link_text.lower())
                keywords.extend([
                    word for word in link_words 
                    if len(word) >= 3 and word not in self.STOP_WORDS
                ])
            
            # Extract programming language keywords from code blocks
            code_matches = self.CODE_BLOCK_PATTERN.findall(content)
            for language, _ in code_matches:
                if language and language.strip():
                    keywords.append(language.strip().lower())
            
        except Exception as e:
            self.logger.debug(f"Structure keyword extraction failed: {e}")
        
        return keywords
    
    def _generate_anchor(self, header_text: str) -> str:
        """
        Generate URL anchor from header text (GitHub-style).
        
        Args:
            header_text: Header text to convert
            
        Returns:
            URL-friendly anchor string
        """
        # Convert to lowercase and replace spaces with hyphens
        anchor = header_text.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)  # Remove non-alphanumeric chars
        anchor = re.sub(r'[\s_-]+', '-', anchor)  # Replace spaces/underscores with hyphens
        anchor = anchor.strip('-')  # Remove leading/trailing hyphens
        
        return anchor