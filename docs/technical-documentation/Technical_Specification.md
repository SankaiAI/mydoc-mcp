# mydocs-mcp API Reference

## Overview

The mydocs-mcp server provides three core MCP tools for document management through the Model Context Protocol. All tools follow MCP specification and communicate via JSON-RPC 2.0 over stdio transport.

## Table of Contents

1. [Core Tools](#core-tools)
   - [indexDocument](#indexdocument)
   - [searchDocuments](#searchdocuments)
   - [getDocument](#getdocument)
2. [Data Types](#data-types)
3. [Error Handling](#error-handling)
4. [Performance Guarantees](#performance-guarantees)
5. [Examples](#examples)

---

## Core Tools

### indexDocument

Indexes a document for searching, extracting metadata and content for fast retrieval.

#### Request

```json
{
  "tool": "indexDocument",
  "arguments": {
    "file_path": "/path/to/document.md",
    "force": false,
    "extract_metadata": true
  }
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_path` | string | Yes | - | Absolute path to the document to index |
| `force` | boolean | No | false | Force reindexing even if document unchanged |
| `extract_metadata` | boolean | No | true | Extract and store document metadata |

#### Response

```json
{
  "success": true,
  "document_id": "doc_a1b2c3d4e5f6",
  "indexed_at": "2025-09-04T15:30:00Z",
  "metadata": {
    "title": "Document Title",
    "file_type": "markdown",
    "file_size": 4096,
    "word_count": 500,
    "created_at": "2025-09-01T10:00:00Z",
    "modified_at": "2025-09-04T14:00:00Z"
  },
  "performance": {
    "parse_time_ms": 15,
    "index_time_ms": 30,
    "total_time_ms": 45
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether indexing succeeded |
| `document_id` | string | Unique identifier for the document |
| `indexed_at` | string | ISO 8601 timestamp of indexing |
| `metadata` | object | Extracted document metadata |
| `performance` | object | Performance metrics for the operation |

#### Error Responses

```json
{
  "success": false,
  "error": "File not found",
  "error_code": "FILE_NOT_FOUND",
  "file_path": "/path/to/missing.md"
}
```

---

### searchDocuments

Searches indexed documents using keyword matching and relevance ranking.

#### Request

```json
{
  "tool": "searchDocuments",
  "arguments": {
    "query": "API design patterns",
    "file_type": "markdown",
    "limit": 10,
    "offset": 0,
    "include_content": false,
    "min_score": 0.5
  }
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query string |
| `file_type` | string | No | null | Filter by file type ("markdown", "text") |
| `limit` | integer | No | 20 | Maximum number of results |
| `offset` | integer | No | 0 | Pagination offset |
| `include_content` | boolean | No | false | Include full content in results |
| `min_score` | float | No | 0.0 | Minimum relevance score (0.0-1.0) |

#### Response

```json
{
  "results": [
    {
      "id": "doc_a1b2c3d4e5f6",
      "title": "API Design Best Practices",
      "file_path": "/docs/api-design.md",
      "relevance_score": 0.95,
      "snippet": "...REST API design patterns focus on resource-based URLs...",
      "highlights": [
        {"text": "API", "positions": [10, 45, 78]},
        {"text": "design", "positions": [14, 49, 82]},
        {"text": "patterns", "positions": [21, 56, 89]}
      ],
      "metadata": {
        "file_type": "markdown",
        "word_count": 1500,
        "modified_at": "2025-09-03T12:00:00Z"
      }
    }
  ],
  "total_results": 25,
  "returned_results": 10,
  "search_time_ms": 67,
  "query_info": {
    "original_query": "API design patterns",
    "processed_query": "api design pattern",
    "search_type": "keyword"
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `results` | array | Array of matching documents |
| `total_results` | integer | Total number of matches found |
| `returned_results` | integer | Number of results in this response |
| `search_time_ms` | integer | Search execution time in milliseconds |
| `query_info` | object | Information about query processing |

#### Result Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Document identifier |
| `title` | string | Document title or filename |
| `file_path` | string | Full path to the document |
| `relevance_score` | float | Relevance score (0.0-1.0) |
| `snippet` | string | Content excerpt with query terms |
| `highlights` | array | Term positions for highlighting |
| `metadata` | object | Document metadata |

---

### getDocument

Retrieves a specific document by ID or file path.

#### Request

```json
{
  "tool": "getDocument",
  "arguments": {
    "document_id": "doc_a1b2c3d4e5f6",
    "file_path": "/docs/api-design.md",
    "format": "markdown",
    "include_metadata": true,
    "max_content_length": 50000
  }
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `document_id` | string | No* | - | Document ID to retrieve |
| `file_path` | string | No* | - | File path to retrieve |
| `format` | string | No | "json" | Output format ("json", "markdown", "text") |
| `include_metadata` | boolean | No | true | Include document metadata |
| `max_content_length` | integer | No | 100000 | Maximum content length to return |

*Note: Either `document_id` or `file_path` must be provided

#### Response

```json
{
  "success": true,
  "document_id": "doc_a1b2c3d4e5f6",
  "content": "# API Design Best Practices\n\nThis document covers...",
  "format": "markdown",
  "metadata": {
    "title": "API Design Best Practices",
    "file_path": "/docs/api-design.md",
    "file_type": "markdown",
    "file_size": 15234,
    "word_count": 1500,
    "created_at": "2025-09-01T10:00:00Z",
    "modified_at": "2025-09-03T12:00:00Z",
    "indexed_at": "2025-09-04T08:00:00Z"
  },
  "truncated": false,
  "retrieval_time_ms": 23
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether retrieval succeeded |
| `document_id` | string | Document identifier |
| `content` | string | Document content in requested format |
| `format` | string | Format of the content |
| `metadata` | object | Document metadata (if requested) |
| `truncated` | boolean | Whether content was truncated |
| `retrieval_time_ms` | integer | Retrieval time in milliseconds |

---

## Data Types

### Document Metadata

Standard metadata object returned by various tools:

```typescript
interface DocumentMetadata {
  title: string;              // Document title or filename
  file_path: string;          // Absolute path to file
  file_type: string;          // "markdown" | "text"
  file_size: number;          // Size in bytes
  word_count: number;         // Number of words
  created_at: string;         // ISO 8601 timestamp
  modified_at: string;        // ISO 8601 timestamp
  indexed_at?: string;        // ISO 8601 timestamp (when indexed)
  
  // Optional extracted metadata
  description?: string;       // Document description
  tags?: string[];           // Extracted tags
  links?: string[];          // Extracted links
  headings?: string[];       // Document headings (markdown)
}
```

### Performance Metrics

Performance information included in responses:

```typescript
interface PerformanceMetrics {
  parse_time_ms?: number;     // Time to parse document
  index_time_ms?: number;     // Time to index in database
  search_time_ms?: number;    // Time to execute search
  retrieval_time_ms?: number; // Time to retrieve document
  total_time_ms: number;      // Total operation time
}
```

---

## Error Handling

### Error Response Format

All errors follow this standard format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "details": {
    "additional": "context-specific information"
  }
}
```

### Common Error Codes

| Code | Description | HTTP Equivalent |
|------|-------------|-----------------|
| `FILE_NOT_FOUND` | Document file doesn't exist | 404 |
| `PERMISSION_DENIED` | No read access to file | 403 |
| `INVALID_PATH` | Invalid file path format | 400 |
| `UNSUPPORTED_TYPE` | File type not supported | 415 |
| `DATABASE_ERROR` | Database operation failed | 500 |
| `PARSE_ERROR` | Failed to parse document | 422 |
| `QUERY_ERROR` | Invalid search query | 400 |
| `NOT_INDEXED` | Document not in index | 404 |
| `TIMEOUT` | Operation timed out | 408 |

### Error Examples

```json
// File not found
{
  "success": false,
  "error": "File not found: /docs/missing.md",
  "error_code": "FILE_NOT_FOUND",
  "details": {
    "file_path": "/docs/missing.md",
    "checked_at": "2025-09-04T15:30:00Z"
  }
}

// Invalid query
{
  "success": false,
  "error": "Search query cannot be empty",
  "error_code": "QUERY_ERROR",
  "details": {
    "query": "",
    "min_length": 1
  }
}
```

---

## Performance Guarantees

All operations are designed to complete within 200ms under normal conditions:

| Operation | P50 | P95 | P99 | Max |
|-----------|-----|-----|-----|-----|
| indexDocument | 45ms | 120ms | 180ms | 200ms |
| searchDocuments | 67ms | 150ms | 190ms | 200ms |
| getDocument | 23ms | 80ms | 150ms | 200ms |

### Performance Factors

- **Document Size**: Larger documents take longer to parse and index
- **Search Complexity**: More terms and filters increase search time
- **Database Size**: Performance degrades slightly with millions of documents
- **Concurrent Operations**: Server handles up to 100 concurrent requests

---

## Examples

### Example 1: Index a New Document

```python
# Request
request = {
    "tool": "indexDocument",
    "arguments": {
        "file_path": "/home/user/docs/project-plan.md"
    }
}

# Response
response = {
    "success": True,
    "document_id": "doc_xyz789",
    "indexed_at": "2025-09-04T16:00:00Z",
    "metadata": {
        "title": "Q4 Project Plan",
        "file_type": "markdown",
        "word_count": 2500
    }
}
```

### Example 2: Search with Filters

```python
# Request
request = {
    "tool": "searchDocuments",
    "arguments": {
        "query": "authentication OAuth",
        "file_type": "markdown",
        "limit": 5,
        "min_score": 0.7
    }
}

# Response
response = {
    "results": [
        {
            "id": "doc_abc123",
            "title": "OAuth Implementation Guide",
            "relevance_score": 0.92,
            "snippet": "...OAuth 2.0 authentication flow..."
        },
        {
            "id": "doc_def456",
            "title": "API Authentication",
            "relevance_score": 0.78,
            "snippet": "...various authentication methods including OAuth..."
        }
    ],
    "total_results": 2,
    "search_time_ms": 54
}
```

### Example 3: Retrieve Document as Markdown

```python
# Request
request = {
    "tool": "getDocument",
    "arguments": {
        "document_id": "doc_abc123",
        "format": "markdown"
    }
}

# Response
response = {
    "success": True,
    "document_id": "doc_abc123",
    "content": "# OAuth Implementation Guide\n\n## Overview\n...",
    "format": "markdown",
    "metadata": {
        "title": "OAuth Implementation Guide",
        "word_count": 3200,
        "modified_at": "2025-09-03T14:30:00Z"
    }
}
```

### Example 4: Handle Errors Gracefully

```python
# Request for non-existent document
request = {
    "tool": "getDocument",
    "arguments": {
        "document_id": "doc_nonexistent"
    }
}

# Error response
response = {
    "success": False,
    "error": "Document not found in index",
    "error_code": "NOT_INDEXED",
    "details": {
        "document_id": "doc_nonexistent",
        "suggestion": "Use searchDocuments to find available documents"
    }
}
```

---

## Integration with Claude Code

### Configuration

Add to Claude Code's MCP settings:

```json
{
  "mcpServers": {
    "mydocs": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "/path/to/mydocs-mcp",
      "env": {
        "DOCUMENT_ROOT": "/home/user/Documents"
      }
    }
  }
}
```

### Usage in Claude Code

```python
# Natural language commands Claude Code understands:

"Index all markdown files in /project/docs"
# → Triggers indexDocument for each .md file

"Search for documents about authentication"
# → Triggers searchDocuments with query "authentication"

"Get the document about API design"
# → Triggers searchDocuments, then getDocument for best match

"Show me the file /project/README.md"
# → Triggers getDocument with file_path
```

---

## Best Practices

### Indexing
- Index documents during off-peak hours for large collections
- Use `force=false` to avoid unnecessary reindexing
- Enable file watcher for automatic index updates

### Searching
- Use specific keywords for better results
- Apply filters to narrow down results
- Set appropriate `min_score` to filter low-relevance matches

### Performance
- Limit search results to what you need (`limit` parameter)
- Use pagination (`offset`) for large result sets
- Enable caching for frequently accessed documents

### Error Handling
- Always check `success` field in responses
- Log error codes for debugging
- Implement retry logic for transient errors

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-09-04 | Initial release with three core tools |
| 0.9.0 | 2025-09-03 | Beta release for testing |

---

*Last Updated: September 4, 2025*