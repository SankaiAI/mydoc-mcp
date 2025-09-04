"""
searchDocuments MCP Tool Implementation

This module implements the searchDocuments tool for mydocs-mcp, which provides
comprehensive keyword-based document search with relevance ranking, filtering,
and result optimization. The tool integrates with the search queries layer
and provides sub-200ms response times for typical queries.
"""

import re
import hashlib
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from .base import BaseMCPTool, ToolResult, ToolExecutionError
from ..database.database_manager import DocumentManager
from ..database.models import SearchCache


class SearchDocumentsTool(BaseMCPTool):
    """
    MCP Tool for searching documents with keyword matching.
    
    This tool provides comprehensive document search capabilities including:
    - Keyword-based text search with relevance ranking
    - File type filtering (.md, .txt)
    - Result sorting (relevance, date, name)
    - Query result caching for performance
    - Content snippet generation with keyword highlighting
    - Search performance metrics and optimization
    
    Performance targets:
    - Sub-200ms response time for typical queries
    - Support for complex queries with multiple keywords
    - Efficient result ranking and filtering
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize searchDocuments tool with search cache."""
        super().__init__(*args, **kwargs)
        self.search_cache_ttl_minutes = 30  # Cache search results for 30 minutes
        self.max_snippet_length = 200  # Maximum snippet length for results
    
    def get_tool_name(self) -> str:
        """Return the MCP tool name."""
        return "searchDocuments"
    
    def get_tool_description(self) -> str:
        """Return the MCP tool description."""
        return (
            "Search indexed documents using keyword matching with relevance ranking. "
            "Supports file type filtering, result sorting, and returns document "
            "metadata with content snippets. Optimized for sub-200ms response times."
        )
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query with keywords to match against document content",
                    "minLength": 1,
                    "maxLength": 500
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                },
                "file_type": {
                    "type": "string",
                    "description": "Filter results by file type",
                    "enum": [".md", ".txt", "markdown", "text"],
                    "default": None
                },
                "sort_by": {
                    "type": "string",
                    "description": "Sort order for results",
                    "enum": ["relevance", "date", "name"],
                    "default": "relevance"
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    
    async def _execute_tool(self, validated_params: Dict[str, Any]) -> ToolResult:
        """
        Execute the searchDocuments tool.
        
        Args:
            validated_params: Validated tool parameters
            
        Returns:
            ToolResult with search results
        """
        query = validated_params["query"]
        limit = validated_params.get("limit", 10)
        file_type = validated_params.get("file_type")
        sort_by = validated_params.get("sort_by", "relevance")
        
        search_start_time = time.time()
        
        try:
            # Normalize and validate query
            normalized_query = self._normalize_query(query)
            if not normalized_query:
                return ToolResult.error_result(
                    "Query contains no valid search terms"
                )
            
            # Check search cache first
            cache_key = self._generate_cache_key(normalized_query, limit, file_type, sort_by)
            cached_result = await self._get_cached_search(cache_key)
            
            if cached_result:
                search_time_ms = (time.time() - search_start_time) * 1000
                self.logger.debug(f"Cache hit for search query: {query}")
                
                # Add timing information to cached result
                cached_result["search_time_ms"] = search_time_ms
                cached_result["from_cache"] = True
                
                return ToolResult.success_result(
                    data=cached_result,
                    metadata={
                        "tool_version": "1.0",
                        "search_method": "cached",
                        "cache_hit": True
                    }
                )
            
            # Normalize file type filter
            file_type_filter = self._normalize_file_type(file_type) if file_type else None
            
            # Execute search query
            search_results = await self.database_manager.search_queries.search_documents(
                query=normalized_query,
                limit=limit * 2,  # Get more results for better ranking
                offset=0,
                file_type_filter=file_type_filter
            )
            
            # Apply additional ranking and filtering
            ranked_results = await self._rank_and_filter_results(
                search_results, normalized_query, sort_by
            )
            
            # Limit results to requested amount
            final_results = ranked_results[:limit]
            
            # Generate result data
            formatted_results = await self._format_search_results(
                final_results, normalized_query
            )
            
            search_time_ms = (time.time() - search_start_time) * 1000
            
            # Prepare response data
            response_data = {
                "results": formatted_results,
                "total_found": len(search_results),
                "returned_count": len(formatted_results),
                "search_time_ms": round(search_time_ms, 2),
                "query_processed": normalized_query,
                "from_cache": False
            }
            
            # Add search metadata
            if file_type_filter:
                response_data["file_type_filter"] = file_type_filter
            
            if sort_by != "relevance":
                response_data["sort_by"] = sort_by
            
            # Cache the results for future queries
            await self._cache_search_results(cache_key, response_data, normalized_query)
            
            # Log search performance
            self.logger.info(
                f"Search completed: query='{query}', results={len(formatted_results)}, "
                f"time={search_time_ms:.2f}ms"
            )
            
            return ToolResult.success_result(
                data=response_data,
                metadata={
                    "tool_version": "1.0",
                    "search_method": "database",
                    "performance_target_met": search_time_ms < 200.0,
                    "cache_hit": False
                }
            )
            
        except Exception as e:
            search_time_ms = (time.time() - search_start_time) * 1000
            self.logger.error(f"searchDocuments tool execution failed: {e}", exc_info=True)
            
            return ToolResult.error_result(
                f"Search failed: {str(e)}",
                metadata={
                    "search_time_ms": round(search_time_ms, 2),
                    "query": query
                }
            )
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize search query for consistent processing.
        
        Args:
            query: Raw search query
            
        Returns:
            Normalized query string
        """
        # Remove extra whitespace and convert to lowercase
        normalized = re.sub(r'\s+', ' ', query.strip().lower())
        
        # Remove empty terms
        terms = [term for term in normalized.split() if len(term) > 0]
        
        # Remove very short terms (less than 2 characters) unless they're meaningful
        meaningful_short_terms = {'c', 'r', 'go', 'js', 'ai', 'ml', 'ui', 'ux'}
        filtered_terms = []
        
        for term in terms:
            if len(term) >= 2 or term in meaningful_short_terms:
                filtered_terms.append(term)
        
        return ' '.join(filtered_terms)
    
    def _normalize_file_type(self, file_type: str) -> str:
        """
        Normalize file type filter to database format (without dot).
        
        Args:
            file_type: Raw file type specification
            
        Returns:
            Normalized file extension (without dot)
        """
        file_type_mapping = {
            "md": "md",
            "markdown": "md",
            "txt": "txt",
            "text": "txt",
            ".md": "md",
            ".txt": "txt"
        }
        
        normalized = file_type.lower().strip()
        return file_type_mapping.get(normalized, normalized.lstrip('.'))
    
    def _generate_cache_key(
        self,
        query: str,
        limit: int,
        file_type: Optional[str],
        sort_by: str
    ) -> str:
        """
        Generate cache key for search query.
        
        Args:
            query: Normalized query string
            limit: Result limit
            file_type: File type filter
            sort_by: Sort order
            
        Returns:
            Cache key hash
        """
        cache_data = f"{query}|{limit}|{file_type or ''}|{sort_by}"
        return hashlib.md5(cache_data.encode('utf-8')).hexdigest()
    
    async def _get_cached_search(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached search results.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Cached search results or None
        """
        try:
            cached_entry = await self.database_manager.search_queries.get_search_cache(cache_key)
            
            if cached_entry and cached_entry.results:
                # Parse JSON results
                import json
                return json.loads(cached_entry.results)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to retrieve search cache: {e}")
            return None
    
    async def _cache_search_results(
        self,
        cache_key: str,
        results: Dict[str, Any],
        query: str
    ) -> None:
        """
        Cache search results for future queries.
        
        Args:
            cache_key: Cache key
            results: Search results to cache
            query: Original query
        """
        try:
            import json
            
            # Create cache entry
            cache_entry = SearchCache(
                query_hash=cache_key,
                query_text=query,
                results=json.dumps(results),
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=self.search_cache_ttl_minutes),
                hit_count=0
            )
            
            await self.database_manager.search_queries.create_search_cache(cache_entry)
            
        except Exception as e:
            self.logger.warning(f"Failed to cache search results: {e}")
    
    async def _rank_and_filter_results(
        self,
        search_results: List[Tuple[Any, float]],  # (Document, relevance_score)
        query: str,
        sort_by: str
    ) -> List[Tuple[Any, float]]:
        """
        Apply additional ranking and filtering to search results.
        
        Args:
            search_results: Raw search results from database
            query: Search query for relevance calculation
            sort_by: Sort order preference
            
        Returns:
            Ranked and filtered results
        """
        if not search_results:
            return []
        
        # Apply additional relevance scoring
        enhanced_results = []
        query_terms = query.lower().split()
        
        for document, base_score in search_results:
            # Calculate additional relevance factors
            title_score = self._calculate_title_relevance(document.file_name, query_terms)
            recency_score = self._calculate_recency_score(document.indexed_at)
            content_score = self._calculate_content_relevance(document.content, query_terms)
            
            # Combine scores (weighted average)
            final_score = (
                base_score * 0.4 +          # Database relevance score
                title_score * 0.3 +         # Title relevance
                content_score * 0.2 +       # Content relevance
                recency_score * 0.1         # Document recency
            )
            
            enhanced_results.append((document, final_score))
        
        # Sort results based on preference
        if sort_by == "relevance":
            enhanced_results.sort(key=lambda x: x[1], reverse=True)
        elif sort_by == "date":
            enhanced_results.sort(key=lambda x: x[0].indexed_at or datetime.min, reverse=True)
        elif sort_by == "name":
            enhanced_results.sort(key=lambda x: x[0].file_name.lower())
        
        return enhanced_results
    
    def _calculate_title_relevance(self, filename: str, query_terms: List[str]) -> float:
        """Calculate relevance score based on filename matches."""
        filename_lower = filename.lower()
        score = 0.0
        
        for term in query_terms:
            if term in filename_lower:
                score += 10.0  # High weight for filename matches
        
        return min(score, 30.0)  # Cap the score
    
    def _calculate_recency_score(self, indexed_at: Optional[datetime]) -> float:
        """Calculate relevance score based on document recency."""
        if not indexed_at:
            return 0.0
        
        days_old = (datetime.now() - indexed_at).days
        
        # Recent documents get higher scores
        if days_old <= 7:
            return 5.0
        elif days_old <= 30:
            return 3.0
        elif days_old <= 90:
            return 1.0
        else:
            return 0.5
    
    def _calculate_content_relevance(self, content: str, query_terms: List[str]) -> float:
        """Calculate relevance score based on content analysis."""
        if not content:
            return 0.0
        
        content_lower = content.lower()
        score = 0.0
        
        for term in query_terms:
            # Count occurrences in content
            occurrences = content_lower.count(term)
            score += min(occurrences * 0.5, 5.0)  # Cap per-term contribution
        
        return min(score, 15.0)  # Cap total content score
    
    async def _format_search_results(
        self,
        ranked_results: List[Tuple[Any, float]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Format search results for response.
        
        Args:
            ranked_results: Ranked search results
            query: Search query for snippet generation
            
        Returns:
            List of formatted result dictionaries
        """
        formatted_results = []
        query_terms = query.lower().split()
        
        for document, relevance_score in ranked_results:
            # Generate content snippet
            snippet = self._generate_content_snippet(document.content, query_terms)
            
            # Get document metadata
            metadata = await self.database_manager.metadata_queries.get_document_metadata(
                document.id
            )
            
            # Format result
            result = {
                "document_id": document.id,
                "file_path": document.file_path,
                "file_name": document.file_name,
                "file_type": document.file_type,
                "file_size_bytes": document.file_size,
                "relevance_score": round(relevance_score, 3),
                "indexed_at": document.indexed_at.isoformat() if document.indexed_at else None,
                "modified_at": document.modified_at.isoformat() if document.modified_at else None,
                "content_snippet": snippet,
                "metadata": metadata
            }
            
            formatted_results.append(result)
        
        return formatted_results
    
    def _generate_content_snippet(
        self,
        content: str,
        query_terms: List[str]
    ) -> str:
        """
        Generate content snippet with keyword highlighting.
        
        Args:
            content: Full document content
            query_terms: Search terms for highlighting
            
        Returns:
            Content snippet with highlighted terms
        """
        if not content:
            return ""
        
        content_lower = content.lower()
        
        # Find best position for snippet (around first keyword match)
        best_position = 0
        for term in query_terms:
            pos = content_lower.find(term)
            if pos >= 0:
                # Center snippet around the keyword
                start_pos = max(0, pos - self.max_snippet_length // 2)
                best_position = start_pos
                break
        
        # Extract snippet
        snippet_end = min(len(content), best_position + self.max_snippet_length)
        snippet = content[best_position:snippet_end]
        
        # Add ellipsis if truncated
        if best_position > 0:
            snippet = "..." + snippet
        if snippet_end < len(content):
            snippet = snippet + "..."
        
        # Highlight query terms (simple highlighting with markdown)
        for term in query_terms:
            if term:
                # Case-insensitive replacement with markdown bold
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                snippet = pattern.sub(f"**{term}**", snippet)
        
        return snippet.strip()
    
    async def get_search_statistics(self) -> Dict[str, Any]:
        """
        Get search performance statistics.
        
        Returns:
            Dictionary with search statistics
        """
        try:
            # Get document count by type
            total_docs = await self.database_manager.doc_queries.count_documents()
            md_docs = await self.database_manager.doc_queries.count_documents(".md")
            txt_docs = await self.database_manager.doc_queries.count_documents(".txt")
            
            return {
                "indexed_documents": {
                    "total": total_docs,
                    "markdown": md_docs,
                    "text": txt_docs
                },
                "tool_performance": self.get_tool_info()["performance"],
                "cache_ttl_minutes": self.search_cache_ttl_minutes,
                "max_snippet_length": self.max_snippet_length
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get search statistics: {e}")
            return {
                "error": str(e),
                "tool_performance": self.get_tool_info()["performance"]
            }
    
    async def clear_search_cache(self) -> Dict[str, Any]:
        """
        Clear expired search cache entries.
        
        Returns:
            Cache cleanup results
        """
        try:
            cleared_count = await self.database_manager.search_queries.cleanup_expired_cache()
            
            return {
                "success": True,
                "cleared_entries": cleared_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to clear search cache: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }