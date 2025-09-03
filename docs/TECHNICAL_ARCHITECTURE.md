# mydocs-mcp - Technical Architecture Document (TAD)

## Document Information

**Document Type**: Technical Architecture Document  
**Project**: mydocs-mcp - Personal Document Intelligence MCP Server  
**Version**: 1.0  
**Created**: September 3, 2025  
**Timeline**: 3-Day Development Sprint (72 hours)  
**Status**: Active Development  

---

## 1. Executive Summary

### 1.1 Architecture Overview

mydocs-mcp is a Model Context Protocol (MCP) compliant server designed to provide AI agents with intelligent access to users' personal document history. The architecture follows a modular, privacy-first approach with local-only processing capabilities, enabling secure document intelligence without external dependencies.

### 1.2 Key Architectural Principles

- **Privacy-First**: Local-only processing by default, no cloud dependencies
- **MCP Compliance**: Full adherence to Model Context Protocol specifications
- **Modular Design**: Extensible plugin architecture for future enhancements
- **Performance Optimized**: Sub-200ms response times for typical queries
- **Development Focused**: 3-day sprint delivery with MVP functionality

---

## 2. Technology Stack Decisions

### 2.1 Core Technology Stack

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Runtime Language** | Python | 3.11+ | Excellent MCP ecosystem support, rapid development capabilities, rich AI/ML libraries |
| **MCP Framework** | `mcp` Python Package | 1.0.0+ | Official MCP implementation, comprehensive tool support, active development |
| **Process Communication** | STDIO Transport | Native | Direct integration with Claude Code, minimal setup complexity, local-only security |
| **Primary Database** | SQLite | 3.42+ | Zero-configuration, local storage, ACID compliance, perfect for MVP |
| **Document Processing** | Python Built-ins | 3.11+ | Native text processing, markdown support, no external dependencies |
| **Development Server** | asyncio | 3.11+ | Native async support, high concurrency, MCP compatibility |

### 2.2 Supporting Infrastructure

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Containerization** | Docker | 24.0+ | Consistent deployment, environment isolation, easy distribution |
| **Package Management** | pip + pyproject.toml | Latest | Python standard, dependency management, development workflow |
| **Configuration** | YAML + Environment Variables | Native | Human-readable, environment-specific settings, secure secrets |
| **Logging** | Python logging | 3.11+ | Native implementation, structured logging, performance optimized |

### 2.3 Future-Ready Technologies (Post-MVP)

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Vector Database** | ChromaDB | 0.4+ | Semantic search capabilities |
| **Embeddings** | OpenAI Ada-002 | Latest | Text similarity matching |
| **Production Database** | PostgreSQL | 15+ | Scalable multi-user support |
| **HTTP Transport** | FastAPI + SSE | 0.104+ | Remote deployment capabilities |
| **Authentication** | OAuth2 | Latest | Secure remote access |

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AI AGENTS                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │   Claude Code   │  │  Other MCP      │  │   Custom     │  │
│  │                 │  │  Clients        │  │   Agents     │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol (STDIO)
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    MCP SERVER LAYER                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │   Tool Registry │  │   Transport     │  │  Middleware  │  │
│  │                 │  │   (STDIO)       │  │   (Logging)  │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ Internal API
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     TOOLS LAYER                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │ searchDocuments │  │   getDocument   │  │ indexDocument│  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ Business Logic
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   CORE BUSINESS LAYER                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │ Document        │  │  Search         │  │   Pattern    │  │
│  │ Manager         │  │  Engine         │  │   Analyzer   │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ Data Access
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    STORAGE LAYER                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │   SQLite DB     │  │  File System    │  │    Cache     │  │
│  │  (Metadata)     │  │  (Documents)    │  │   Manager    │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Component Responsibilities

#### MCP Server Layer
- **Tool Registry**: Dynamic registration and management of available tools
- **Transport Handler**: STDIO communication with AI agents
- **Middleware**: Cross-cutting concerns (logging, error handling)

#### Tools Layer
- **searchDocuments**: Keyword-based document search with filtering
- **getDocument**: Document content retrieval with metadata
- **indexDocument**: New document addition to searchable index

#### Core Business Layer
- **Document Manager**: Document lifecycle, versioning, metadata management
- **Search Engine**: Text-based search with relevance ranking
- **Pattern Analyzer**: Document structure analysis (future enhancement)

#### Storage Layer
- **SQLite Database**: Document metadata, search indexes, configuration
- **File System**: Raw document content storage
- **Cache Manager**: Performance optimization for frequent queries

---

## 4. Detailed Component Specifications

### 4.1 MCP Server Implementation

#### Technology Decision: Python MCP Package
```python
# Core server implementation using official MCP library
from mcp import Server
from mcp.server.stdio import stdio_server

# Rationale: Official implementation ensures protocol compliance
# Version: 1.0.0+ for stability and feature completeness
```

**Key Features**:
- Full MCP protocol compliance
- STDIO transport for local security
- Async request handling
- Structured error responses
- Tool schema validation

**Performance Specifications**:
- Tool call response time: < 200ms average
- Concurrent connections: 10+ simultaneous
- Memory footprint: < 256MB for MVP dataset
- Startup time: < 5 seconds

### 4.2 Document Storage System

#### Primary Storage: SQLite 3.42+

```sql
-- Core schema for MVP implementation
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    title TEXT,
    content_hash TEXT,
    file_type TEXT,
    file_size INTEGER,
    created_date DATETIME,
    modified_date DATETIME,
    indexed_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE document_metadata (
    document_id INTEGER,
    key TEXT,
    value TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    PRIMARY KEY (document_id, key)
);

CREATE INDEX idx_documents_type ON documents(file_type);
CREATE INDEX idx_documents_modified ON documents(modified_date);
CREATE INDEX idx_metadata_key ON document_metadata(key);
```

**Rationale for SQLite**:
- Zero configuration setup
- ACID compliance for data integrity
- Local storage aligns with privacy-first architecture
- Sufficient performance for MVP requirements (10K+ documents)
- Built-in full-text search capabilities via FTS5

#### File System Organization
```
data/
├── documents/          # Indexed document content
├── indexes/           # SQLite database files
├── cache/            # Temporary cache files
└── backups/          # Automated backups (future)
```

### 4.3 Search Engine Implementation

#### MVP Search Capabilities
```python
class SearchEngine:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def keyword_search(self, query: str, filters: dict = None) -> List[Document]:
        """
        Text-based search using SQLite FTS5
        Performance target: <200ms for typical queries
        """
        pass
    
    def filter_documents(self, type_filter: str = None, 
                        date_range: tuple = None) -> List[Document]:
        """
        Metadata-based filtering
        Supports: file type, date ranges, custom tags
        """
        pass
```

**Search Algorithm**:
1. **Keyword Matching**: SQLite FTS5 for full-text search
2. **Relevance Scoring**: TF-IDF based ranking
3. **Metadata Filtering**: Type, date, size-based filters
4. **Result Optimization**: Limit + offset for pagination

**Future Enhancements** (Post-MVP):
- Semantic search using vector embeddings
- Similarity-based document matching
- Context-aware recommendations

### 4.4 MCP Tools Specification

#### Core Tool: searchDocuments
```json
{
  "name": "searchDocuments",
  "description": "Search personal documents using keyword search with filtering",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query text"
      },
      "type_filter": {
        "type": "string",
        "enum": ["markdown", "text", "all"],
        "description": "Filter by document type"
      },
      "limit": {
        "type": "number",
        "default": 10,
        "maximum": 50,
        "description": "Maximum number of results"
      }
    },
    "required": ["query"]
  }
}
```

#### Core Tool: getDocument
```json
{
  "name": "getDocument",
  "description": "Retrieve full content and metadata of a specific document",
  "inputSchema": {
    "type": "object",
    "properties": {
      "document_id": {
        "type": "string",
        "description": "Unique document identifier"
      },
      "include_metadata": {
        "type": "boolean",
        "default": true,
        "description": "Include document metadata in response"
      }
    },
    "required": ["document_id"]
  }
}
```

#### Core Tool: indexDocument
```json
{
  "name": "indexDocument",
  "description": "Add new document to searchable index",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "Path to document file"
      },
      "tags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Optional tags for categorization"
      }
    },
    "required": ["file_path"]
  }
}
```

---

## 5. Development Environment Configuration

### 5.1 Required Development Dependencies

#### Core Dependencies (requirements.txt)
```txt
# MCP Framework
mcp>=1.0.0

# Database
sqlite3  # Built into Python 3.11+

# Development Tools
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.5.0

# Documentation
mkdocs>=1.5.0
mkdocs-material>=9.0.0
```

#### Development Environment Setup
```bash
# Python version requirement
python --version  # Must be 3.11+

# Virtual environment setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Development mode installation
pip install -e .
```

### 5.2 Docker Configuration

#### Multi-Stage Dockerfile
```dockerfile
# Development stage
FROM python:3.11-slim as development
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "src.main"]

# Production stage (future)
FROM python:3.11-slim as production
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
USER nobody
CMD ["python", "-m", "src.main"]
```

#### Docker Compose Configuration
```yaml
version: '3.8'
services:
  mydocs-mcp:
    build:
      context: .
      target: development
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - MCP_TRANSPORT=stdio
      - DATABASE_URL=sqlite:///data/documents.db
    stdin_open: true
    tty: true
```

### 5.3 Configuration Management

#### Environment Variables
```bash
# Core Configuration
MCP_TRANSPORT=stdio                    # Transport protocol
DATABASE_URL=sqlite:///data/documents.db  # Database connection
LOG_LEVEL=INFO                         # Logging verbosity
MAX_DOCUMENT_SIZE=10MB                 # File size limit

# Performance Tuning
CACHE_TTL_SECONDS=3600                # Cache lifetime
MAX_CONCURRENT_CONNECTIONS=10         # Connection limit
SEARCH_TIMEOUT_SECONDS=30            # Query timeout
```

#### Configuration File (config/server_config.yaml)
```yaml
server:
  transport: stdio
  max_connections: 10
  timeout: 30

storage:
  database_url: "sqlite:///data/documents.db"
  document_root: "./data/documents"
  cache_directory: "./data/cache"

search:
  max_results: 50
  default_limit: 10
  enable_caching: true

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "./data/logs/mydocs-mcp.log"
```

---

## 6. Security Architecture

### 6.1 Privacy-First Design

#### Local-Only Processing
- **No Network Communication**: All processing occurs locally
- **No Telemetry**: Zero data collection or external reporting
- **User Data Control**: Complete user ownership of all documents
- **Transparent Operations**: All data processing is auditable

#### File System Security
```python
# Secure file access patterns
import os
from pathlib import Path

def validate_document_path(path: str) -> bool:
    """Ensure document paths are within allowed directories"""
    resolved_path = Path(path).resolve()
    allowed_root = Path("./data/documents").resolve()
    
    try:
        resolved_path.relative_to(allowed_root)
        return True
    except ValueError:
        return False  # Path outside allowed directory
```

### 6.2 Data Protection

#### Input Validation
- **Path Traversal Protection**: Restrict file access to designated directories
- **File Type Validation**: Only process approved document formats
- **Size Limits**: Prevent resource exhaustion from large files
- **Content Sanitization**: Basic malformed content handling

#### Error Handling
- **No Sensitive Information**: Error messages exclude file contents
- **Graceful Degradation**: System continues operating despite individual failures
- **Audit Logging**: All operations logged for debugging and security review

### 6.3 Future Security Enhancements (Post-MVP)

#### Encryption at Rest
- **Document Encryption**: AES-256 encryption for sensitive documents
- **Key Management**: Secure key derivation and storage
- **Selective Encryption**: User-configurable encryption policies

#### Authentication System
- **OAuth2 Integration**: Industry-standard authentication
- **API Key Management**: Secure API access for remote deployments
- **Role-Based Access**: Granular permissions for multi-user scenarios

---

## 7. Performance Architecture

### 7.1 MVP Performance Targets

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| **Tool Call Response** | < 200ms average | Built-in timing middleware |
| **Document Indexing** | > 10 docs/second | Batch processing benchmarks |
| **Memory Usage** | < 256MB for 10K docs | Runtime memory monitoring |
| **Search Accuracy** | > 80% relevance | Manual testing with sample queries |
| **Container Startup** | < 5 seconds | Docker startup timing |

### 7.2 Performance Optimization Strategies

#### Database Optimization
```sql
-- Optimized indexes for common query patterns
CREATE INDEX idx_documents_compound ON documents(file_type, modified_date);
CREATE INDEX idx_fts_documents ON documents USING fts5(title, content);

-- Query optimization
PRAGMA journal_mode=WAL;  -- Better concurrent access
PRAGMA synchronous=NORMAL;  -- Balance safety/performance
PRAGMA cache_size=10000;  -- Larger memory cache
```

#### Caching Strategy
- **Query Result Caching**: Cache search results for repeated queries
- **Document Content Caching**: Keep frequently accessed documents in memory
- **Metadata Caching**: Cache document metadata for faster filtering
- **TTL-Based Expiration**: Automatic cache invalidation

#### Async Processing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncDocumentProcessor:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_document(self, file_path: str):
        """Non-blocking document processing"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._sync_process_document, 
            file_path
        )
```

---

## 8. Deployment Architecture

### 8.1 MVP Deployment Strategy

#### Local Development Deployment
```bash
# Direct Python execution
python -m src.main

# Development server with auto-reload
python -m src.main --dev --reload

# Docker development
docker-compose -f docker/docker-compose.dev.yml up
```

#### Production-Ready Deployment (Future)
```bash
# Production container
docker build -t mydocs-mcp:latest .
docker run -d \
  --name mydocs-mcp \
  -v /path/to/documents:/app/data \
  -e MCP_TRANSPORT=http_sse \
  -p 8000:8000 \
  mydocs-mcp:latest
```

### 8.2 Container Architecture

#### Resource Requirements
- **CPU**: 1 core minimum, 2 cores recommended
- **Memory**: 512MB minimum, 1GB recommended
- **Storage**: 100MB application + user documents
- **Network**: Local-only for MVP, HTTP/8000 for future

#### Volume Mounts
- `/app/data`: Persistent document storage
- `/app/config`: Configuration files
- `/app/logs`: Application logs (future)

### 8.3 Scaling Considerations (Post-MVP)

#### Horizontal Scaling
- **Load Balancing**: Multiple server instances
- **Database Replication**: Read replicas for search queries
- **Shared Storage**: Distributed file systems

#### Performance Monitoring
- **Metrics Collection**: Prometheus-compatible metrics
- **Health Checks**: Kubernetes/Docker health endpoints
- **Performance Dashboards**: Grafana visualization

---

## 9. Development Workflow

### 9.1 3-Day Sprint Timeline

#### Day 1 (Foundation - 0-24 hours)
```
Hours 0-8:   Project setup, MCP server skeleton
Hours 8-16:  Database schema, document indexing system
Hours 16-24: Basic MCP tools, initial testing
```

#### Day 2 (Core Features - 24-48 hours)
```
Hours 24-32: Search engine implementation
Hours 32-40: Docker configuration, dev environment
Hours 40-48: Integration testing, bug fixes
```

#### Day 3 (Demo & Delivery - 48-72 hours)
```
Hours 48-56: Demo preparation, sample documents
Hours 56-64: Documentation, guides, README
Hours 64-72: Final testing, deployment package
```

### 9.2 Quality Assurance Process

#### Testing Strategy
- **Unit Tests**: Individual component testing (>80% coverage)
- **Integration Tests**: MCP protocol compliance testing
- **End-to-End Tests**: Full workflow demonstration
- **Performance Tests**: Response time and resource usage validation

#### Code Quality Standards
```python
# Type hints for all public functions
def search_documents(query: str, limit: int = 10) -> List[Document]:
    """Search documents with type safety"""
    pass

# Comprehensive error handling
try:
    result = process_document(file_path)
except DocumentProcessingError as e:
    logger.error(f"Failed to process {file_path}: {e}")
    return {"error": "Document processing failed"}
```

### 9.3 Documentation Requirements

#### Technical Documentation
- **README.md**: Installation, setup, basic usage
- **API_REFERENCE.md**: MCP tool specifications with examples
- **DEPLOYMENT.md**: Docker deployment instructions
- **TROUBLESHOOTING.md**: Common issues and solutions

#### Code Documentation
- Docstrings for all public functions and classes
- Inline comments for complex algorithms
- Type hints for function signatures
- Configuration option documentation

---

## 10. Risk Mitigation & Contingencies

### 10.1 Technical Risk Mitigation

#### MCP Protocol Complexity
- **Risk**: Integration challenges with MCP specification
- **Mitigation**: Use official MCP Python library, extensive testing
- **Contingency**: Simplify tool interfaces if needed

#### Performance Requirements
- **Risk**: Response times exceed 200ms target
- **Mitigation**: Database indexing, caching strategies
- **Contingency**: Reduce feature scope, optimize critical path

#### Time Constraints
- **Risk**: 72-hour timeline is insufficient
- **Mitigation**: Focus on core MVP features only
- **Contingency**: Defer advanced features to future releases

### 10.2 Operational Risk Mitigation

#### Data Corruption
- **Risk**: Document index corruption
- **Mitigation**: Database transactions, error handling
- **Contingency**: Automated index rebuilding capability

#### Resource Exhaustion
- **Risk**: Memory or disk space issues
- **Mitigation**: Resource limits, monitoring
- **Contingency**: Graceful degradation, cleanup processes

---

## 11. Future Architecture Evolution

### 11.1 Phase 2 Enhancements (Post-MVP)

#### Semantic Search Capabilities
```python
# Vector embedding integration
from sentence_transformers import SentenceTransformer
import chromadb

class SemanticSearchEngine:
    def __init__(self):
        self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_db = chromadb.Client()
    
    async def semantic_search(self, query: str) -> List[Document]:
        """AI-powered document similarity search"""
        pass
```

#### Template Generation System
```python
class TemplateGenerator:
    def extract_patterns(self, documents: List[Document]) -> Dict:
        """Extract common patterns from document set"""
        pass
    
    def generate_template(self, pattern: Dict, context: str) -> str:
        """Generate new document from extracted patterns"""
        pass
```

### 11.2 Phase 3 Architecture (Advanced Features)

#### Multi-User Support
- **Database Migration**: SQLite to PostgreSQL
- **Authentication**: OAuth2 integration
- **API Gateway**: HTTP+SSE transport implementation
- **Permissions**: Role-based access control

#### Enterprise Features
- **Audit Logging**: Comprehensive operation tracking
- **Backup Systems**: Automated data protection
- **Monitoring**: Prometheus metrics and alerting
- **High Availability**: Load balancing and failover

---

## 12. Conclusion

### 12.1 Architecture Summary

The mydocs-mcp technical architecture provides a solid foundation for delivering a working MVP within the 3-day sprint timeline while maintaining extensibility for future enhancements. Key architectural strengths include:

- **Privacy-First Design**: Local-only processing ensures complete user data control
- **MCP Compliance**: Official protocol implementation guarantees compatibility
- **Performance Optimized**: Sub-200ms response times through efficient design
- **Development Focused**: Streamlined stack enables rapid feature delivery
- **Future-Ready**: Modular architecture supports advanced features

### 12.2 Technical Decision Summary

| Decision Area | MVP Choice | Post-MVP Evolution | Rationale |
|---------------|------------|-------------------|-----------|
| **Language** | Python 3.11+ | Maintained | Rapid development, MCP ecosystem |
| **Transport** | STDIO | + HTTP+SSE | Local security, then remote access |
| **Database** | SQLite | + PostgreSQL | Zero config, then scalability |
| **Search** | Keyword/FTS5 | + Vector embeddings | MVP simplicity, then AI power |
| **Deployment** | Local/Docker | + Kubernetes | Development focus, then production |

### 12.3 Success Metrics Alignment

The technical architecture directly supports the project's success criteria:

- **Functional MCP Server**: Official library ensures protocol compliance
- **Document Search**: SQLite FTS5 provides reliable text search
- **Performance Targets**: Async design meets response time requirements
- **Docker Deployment**: Container-first approach simplifies distribution
- **Demo Ready**: Comprehensive tooling supports demonstration workflows

This architecture document serves as the definitive technical reference for the 3-day development sprint, providing clear guidance for implementation decisions while maintaining flexibility for future evolution.

---

**Document Approval**:  
Technical Architecture Lead: _________________ Date: _________  
Project Sponsor: _________________ Date: _________  
Quality Assurance: _________________ Date: _________

**Version Control**:  
- Version 1.0: Initial architecture definition (September 3, 2025)
- Next Review: End of Day 1 implementation checkpoint