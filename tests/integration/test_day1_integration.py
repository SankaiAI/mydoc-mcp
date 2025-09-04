"""
Day 1 Integration Testing for mydocs-mcp

This module provides comprehensive integration testing for all components
implemented during Day 1 of the 3-day sprint. It validates MCP server
functionality, tool registration, complete workflows, performance, and error handling.
"""

import asyncio
import json
import os
import tempfile
import time
import traceback
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

import pytest
import sys
sys.path.append('.')
sys.path.append('src')

# Import mydocs-mcp components
from src.server import MyDocsMCPServer
from src.config import ServerConfig
from src.database.database_manager import DocumentManager, create_document_manager
from src.parsers.parser_factory import get_default_factory
from src.tools.registration import register_core_tools
from src.tool_registry import ToolRegistry


@dataclass
class TestDocument:
    """Test document data structure."""
    file_path: str
    content: str
    file_type: str
    expected_title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass 
class PerformanceMetric:
    """Performance measurement data structure."""
    operation: str
    duration_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    success: bool
    duration_ms: float
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class Day1IntegrationTester:
    """
    Comprehensive Day 1 integration testing suite.
    
    Tests all core functionality implemented during Day 1:
    - MCP server startup and shutdown
    - Tool registration and discovery
    - Complete document processing workflows
    - MCP protocol compliance
    - Performance benchmarking
    - Error handling and recovery
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the integration tester."""
        self.logger = logger or logging.getLogger(__name__)
        self.test_results: List[TestResult] = []
        self.performance_metrics: List[PerformanceMetric] = []
        self.temp_dir: Optional[tempfile.TemporaryDirectory] = None
        self.database_path: Optional[str] = None
        self.server: Optional[MyDocsMCPServer] = None
        self.database_manager: Optional[DocumentManager] = None
        
        # Test documents for integration testing
        self.test_documents = [
            TestDocument(
                file_path="test_document_1.md",
                content="""# Machine Learning Fundamentals

## Introduction
Machine learning is a subset of artificial intelligence that focuses on algorithms
that can learn from and make predictions on data.

## Key Concepts
- **Supervised Learning**: Learning with labeled data
- **Unsupervised Learning**: Finding patterns in unlabeled data
- **Reinforcement Learning**: Learning through interaction with environment

## Applications
Machine learning is used in:
1. Image recognition
2. Natural language processing
3. Recommendation systems
4. Autonomous vehicles

## Conclusion
Understanding these fundamentals is crucial for ML practitioners.
""",
                file_type="markdown",
                expected_title="Machine Learning Fundamentals",
                metadata={"category": "education", "difficulty": "beginner"}
            ),
            TestDocument(
                file_path="test_document_2.txt",
                content="""Project Management Best Practices

Effective project management requires careful planning and execution.
Here are key practices for successful project delivery:

Planning Phase:
- Define clear project scope and objectives
- Identify stakeholders and their requirements
- Create detailed work breakdown structure
- Establish timeline and milestones

Execution Phase:
- Regular team communication and status updates
- Risk monitoring and mitigation
- Quality assurance and testing
- Change management processes

Closing Phase:
- Project review and lessons learned
- Documentation and knowledge transfer
- Stakeholder satisfaction assessment

Tools and Technologies:
- Agile methodologies (Scrum, Kanban)
- Project management software (Jira, Asana)
- Communication platforms (Slack, Teams)
- Documentation tools (Confluence, Notion)

Success Factors:
1. Clear communication
2. Stakeholder engagement
3. Risk management
4. Quality focus
5. Continuous improvement

Remember: Good project management is essential for delivering value to customers.
""",
                file_type="text",
                expected_title="Project Management Best Practices",
                metadata={"category": "management", "difficulty": "intermediate"}
            ),
            TestDocument(
                file_path="test_document_3.md",
                content="""# Python Programming Advanced Concepts

## Abstract Classes and Interfaces

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        pass

class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
    
    def area(self) -> float:
        return self.width * self.height
    
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)
```

## Decorators and Context Managers

### Function Decorators
```python
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper
```

### Context Managers
```python
from contextlib import contextmanager

@contextmanager
def database_transaction():
    connection = get_database_connection()
    transaction = connection.begin()
    try:
        yield connection
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise
    finally:
        connection.close()
```

## Asynchronous Programming

```python
import asyncio
import aiohttp

async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def main():
    urls = ["http://api1.com", "http://api2.com", "http://api3.com"]
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results
```

## Performance Optimization

### Memory Management
- Use generators for large datasets
- Implement proper caching strategies
- Profile memory usage with tools like memory_profiler

### CPU Optimization
- Use multiprocessing for CPU-bound tasks
- Implement algorithmic improvements
- Profile with cProfile and line_profiler

## Best Practices
1. Follow PEP 8 style guidelines
2. Write comprehensive tests
3. Use type hints for better code documentation
4. Handle exceptions gracefully
5. Optimize for readability first, performance second
""",
                file_type="markdown",
                expected_title="Python Programming Advanced Concepts",
                metadata={"category": "programming", "language": "python", "difficulty": "advanced"}
            )
        ]
    
    async def setup_test_environment(self) -> bool:
        """Set up the test environment with temporary database and files."""
        try:
            self.logger.info("Setting up Day 1 integration test environment")
            
            # Create temporary directory
            self.temp_dir = tempfile.TemporaryDirectory()
            temp_path = Path(self.temp_dir.name)
            
            # Create database path
            self.database_path = str(temp_path / "test_database.db")
            
            # Create test document files
            for doc in self.test_documents:
                doc_path = temp_path / doc.file_path
                doc_path.write_text(doc.content, encoding='utf-8')
                # Update document path to absolute path
                doc.file_path = str(doc_path)
            
            self.logger.info(f"Test environment set up in: {temp_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set up test environment: {e}", exc_info=True)
            return False
    
    async def cleanup_test_environment(self) -> None:
        """Clean up the test environment."""
        try:
            if self.database_manager:
                await self.database_manager.close()
                self.database_manager = None
            
            if self.server:
                await self.server.stop()
                self.server = None
            
            if self.temp_dir:
                self.temp_dir.cleanup()
                self.temp_dir = None
            
            self.logger.info("Test environment cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}", exc_info=True)
    
    def _record_test_result(self, test_name: str, success: bool, duration_ms: float, 
                          error: Optional[str] = None, metrics: Optional[Dict[str, Any]] = None) -> None:
        """Record a test result."""
        result = TestResult(
            test_name=test_name,
            success=success,
            duration_ms=duration_ms,
            error=error,
            metrics=metrics
        )
        self.test_results.append(result)
        
        status = "PASS" if success else "FAIL"
        self.logger.info(f"Test '{test_name}': {status} ({duration_ms:.2f}ms)")
        if error:
            self.logger.error(f"Test error: {error}")
    
    def _record_performance_metric(self, operation: str, duration_ms: float, 
                                 success: bool, error: Optional[str] = None) -> None:
        """Record a performance metric."""
        metric = PerformanceMetric(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error=error
        )
        self.performance_metrics.append(metric)
    
    async def test_server_startup_and_shutdown(self) -> bool:
        """Test MCP server startup and graceful shutdown."""
        test_name = "Server Startup and Shutdown"
        start_time = time.time()
        
        try:
            self.logger.info("Testing MCP server startup and shutdown")
            
            # Create server configuration
            config = ServerConfig(
                database_url=f"sqlite:///{self.database_path}",
                transport="stdio",
                log_level="DEBUG"
            )
            
            # Test server creation
            server_start = time.time()
            self.server = MyDocsMCPServer(config)
            server_creation_time = (time.time() - server_start) * 1000
            
            # Test tool initialization (simulate startup process)
            init_start = time.time()
            tool_registry = ToolRegistry()
            success = await register_core_tools(
                tool_registry=tool_registry,
                database_path=self.database_path,
                logger=self.logger
            )
            init_time = (time.time() - init_start) * 1000
            
            if not success:
                raise Exception("Failed to register core tools")
            
            # Verify tool registration
            registered_tools = tool_registry.get_tool_names()
            expected_tools = {"indexDocument", "searchDocuments", "getDocument"}
            
            if not expected_tools.issubset(set(registered_tools)):
                missing_tools = expected_tools - set(registered_tools)
                raise Exception(f"Missing tools: {missing_tools}")
            
            # Test graceful shutdown
            shutdown_start = time.time()
            await self.server.stop()
            shutdown_time = (time.time() - shutdown_start) * 1000
            
            # Record performance metrics
            self._record_performance_metric("server_creation", server_creation_time, True)
            self._record_performance_metric("tool_initialization", init_time, True)
            self._record_performance_metric("server_shutdown", shutdown_time, True)
            
            duration = (time.time() - start_time) * 1000
            
            # Verify performance targets
            performance_check = init_time < 5000  # Less than 5 seconds for tool init
            
            metrics = {
                "server_creation_time_ms": server_creation_time,
                "tool_initialization_time_ms": init_time,
                "server_shutdown_time_ms": shutdown_time,
                "registered_tools": registered_tools,
                "performance_target_met": performance_check
            }
            
            self._record_test_result(test_name, True, duration, metrics=metrics)
            return True
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = f"Server startup/shutdown test failed: {str(e)}"
            self._record_test_result(test_name, False, duration, error_msg)
            return False
    
    async def test_tool_registration_and_discovery(self) -> bool:
        """Test MCP tool registration and discovery functionality."""
        test_name = "Tool Registration and Discovery"
        start_time = time.time()
        
        try:
            self.logger.info("Testing tool registration and discovery")
            
            # Initialize database manager
            self.database_manager = await create_document_manager(
                database_path=self.database_path,
                logger=self.logger
            )
            
            if not self.database_manager:
                raise Exception("Failed to create database manager")
            
            # Create tool registry
            tool_registry = ToolRegistry()
            parser_factory = get_default_factory(self.logger)
            
            # Test individual tool registration
            from src.tools.indexDocument import IndexDocumentTool
            from src.tools.searchDocuments import SearchDocumentsTool
            from src.tools.getDocument import GetDocumentTool
            
            # Test indexDocument tool
            index_tool = IndexDocumentTool(
                database_manager=self.database_manager,
                parser_factory=parser_factory,
                logger=self.logger
            )
            
            # Test searchDocuments tool
            search_tool = SearchDocumentsTool(
                database_manager=self.database_manager,
                parser_factory=parser_factory,
                logger=self.logger
            )
            
            # Test getDocument tool
            get_tool = GetDocumentTool(
                database_manager=self.database_manager,
                parser_factory=parser_factory,
                logger=self.logger
            )
            
            # Verify tool schemas
            tools = [index_tool, search_tool, get_tool]
            tool_schemas = {}
            
            for tool in tools:
                schema = tool.get_parameter_schema()
                tool_name = tool.get_tool_name()
                tool_schemas[tool_name] = schema
                
                # Validate schema structure
                if not isinstance(schema, dict):
                    raise Exception(f"Tool {tool_name} schema is not a dict")
                
                if "type" not in schema:
                    raise Exception(f"Tool {tool_name} schema missing type")
                
                if "properties" not in schema:
                    raise Exception(f"Tool {tool_name} schema missing properties")
            
            # Test complete registration
            registration_start = time.time()
            success = await register_core_tools(
                tool_registry=tool_registry,
                database_path=self.database_path,
                logger=self.logger
            )
            registration_time = (time.time() - registration_start) * 1000
            
            if not success:
                raise Exception("Core tools registration failed")
            
            # Verify tool discovery
            registered_tools = tool_registry.get_tool_names()
            available_tools = tool_registry.get_available_tools()
            
            expected_tools = {"indexDocument", "searchDocuments", "getDocument"}
            if not expected_tools.issubset(set(registered_tools)):
                missing = expected_tools - set(registered_tools)
                raise Exception(f"Missing registered tools: {missing}")
            
            # Verify MCP tool format
            for tool in available_tools:
                if not hasattr(tool, 'name'):
                    raise Exception("MCP tool missing name attribute")
                if not hasattr(tool, 'description'):
                    raise Exception("MCP tool missing description attribute")
                if not hasattr(tool, 'inputSchema'):
                    raise Exception("MCP tool missing inputSchema attribute")
            
            duration = (time.time() - start_time) * 1000
            
            metrics = {
                "registration_time_ms": registration_time,
                "registered_tool_count": len(registered_tools),
                "available_tool_count": len(available_tools),
                "tool_schemas": tool_schemas,
                "registered_tools": registered_tools
            }
            
            self._record_performance_metric("tool_registration", registration_time, True)
            self._record_test_result(test_name, True, duration, metrics=metrics)
            return True
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = f"Tool registration test failed: {str(e)}"
            self._record_test_result(test_name, False, duration, error_msg)
            return False
    
    async def test_complete_document_workflows(self) -> bool:
        """Test complete document processing workflows end-to-end."""
        test_name = "Complete Document Workflows"
        start_time = time.time()
        
        try:
            self.logger.info("Testing complete document workflows")
            
            # Ensure database manager is available
            if not self.database_manager:
                self.database_manager = await create_document_manager(
                    database_path=self.database_path,
                    logger=self.logger
                )
            
            # Create tool registry and register tools
            tool_registry = ToolRegistry()
            success = await register_core_tools(
                tool_registry=tool_registry,
                database_path=self.database_path,
                logger=self.logger
            )
            
            if not success:
                raise Exception("Failed to register tools for workflow testing")
            
            workflow_results = []
            
            # Test Workflow 1: Index -> Search -> Retrieve by ID
            for i, doc in enumerate(self.test_documents):
                workflow_start = time.time()
                
                # Step 1: Index document
                index_start = time.time()
                index_result = await tool_registry.execute_tool("indexDocument", {
                    "file_path": doc.file_path
                })
                index_time = (time.time() - index_start) * 1000
                
                # Debug: Print index result
                self.logger.debug(f"Index result for {doc.file_path}: {index_result}")
                
                if "error" in index_result:
                    raise Exception(f"Index failed for {doc.file_path}: {index_result['error']}")
                
                # Verify indexing success
                if not index_result.get("success", False):
                    raise Exception(f"Index operation reported failure for {doc.file_path}: {index_result}")
                
                # Get document ID from the data field
                data = index_result.get("data", {})
                document_id = data.get("document_id")
                if not document_id:
                    raise Exception(f"No document ID returned for {doc.file_path}. Full result: {index_result}")
                
                # Step 2: Search for the document
                search_start = time.time()
                search_query = doc.expected_title.split()[0] if doc.expected_title else "test"
                search_result = await tool_registry.execute_tool("searchDocuments", {
                    "query": search_query,
                    "limit": 10
                })
                search_time = (time.time() - search_start) * 1000
                
                if "error" in search_result:
                    raise Exception(f"Search failed for query '{search_query}': {search_result['error']}")
                
                # Debug search result structure
                self.logger.debug(f"Search result for query '{search_query}': {search_result}")
                
                # Verify search results (extract from data field if present)
                if "data" in search_result:
                    documents = search_result["data"].get("results", [])
                else:
                    documents = search_result.get("documents", [])
                    
                if not documents:
                    # Try a more general search
                    fallback_result = await tool_registry.execute_tool("searchDocuments", {
                        "query": "test",
                        "limit": 10
                    })
                    if "data" in fallback_result:
                        documents = fallback_result["data"].get("results", [])
                    else:
                        documents = fallback_result.get("documents", [])
                    
                    if not documents:
                        raise Exception(f"No search results for query '{search_query}' or fallback 'test'. Index result: {index_result}, Search result: {search_result}")
                
                # Find our document in results
                found_document = None
                for search_doc in documents:
                    # Check for both 'id' and 'document_id' fields
                    doc_id = search_doc.get("id") or search_doc.get("document_id")
                    if doc_id == document_id:
                        found_document = search_doc
                        break
                
                if not found_document:
                    raise Exception(f"Indexed document not found in search results for query '{search_query}'")
                
                # Step 3: Retrieve document by ID
                get_start = time.time()
                get_result = await tool_registry.execute_tool("getDocument", {
                    "document_id": document_id,
                    "format": "json",
                    "include_metadata": True
                })
                get_time = (time.time() - get_start) * 1000
                
                if "error" in get_result:
                    raise Exception(f"Get document failed for ID {document_id}: {get_result['error']}")
                
                # Verify document content (extract from data field if present)
                if "data" in get_result:
                    retrieved_doc = get_result["data"].get("document")
                else:
                    retrieved_doc = get_result.get("document")
                    
                if not retrieved_doc:
                    raise Exception(f"No document returned for ID {document_id}. Get result: {get_result}")
                
                # Verify content integrity
                retrieved_content = retrieved_doc.get("content", "")
                if not retrieved_content:
                    raise Exception(f"Empty content retrieved for document ID {document_id}. Document: {retrieved_doc}")
                
                # Check that original content is preserved (basic check)
                original_lines = doc.content.strip().split('\n')
                retrieved_lines = retrieved_content.strip().split('\n')
                
                if len(retrieved_lines) < len(original_lines) * 0.8:  # Allow some processing differences
                    raise Exception(f"Content significantly different after round-trip for {doc.file_path}")
                
                workflow_time = (time.time() - workflow_start) * 1000
                
                # Record performance metrics
                self._record_performance_metric(f"index_document_{i}", index_time, True)
                self._record_performance_metric(f"search_documents_{i}", search_time, True)
                self._record_performance_metric(f"get_document_{i}", get_time, True)
                self._record_performance_metric(f"complete_workflow_{i}", workflow_time, True)
                
                workflow_results.append({
                    "document_path": doc.file_path,
                    "document_id": document_id,
                    "index_time_ms": index_time,
                    "search_time_ms": search_time,
                    "get_time_ms": get_time,
                    "total_workflow_time_ms": workflow_time,
                    "search_query": search_query,
                    "search_results_count": len(documents),
                    "content_integrity_check": "passed"
                })
            
            # Test Workflow 2: Search with filtering
            filter_test_start = time.time()
            
            # Search for markdown files only
            md_search_result = await tool_registry.execute_tool("searchDocuments", {
                "query": "python",
                "file_type": "markdown",
                "limit": 5
            })
            
            if "error" in md_search_result:
                raise Exception(f"Filtered search failed: {md_search_result['error']}")
            
            if "data" in md_search_result:
                md_documents = md_search_result["data"].get("results", [])
            else:
                md_documents = md_search_result.get("documents", [])
            
            # Verify filtering worked
            for doc in md_documents:
                file_path = doc.get("file_path", "")
                if not file_path.endswith(".md"):
                    raise Exception(f"Filter failed: non-markdown file in results: {file_path}")
            
            filter_test_time = (time.time() - filter_test_start) * 1000
            self._record_performance_metric("filtered_search", filter_test_time, True)
            
            # Test Workflow 3: Retrieve by path
            path_test_start = time.time()
            
            test_doc = self.test_documents[0]
            path_result = await tool_registry.execute_tool("getDocument", {
                "file_path": test_doc.file_path,
                "format": "markdown",
                "include_metadata": True
            })
            
            if "error" in path_result:
                raise Exception(f"Get by path failed: {path_result['error']}")
            
            path_test_time = (time.time() - path_test_start) * 1000
            self._record_performance_metric("get_document_by_path", path_test_time, True)
            
            duration = (time.time() - start_time) * 1000
            
            # Validate performance requirements
            avg_index_time = sum(r["index_time_ms"] for r in workflow_results) / len(workflow_results)
            avg_search_time = sum(r["search_time_ms"] for r in workflow_results) / len(workflow_results)
            avg_get_time = sum(r["get_time_ms"] for r in workflow_results) / len(workflow_results)
            
            performance_targets_met = (
                avg_index_time < 1000 and  # < 1 second for indexing
                avg_search_time < 200 and  # < 200ms for search
                avg_get_time < 200  # < 200ms for retrieval
            )
            
            metrics = {
                "workflow_count": len(workflow_results),
                "average_index_time_ms": avg_index_time,
                "average_search_time_ms": avg_search_time,
                "average_get_time_ms": avg_get_time,
                "performance_targets_met": performance_targets_met,
                "workflow_details": workflow_results,
                "filtered_search_results": len(md_documents),
                "path_retrieval_time_ms": path_test_time
            }
            
            self._record_test_result(test_name, True, duration, metrics=metrics)
            return True
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = f"Document workflow test failed: {str(e)}\n{traceback.format_exc()}"
            self._record_test_result(test_name, False, duration, error_msg)
            return False
    
    async def test_performance_benchmarks(self) -> bool:
        """Test performance benchmarks and validate response time requirements."""
        test_name = "Performance Benchmarks"
        start_time = time.time()
        
        try:
            self.logger.info("Running performance benchmark tests")
            
            # Ensure tools are registered
            if not self.database_manager:
                self.database_manager = await create_document_manager(
                    database_path=self.database_path,
                    logger=self.logger
                )
            
            tool_registry = ToolRegistry()
            success = await register_core_tools(
                tool_registry=tool_registry,
                database_path=self.database_path,
                logger=self.logger
            )
            
            if not success:
                raise Exception("Failed to register tools for performance testing")
            
            # Ensure we have indexed documents
            for doc in self.test_documents:
                await tool_registry.execute_tool("indexDocument", {"file_path": doc.file_path})
            
            performance_results = {}
            
            # Benchmark 1: Search Response Time Distribution
            search_times = []
            search_queries = [
                "python", "machine learning", "project management", 
                "programming", "algorithms", "best practices",
                "fundamentals", "concepts", "applications", "tools"
            ]
            
            for query in search_queries:
                search_start = time.time()
                result = await tool_registry.execute_tool("searchDocuments", {
                    "query": query,
                    "limit": 10
                })
                search_time = (time.time() - search_start) * 1000
                
                if "error" not in result:
                    search_times.append(search_time)
                    self._record_performance_metric(f"search_query_{query}", search_time, True)
                else:
                    self._record_performance_metric(f"search_query_{query}", search_time, False, result["error"])
            
            # Calculate search statistics
            if search_times:
                avg_search_time = sum(search_times) / len(search_times)
                min_search_time = min(search_times)
                max_search_time = max(search_times)
                
                # Calculate percentiles
                search_times_sorted = sorted(search_times)
                p95_index = int(0.95 * len(search_times_sorted))
                p99_index = int(0.99 * len(search_times_sorted))
                p95_search_time = search_times_sorted[p95_index] if p95_index < len(search_times_sorted) else max_search_time
                p99_search_time = search_times_sorted[p99_index] if p99_index < len(search_times_sorted) else max_search_time
                
                performance_results["search"] = {
                    "average_ms": avg_search_time,
                    "min_ms": min_search_time,
                    "max_ms": max_search_time,
                    "p95_ms": p95_search_time,
                    "p99_ms": p99_search_time,
                    "sub_200ms_count": sum(1 for t in search_times if t < 200),
                    "total_queries": len(search_times),
                    "sub_200ms_percentage": (sum(1 for t in search_times if t < 200) / len(search_times)) * 100
                }
            
            # Benchmark 2: Document Retrieval Performance
            get_times = []
            
            # Get all indexed documents
            search_all = await tool_registry.execute_tool("searchDocuments", {
                "query": "*",
                "limit": 100
            })
            
            if "error" not in search_all:
                if "data" in search_all:
                    documents = search_all["data"].get("results", [])
                else:
                    documents = search_all.get("documents", [])
                
                for doc in documents[:10]:  # Test first 10 documents
                    doc_id = doc.get("id") or doc.get("document_id")
                    if doc_id:
                        get_start = time.time()
                        result = await tool_registry.execute_tool("getDocument", {
                            "document_id": doc_id,
                            "format": "json"
                        })
                        get_time = (time.time() - get_start) * 1000
                        
                        if "error" not in result:
                            get_times.append(get_time)
                            self._record_performance_metric(f"get_document_{doc_id}", get_time, True)
                        else:
                            self._record_performance_metric(f"get_document_{doc_id}", get_time, False, result["error"])
            
            # Calculate retrieval statistics
            if get_times:
                avg_get_time = sum(get_times) / len(get_times)
                min_get_time = min(get_times)
                max_get_time = max(get_times)
                
                performance_results["retrieval"] = {
                    "average_ms": avg_get_time,
                    "min_ms": min_get_time,
                    "max_ms": max_get_time,
                    "sub_200ms_count": sum(1 for t in get_times if t < 200),
                    "total_retrievals": len(get_times),
                    "sub_200ms_percentage": (sum(1 for t in get_times if t < 200) / len(get_times)) * 100
                }
            
            # Benchmark 3: Concurrent Operations
            concurrent_start = time.time()
            
            # Run 5 concurrent searches
            concurrent_tasks = []
            for i in range(5):
                task = tool_registry.execute_tool("searchDocuments", {
                    "query": f"test query {i}",
                    "limit": 5
                })
                concurrent_tasks.append(task)
            
            concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            concurrent_time = (time.time() - concurrent_start) * 1000
            
            concurrent_successes = sum(1 for r in concurrent_results if not isinstance(r, Exception) and "error" not in r)
            
            performance_results["concurrent"] = {
                "total_time_ms": concurrent_time,
                "concurrent_operations": len(concurrent_tasks),
                "successful_operations": concurrent_successes,
                "success_rate": (concurrent_successes / len(concurrent_tasks)) * 100,
                "average_concurrent_response_ms": concurrent_time / len(concurrent_tasks)
            }
            
            self._record_performance_metric("concurrent_operations", concurrent_time, concurrent_successes == len(concurrent_tasks))
            
            # Validate performance requirements
            search_performance_ok = performance_results.get("search", {}).get("average_ms", 1000) < 200
            retrieval_performance_ok = performance_results.get("retrieval", {}).get("average_ms", 1000) < 200
            concurrent_performance_ok = performance_results.get("concurrent", {}).get("total_time_ms", 10000) < 5000
            
            overall_performance_ok = search_performance_ok and retrieval_performance_ok and concurrent_performance_ok
            
            duration = (time.time() - start_time) * 1000
            
            metrics = {
                "performance_results": performance_results,
                "search_performance_target_met": search_performance_ok,
                "retrieval_performance_target_met": retrieval_performance_ok,
                "concurrent_performance_target_met": concurrent_performance_ok,
                "overall_performance_target_met": overall_performance_ok
            }
            
            self._record_test_result(test_name, overall_performance_ok, duration, 
                                  None if overall_performance_ok else "Performance targets not met",
                                  metrics=metrics)
            return overall_performance_ok
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = f"Performance benchmark test failed: {str(e)}"
            self._record_test_result(test_name, False, duration, error_msg)
            return False
    
    async def test_error_handling_and_recovery(self) -> bool:
        """Test error handling and recovery scenarios."""
        test_name = "Error Handling and Recovery"
        start_time = time.time()
        
        try:
            self.logger.info("Testing error handling and recovery")
            
            # Ensure tools are registered
            if not self.database_manager:
                self.database_manager = await create_document_manager(
                    database_path=self.database_path,
                    logger=self.logger
                )
            
            tool_registry = ToolRegistry()
            success = await register_core_tools(
                tool_registry=tool_registry,
                database_path=self.database_path,
                logger=self.logger
            )
            
            if not success:
                raise Exception("Failed to register tools for error testing")
            
            error_test_results = []
            
            # Test 1: Invalid file path for indexing
            test_start = time.time()
            result = await tool_registry.execute_tool("indexDocument", {
                "file_path": "/nonexistent/path/to/file.txt"
            })
            test_time = (time.time() - test_start) * 1000
            
            # Should return an error, not crash
            if "error" not in result:
                raise Exception("Expected error for non-existent file, but got success")
            
            error_test_results.append({
                "test": "non_existent_file_index",
                "expected_error": True,
                "got_error": True,
                "time_ms": test_time,
                "error_message": result.get("error", "")
            })
            
            # Test 2: Invalid document ID for retrieval
            test_start = time.time()
            result = await tool_registry.execute_tool("getDocument", {
                "document_id": 99999,
                "format": "json"
            })
            test_time = (time.time() - test_start) * 1000
            
            if "error" not in result:
                raise Exception("Expected error for non-existent document ID, but got success")
            
            error_test_results.append({
                "test": "non_existent_document_id",
                "expected_error": True,
                "got_error": True,
                "time_ms": test_time,
                "error_message": result.get("error", "")
            })
            
            # Test 3: Invalid file path for retrieval
            test_start = time.time()
            result = await tool_registry.execute_tool("getDocument", {
                "file_path": "/nonexistent/path/to/file.txt",
                "format": "json"
            })
            test_time = (time.time() - test_start) * 1000
            
            if "error" not in result:
                raise Exception("Expected error for non-existent file path, but got success")
            
            error_test_results.append({
                "test": "non_existent_file_path",
                "expected_error": True,
                "got_error": True,
                "time_ms": test_time,
                "error_message": result.get("error", "")
            })
            
            # Test 4: Empty search query
            test_start = time.time()
            result = await tool_registry.execute_tool("searchDocuments", {
                "query": "",
                "limit": 10
            })
            test_time = (time.time() - test_start) * 1000
            
            if "error" not in result:
                raise Exception("Expected error for empty search query, but got success")
            
            error_test_results.append({
                "test": "empty_search_query",
                "expected_error": True,
                "got_error": True,
                "time_ms": test_time,
                "error_message": result.get("error", "")
            })
            
            # Test 5: Invalid parameters (missing required fields)
            test_start = time.time()
            result = await tool_registry.execute_tool("indexDocument", {})
            test_time = (time.time() - test_start) * 1000
            
            if "error" not in result:
                raise Exception("Expected error for missing required parameters, but got success")
            
            error_test_results.append({
                "test": "missing_required_parameters",
                "expected_error": True,
                "got_error": True,
                "time_ms": test_time,
                "error_message": result.get("error", "")
            })
            
            # Test 6: Invalid tool name
            test_start = time.time()
            try:
                result = await tool_registry.execute_tool("nonExistentTool", {"param": "value"})
                # If we get here, the tool registry should have returned an error
                if "error" not in result:
                    raise Exception("Expected error for non-existent tool, but got success")
                
                error_test_results.append({
                    "test": "non_existent_tool",
                    "expected_error": True,
                    "got_error": True,
                    "time_ms": (time.time() - test_start) * 1000,
                    "error_message": result.get("error", "")
                })
            except Exception as e:
                # Tool registry might raise exception instead of returning error
                error_test_results.append({
                    "test": "non_existent_tool",
                    "expected_error": True,
                    "got_error": True,
                    "time_ms": (time.time() - test_start) * 1000,
                    "error_message": str(e)
                })
            
            # Test 7: System recovery - verify system still works after errors
            test_start = time.time()
            
            # Index a valid document
            valid_doc = self.test_documents[0]
            result = await tool_registry.execute_tool("indexDocument", {
                "file_path": valid_doc.file_path
            })
            
            if "error" in result:
                raise Exception(f"System recovery failed - cannot index valid document: {result['error']}")
            
            # Search for the document
            result = await tool_registry.execute_tool("searchDocuments", {
                "query": "test",
                "limit": 5
            })
            
            if "error" in result:
                raise Exception(f"System recovery failed - cannot search documents: {result['error']}")
            
            recovery_time = (time.time() - test_start) * 1000
            
            error_test_results.append({
                "test": "system_recovery_after_errors",
                "expected_error": False,
                "got_error": False,
                "time_ms": recovery_time,
                "error_message": None
            })
            
            duration = (time.time() - start_time) * 1000
            
            # Verify all error tests passed
            all_error_tests_passed = all(
                test["expected_error"] == test["got_error"] 
                for test in error_test_results
            )
            
            metrics = {
                "error_test_count": len(error_test_results),
                "error_tests_passed": all_error_tests_passed,
                "error_test_details": error_test_results,
                "system_recovery_successful": error_test_results[-1]["got_error"] == False
            }
            
            self._record_test_result(test_name, all_error_tests_passed, duration, 
                                  None if all_error_tests_passed else "Some error handling tests failed",
                                  metrics=metrics)
            return all_error_tests_passed
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = f"Error handling test failed: {str(e)}"
            self._record_test_result(test_name, False, duration, error_msg)
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests and return comprehensive results."""
        self.logger.info("Starting Day 1 comprehensive integration testing")
        
        overall_start = time.time()
        
        # Set up test environment
        setup_success = await self.setup_test_environment()
        if not setup_success:
            return {
                "success": False,
                "error": "Failed to set up test environment",
                "duration_ms": 0,
                "test_results": [],
                "performance_metrics": []
            }
        
        try:
            # Run all test suites
            test_functions = [
                self.test_server_startup_and_shutdown,
                self.test_tool_registration_and_discovery,
                self.test_complete_document_workflows,
                self.test_performance_benchmarks,
                self.test_error_handling_and_recovery
            ]
            
            all_tests_passed = True
            
            for test_func in test_functions:
                try:
                    test_result = await test_func()
                    if not test_result:
                        all_tests_passed = False
                except Exception as e:
                    self.logger.error(f"Test function {test_func.__name__} failed: {e}", exc_info=True)
                    all_tests_passed = False
            
            total_duration = (time.time() - overall_start) * 1000
            
            # Generate comprehensive results
            results = {
                "success": all_tests_passed,
                "total_duration_ms": total_duration,
                "test_count": len(self.test_results),
                "passed_tests": sum(1 for t in self.test_results if t.success),
                "failed_tests": sum(1 for t in self.test_results if not t.success),
                "performance_metrics_count": len(self.performance_metrics),
                "test_results": [
                    {
                        "name": t.test_name,
                        "success": t.success,
                        "duration_ms": t.duration_ms,
                        "error": t.error,
                        "metrics": t.metrics
                    }
                    for t in self.test_results
                ],
                "performance_metrics": [
                    {
                        "operation": m.operation,
                        "duration_ms": m.duration_ms,
                        "success": m.success,
                        "error": m.error
                    }
                    for m in self.performance_metrics
                ]
            }
            
            return results
            
        finally:
            await self.cleanup_test_environment()


async def run_day1_integration_tests():
    """Main entry point for Day 1 integration testing."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger("day1_integration_tests")
    logger.info("Starting mydocs-mcp Day 1 Integration Testing Suite")
    
    # Create and run integration tester
    tester = Day1IntegrationTester(logger)
    
    try:
        results = await tester.run_all_tests()
        
        # Print summary
        print("\n" + "="*80)
        print("DAY 1 INTEGRATION TESTING RESULTS")
        print("="*80)
        
        print(f"Overall Success: {'PASS' if results['success'] else 'FAIL'}")
        print(f"Total Duration: {results['total_duration_ms']:.2f}ms")
        print(f"Tests Run: {results['test_count']}")
        print(f"Tests Passed: {results['passed_tests']}")
        print(f"Tests Failed: {results['failed_tests']}")
        print(f"Performance Metrics: {results['performance_metrics_count']}")
        
        print("\nTest Results Summary:")
        print("-" * 80)
        for test_result in results['test_results']:
            status = "PASS" if test_result['success'] else "FAIL"
            print(f"{test_result['name']}: {status} ({test_result['duration_ms']:.2f}ms)")
            if test_result['error']:
                print(f"  Error: {test_result['error']}")
        
        print("\nPerformance Summary:")
        print("-" * 80)
        
        # Group performance metrics by operation type
        perf_by_type = {}
        for metric in results['performance_metrics']:
            op_type = metric['operation'].split('_')[0]
            if op_type not in perf_by_type:
                perf_by_type[op_type] = []
            perf_by_type[op_type].append(metric['duration_ms'])
        
        for op_type, times in perf_by_type.items():
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            print(f"{op_type}: avg={avg_time:.2f}ms, min={min_time:.2f}ms, max={max_time:.2f}ms ({len(times)} operations)")
        
        # Day 1 readiness assessment
        print("\n" + "="*80)
        print("DAY 1 READINESS ASSESSMENT")
        print("="*80)
        
        if results['success']:
            print("✓ Day 1 Foundation READY for Day 2 development")
            print("✓ All core MCP tools operational")
            print("✓ Performance targets met")
            print("✓ Error handling validated")
            print("✓ Integration workflows confirmed")
        else:
            print("✗ Day 1 Foundation has issues")
            print("! Review failed tests before proceeding to Day 2")
            
            # Identify critical issues
            critical_failures = [t for t in results['test_results'] if not t['success']]
            if critical_failures:
                print(f"!  {len(critical_failures)} critical test failures identified")
        
        return results
        
    except Exception as e:
        logger.error(f"Integration testing failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "duration_ms": 0,
            "test_results": [],
            "performance_metrics": []
        }


if __name__ == "__main__":
    # Run the integration tests
    results = asyncio.run(run_day1_integration_tests())
    
    # Exit with appropriate code
    exit_code = 0 if results.get('success', False) else 1
    exit(exit_code)