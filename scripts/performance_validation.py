#!/usr/bin/env python3
"""
mydocs-mcp Performance Validation Script

Validates all performance requirements for Day 2 completion.
Tests response times, memory usage, and concurrent operations.
"""

import asyncio
import time
import statistics
import sys
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import psutil
import gc

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.database_manager import DocumentManager
from database.connection import get_database_connection
from tools.searchDocuments import SearchDocumentsTool
from tools.getDocument import GetDocumentTool
from parsers.parser_factory import ParserFactory
import logging_config

# Configure logging
logger = logging_config.setup_logging()

class PerformanceValidator:
    """Performance validation for mydocs-mcp system."""
    
    def __init__(self):
        self.test_results = {}
        self.temp_dir = None
        self.db_connection = None
        self.document_manager = None
        self.process = psutil.Process()
        self.initial_memory = None
        
    async def setup_test_environment(self):
        """Setup test environment with sample documents."""
        logger.info("Setting up performance test environment...")
        
        # Record initial memory
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Create temp directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="mydocs_perf_"))
        
        # Setup database
        db_path = self.temp_dir / "perf_test.db"
        self.db_connection = await get_database_connection(str(db_path))
        self.document_manager = DocumentManager(self.db_connection)
        
        # Initialize database
        await self.document_manager.initialize_database()
        
        # Create test documents
        docs_dir = self.temp_dir / "documents"
        docs_dir.mkdir()
        
        # Create various document types and sizes
        self.create_test_documents(docs_dir)
        
        # Index all documents
        await self.index_test_documents(docs_dir)
        
        logger.info(f"Performance test environment ready: {self.temp_dir}")
        
    def create_test_documents(self, docs_dir: Path):
        """Create test documents of various sizes and types."""
        
        # Small documents (< 1KB)
        for i in range(10):
            (docs_dir / f"small_doc_{i}.md").write_text(
                f"# Small Document {i}\n\nThis is a small test document with keyword content."
            )
            
        # Medium documents (1-10KB) 
        medium_content = "This is a medium-sized document. " * 100
        for i in range(10):
            (docs_dir / f"medium_doc_{i}.txt").write_text(
                f"Medium Document {i}\n\n{medium_content}\n\nKeyword: test{i}"
            )
            
        # Large documents (10-100KB)
        large_content = "This is a large document with extensive content. " * 1000
        for i in range(5):
            (docs_dir / f"large_doc_{i}.md").write_text(
                f"# Large Document {i}\n\n{large_content}\n\nKeyword: large{i}"
            )
            
        logger.info(f"Created {len(list(docs_dir.glob('*')))} test documents")
        
    async def index_test_documents(self, docs_dir: Path):
        """Index all test documents."""
        parser_factory = ParserFactory()
        
        for doc_file in docs_dir.glob("*"):
            try:
                parser = parser_factory.get_parser(str(doc_file))
                parsed_doc = await parser.parse(str(doc_file))
                
                await self.document_manager.add_document(
                    file_path=str(doc_file),
                    title=parsed_doc.title or doc_file.name,
                    content=parsed_doc.content,
                    metadata=parsed_doc.metadata
                )
            except Exception as e:
                logger.warning(f"Failed to index {doc_file}: {e}")
                
        logger.info("Test documents indexed successfully")
        
    async def cleanup_test_environment(self):
        """Clean up test environment."""
        if self.db_connection:
            await self.db_connection.close()
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    async def measure_execution_time(self, coro, description: str) -> float:
        """Measure execution time of an async coroutine in milliseconds."""
        start_time = time.perf_counter()
        result = await coro
        execution_time = (time.perf_counter() - start_time) * 1000
        
        logger.info(f"{description}: {execution_time:.2f}ms")
        return execution_time, result
        
    async def test_database_performance(self):
        """Test database operation performance."""
        logger.info("Testing database performance...")
        
        results = {}
        
        # Test document insertion
        test_content = "Performance test document content."
        
        execution_time, doc_id = await self.measure_execution_time(
            self.document_manager.add_document(
                file_path="/test/perf_insert.md",
                title="Performance Test Document",
                content=test_content,
                metadata={"test": "performance"}
            ),
            "Document insertion"
        )
        results["document_insertion"] = execution_time
        
        # Test document retrieval by ID
        execution_time, document = await self.measure_execution_time(
            self.document_manager.get_document_by_id(doc_id),
            "Document retrieval by ID"
        )
        results["document_retrieval_by_id"] = execution_time
        
        # Test document retrieval by path
        execution_time, document = await self.measure_execution_time(
            self.document_manager.get_document_by_path("/test/perf_insert.md"),
            "Document retrieval by path"
        )
        results["document_retrieval_by_path"] = execution_time
        
        # Test document search
        execution_time, search_results = await self.measure_execution_time(
            self.document_manager.search_documents("test", limit=10),
            "Document search"
        )
        results["document_search"] = execution_time
        
        # Test bulk operations
        start_time = time.perf_counter()
        all_docs = await self.document_manager.get_all_documents()
        execution_time = (time.perf_counter() - start_time) * 1000
        results["get_all_documents"] = execution_time
        logger.info(f"Get all documents ({len(all_docs)} docs): {execution_time:.2f}ms")
        
        self.test_results["database_performance"] = results
        return results
        
    async def test_tool_performance(self):
        """Test MCP tool performance."""
        logger.info("Testing MCP tool performance...")
        
        results = {}
        
        # Initialize tools
        search_tool = SearchDocumentsTool(self.document_manager, logger)
        get_tool = GetDocumentTool(self.document_manager, logger)
        
        # Test searchDocuments tool
        search_queries = [
            {"query": "test", "limit": 10},
            {"query": "document", "limit": 20},
            {"query": "medium", "file_type": "text", "limit": 5},
            {"query": "large", "sort_by": "date", "limit": 15}
        ]
        
        search_times = []
        for query_params in search_queries:
            execution_time, result = await self.measure_execution_time(
                search_tool.execute(query_params),
                f"Search tool: {query_params['query']}"
            )
            search_times.append(execution_time)
            
        results["search_tool_avg"] = statistics.mean(search_times)
        results["search_tool_max"] = max(search_times)
        results["search_tool_min"] = min(search_times)
        
        # Test getDocument tool
        # First get some document IDs
        search_result = await search_tool.execute({"query": "test", "limit": 5})
        documents = search_result.get("documents", [])
        
        get_times = []
        for doc in documents[:3]:  # Test first 3 documents
            doc_id = doc.get("id")
            execution_time, result = await self.measure_execution_time(
                get_tool.execute({"document_id": str(doc_id)}),
                f"Get document: {doc_id}"
            )
            get_times.append(execution_time)
            
        if get_times:
            results["get_tool_avg"] = statistics.mean(get_times)
            results["get_tool_max"] = max(get_times)
            results["get_tool_min"] = min(get_times)
        
        self.test_results["tool_performance"] = results
        return results
        
    async def test_concurrent_performance(self):
        """Test performance under concurrent load."""
        logger.info("Testing concurrent performance...")
        
        search_tool = SearchDocumentsTool(self.document_manager, logger)
        
        # Define concurrent operations
        async def concurrent_search(query_id: int):
            start_time = time.perf_counter()
            result = await search_tool.execute({
                "query": f"test document {query_id % 5}",
                "limit": 10
            })
            return (time.perf_counter() - start_time) * 1000
            
        # Run 10 concurrent searches
        logger.info("Running 10 concurrent searches...")
        start_time = time.perf_counter()
        
        concurrent_tasks = [concurrent_search(i) for i in range(10)]
        execution_times = await asyncio.gather(*concurrent_tasks)
        
        total_concurrent_time = (time.perf_counter() - start_time) * 1000
        
        results = {
            "concurrent_operations": 10,
            "total_time_ms": total_concurrent_time,
            "avg_response_time": statistics.mean(execution_times),
            "max_response_time": max(execution_times),
            "min_response_time": min(execution_times),
            "operations_per_second": 10 / (total_concurrent_time / 1000)
        }
        
        logger.info(f"Concurrent performance: {results['operations_per_second']:.2f} ops/sec")
        logger.info(f"Avg response time: {results['avg_response_time']:.2f}ms")
        
        self.test_results["concurrent_performance"] = results
        return results
        
    async def test_memory_performance(self):
        """Test memory usage and efficiency."""
        logger.info("Testing memory performance...")
        
        # Force garbage collection
        gc.collect()
        
        # Current memory usage
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - self.initial_memory
        
        # Memory efficiency test - run operations and check memory
        search_tool = SearchDocumentsTool(self.document_manager, logger)
        
        # Run multiple operations
        for i in range(50):
            await search_tool.execute({"query": f"test {i}", "limit": 10})
            if i % 10 == 0:
                gc.collect()  # Periodic garbage collection
                
        # Final memory check
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - self.initial_memory
        
        results = {
            "initial_memory_mb": self.initial_memory,
            "current_memory_mb": current_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": memory_increase,
            "total_memory_increase_mb": total_memory_increase,
            "memory_efficiency": "GOOD" if total_memory_increase < 128 else "NEEDS_ATTENTION"
        }
        
        logger.info(f"Memory usage: {final_memory:.2f}MB (increase: {total_memory_increase:.2f}MB)")
        
        self.test_results["memory_performance"] = results
        return results
        
    async def validate_performance_targets(self):
        """Validate all performance targets."""
        logger.info("Validating performance targets...")
        
        validation_results = {}
        
        # Database performance targets
        db_perf = self.test_results.get("database_performance", {})
        validation_results["database_targets"] = {
            "document_insertion": {
                "target_ms": 200,
                "actual_ms": db_perf.get("document_insertion", 0),
                "passed": db_perf.get("document_insertion", 999) < 200
            },
            "document_retrieval": {
                "target_ms": 200,
                "actual_ms": db_perf.get("document_retrieval_by_id", 0),
                "passed": db_perf.get("document_retrieval_by_id", 999) < 200
            },
            "document_search": {
                "target_ms": 200,
                "actual_ms": db_perf.get("document_search", 0),
                "passed": db_perf.get("document_search", 999) < 200
            }
        }
        
        # Tool performance targets
        tool_perf = self.test_results.get("tool_performance", {})
        validation_results["tool_targets"] = {
            "search_tool": {
                "target_ms": 200,
                "actual_ms": tool_perf.get("search_tool_avg", 0),
                "passed": tool_perf.get("search_tool_avg", 999) < 200
            },
            "get_tool": {
                "target_ms": 200,
                "actual_ms": tool_perf.get("get_tool_avg", 0),
                "passed": tool_perf.get("get_tool_avg", 999) < 200
            }
        }
        
        # Concurrent performance targets
        concurrent_perf = self.test_results.get("concurrent_performance", {})
        validation_results["concurrent_targets"] = {
            "avg_response_time": {
                "target_ms": 500,  # More lenient for concurrent operations
                "actual_ms": concurrent_perf.get("avg_response_time", 0),
                "passed": concurrent_perf.get("avg_response_time", 999) < 500
            },
            "operations_per_second": {
                "target": 5.0,  # At least 5 ops/sec
                "actual": concurrent_perf.get("operations_per_second", 0),
                "passed": concurrent_perf.get("operations_per_second", 0) >= 5.0
            }
        }
        
        # Memory performance targets
        memory_perf = self.test_results.get("memory_performance", {})
        validation_results["memory_targets"] = {
            "total_memory_usage": {
                "target_mb": 512,
                "actual_mb": memory_perf.get("final_memory_mb", 0),
                "passed": memory_perf.get("final_memory_mb", 999) < 512
            },
            "memory_increase": {
                "target_mb": 128,
                "actual_mb": memory_perf.get("total_memory_increase_mb", 0),
                "passed": memory_perf.get("total_memory_increase_mb", 999) < 128
            }
        }
        
        self.test_results["performance_validation"] = validation_results
        return validation_results
        
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        
        # Count passed/failed validations
        validation_results = self.test_results.get("performance_validation", {})
        
        total_tests = 0
        passed_tests = 0
        
        for category in validation_results.values():
            for test_name, test_result in category.items():
                total_tests += 1
                if test_result.get("passed", False):
                    passed_tests += 1
                    
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "performance_summary": {
                "overall_status": "PASS" if pass_rate >= 80 else "FAIL",
                "pass_rate": f"{pass_rate:.1f}%",
                "tests_passed": passed_tests,
                "tests_failed": total_tests - passed_tests,
                "total_tests": total_tests
            },
            "detailed_results": self.test_results,
            "performance_highlights": {
                "database_avg_ms": statistics.mean([
                    v for v in self.test_results.get("database_performance", {}).values()
                    if isinstance(v, (int, float))
                ]) if self.test_results.get("database_performance") else 0,
                
                "tool_avg_ms": self.test_results.get("tool_performance", {}).get("search_tool_avg", 0),
                
                "memory_usage_mb": self.test_results.get("memory_performance", {}).get("final_memory_mb", 0),
                
                "concurrent_ops_per_sec": self.test_results.get("concurrent_performance", {}).get("operations_per_second", 0)
            }
        }
        
        return report
        
    async def run_performance_validation(self):
        """Run complete performance validation."""
        logger.info("🚀 Starting mydocs-mcp Performance Validation...")
        
        try:
            await self.setup_test_environment()
            
            # Run performance tests
            await self.test_database_performance()
            await self.test_tool_performance() 
            await self.test_concurrent_performance()
            await self.test_memory_performance()
            
            # Validate against targets
            await self.validate_performance_targets()
            
            # Generate report
            report = self.generate_performance_report()
            
            # Print summary
            logger.info(f"\n{'='*60}")
            logger.info("📊 PERFORMANCE VALIDATION SUMMARY")
            logger.info(f"{'='*60}")
            
            summary = report["performance_summary"]
            logger.info(f"Overall Status: {summary['overall_status']}")
            logger.info(f"Pass Rate: {summary['pass_rate']}")
            logger.info(f"Tests: {summary['tests_passed']}/{summary['total_tests']} passed")
            
            highlights = report["performance_highlights"]
            logger.info(f"\n⚡ PERFORMANCE HIGHLIGHTS:")
            logger.info(f"Database Avg: {highlights['database_avg_ms']:.1f}ms")
            logger.info(f"Tool Avg: {highlights['tool_avg_ms']:.1f}ms") 
            logger.info(f"Memory Usage: {highlights['memory_usage_mb']:.1f}MB")
            logger.info(f"Throughput: {highlights['concurrent_ops_per_sec']:.1f} ops/sec")
            
            # Performance targets met?
            performance_passed = summary["overall_status"] == "PASS"
            logger.info(f"\n🎯 PERFORMANCE TARGETS: {'✅ MET' if performance_passed else '❌ NOT MET'}")
            
            return report
            
        except Exception as e:
            logger.error(f"Performance validation failed: {e}")
            return {"status": "ERROR", "error": str(e)}
        finally:
            await self.cleanup_test_environment()

async def main():
    """Main performance validation entry point."""
    validator = PerformanceValidator()
    report = await validator.run_performance_validation()
    
    # Save performance report
    report_file = Path(__file__).parent.parent / "tests" / "PERFORMANCE_VALIDATION_REPORT.md"
    
    with open(report_file, "w") as f:
        f.write(f"# mydocs-mcp Performance Validation Report\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Status**: {report.get('performance_summary', {}).get('overall_status', 'UNKNOWN')}\n\n")
        
        if "performance_summary" in report:
            summary = report["performance_summary"]
            f.write(f"## Performance Summary\n")
            f.write(f"- **Pass Rate**: {summary['pass_rate']}\n")
            f.write(f"- **Tests Passed**: {summary['tests_passed']}\n")
            f.write(f"- **Tests Failed**: {summary['tests_failed']}\n")
            f.write(f"- **Total Tests**: {summary['total_tests']}\n\n")
            
        if "performance_highlights" in report:
            highlights = report["performance_highlights"]
            f.write(f"## Performance Highlights\n")
            f.write(f"- **Database Average**: {highlights['database_avg_ms']:.1f}ms\n")
            f.write(f"- **Tool Average**: {highlights['tool_avg_ms']:.1f}ms\n")
            f.write(f"- **Memory Usage**: {highlights['memory_usage_mb']:.1f}MB\n")
            f.write(f"- **Throughput**: {highlights['concurrent_ops_per_sec']:.1f} ops/sec\n\n")
            
        if "performance_validation" in report.get("detailed_results", {}):
            f.write(f"## Detailed Validation Results\n")
            validation = report["detailed_results"]["performance_validation"]
            
            for category_name, category_tests in validation.items():
                f.write(f"### {category_name.replace('_', ' ').title()}\n")
                for test_name, test_result in category_tests.items():
                    status = "✅ PASS" if test_result.get("passed") else "❌ FAIL"
                    f.write(f"- **{test_name}**: {status}")
                    if "actual_ms" in test_result:
                        f.write(f" ({test_result['actual_ms']:.1f}ms)")
                    elif "actual_mb" in test_result:
                        f.write(f" ({test_result['actual_mb']:.1f}MB)")
                    elif "actual" in test_result:
                        f.write(f" ({test_result['actual']:.1f})")
                    f.write(f"\n")
                f.write(f"\n")
    
    print(f"\n📋 Performance validation report saved to: {report_file}")
    return report

if __name__ == "__main__":
    asyncio.run(main())