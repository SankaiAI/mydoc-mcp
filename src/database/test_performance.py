"""
mydocs-mcp Database Performance Testing

This module tests database performance to ensure sub-200ms query requirements
are met for all critical operations. Used for validation and benchmarking.
"""

import asyncio
import logging
import time
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any
import statistics
import json

from .database_manager import create_document_manager, DocumentManager
from .models import Document


class PerformanceTest:
    """
    Comprehensive database performance testing suite.
    
    Tests all critical operations against sub-200ms performance targets
    and provides detailed performance metrics.
    """
    
    def __init__(self, database_path: str = None, logger: logging.Logger = None):
        """
        Initialize performance test.
        
        Args:
            database_path: Optional database path (uses temp file if None)
            logger: Optional logger instance
        """
        self.database_path = database_path or self._create_temp_database()
        self.logger = logger or self._setup_logger()
        self.manager: Optional[DocumentManager] = None
        self.test_results: Dict[str, Any] = {}
        
    def _create_temp_database(self) -> str:
        """Create temporary database file for testing."""
        temp_dir = tempfile.mkdtemp()
        return os.path.join(temp_dir, "test_performance.db")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for test output."""
        logger = logging.getLogger("performance_test")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def setup(self) -> bool:
        """Setup test environment."""
        try:
            self.logger.info(f"Setting up performance test with database: {self.database_path}")
            
            # Create document manager
            self.manager = await create_document_manager(
                database_path=self.database_path,
                logger=self.logger
            )
            
            if not self.manager:
                self.logger.error("Failed to create document manager")
                return False
            
            self.logger.info("Performance test setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Performance test setup failed: {e}")
            return False
    
    async def teardown(self) -> None:
        """Clean up test environment."""
        try:
            if self.manager:
                await self.manager.close()
            
            # Remove temporary database
            if os.path.exists(self.database_path):
                os.unlink(self.database_path)
            
            self.logger.info("Performance test cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Performance test cleanup failed: {e}")
    
    def _measure_time(self, func):
        """Decorator to measure function execution time."""
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                return result, execution_time
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                raise Exception(f"Test failed after {execution_time:.2f}ms: {e}")
        
        return wrapper
    
    async def test_document_indexing_performance(self, num_documents: int = 100) -> Dict[str, Any]:
        """
        Test document indexing performance.
        
        Args:
            num_documents: Number of documents to test with
            
        Returns:
            Performance metrics dictionary
        """
        self.logger.info(f"Testing document indexing performance with {num_documents} documents")
        
        times = []
        
        # Test document indexing
        for i in range(num_documents):
            document_content = self._generate_test_document(i, 500)  # 500 word documents
            
            start_time = time.time()
            document_id = await self.manager.index_document(
                file_path=f"/test/document_{i}.md",
                content=document_content,
                metadata={"test_id": str(i), "type": "test", "size": "medium"}
            )
            execution_time = (time.time() - start_time) * 1000
            
            if document_id:
                times.append(execution_time)
            else:
                self.logger.warning(f"Failed to index document {i}")
        
        # Calculate statistics
        if times:
            return {
                "operation": "document_indexing",
                "total_documents": num_documents,
                "successful_operations": len(times),
                "avg_time_ms": statistics.mean(times),
                "min_time_ms": min(times),
                "max_time_ms": max(times),
                "median_time_ms": statistics.median(times),
                "p95_time_ms": self._percentile(times, 95),
                "p99_time_ms": self._percentile(times, 99),
                "operations_under_200ms": len([t for t in times if t < 200]),
                "success_rate": (len(times) / num_documents) * 100,
                "meets_performance_target": max(times) < 1000,  # Allow 1s for indexing
            }
        else:
            return {"operation": "document_indexing", "error": "No successful operations"}
    
    async def test_search_performance(self, num_queries: int = 50) -> Dict[str, Any]:
        """
        Test search query performance.
        
        Args:
            num_queries: Number of search queries to test
            
        Returns:
            Performance metrics dictionary
        """
        self.logger.info(f"Testing search performance with {num_queries} queries")
        
        # First, ensure we have some documents to search
        await self.test_document_indexing_performance(50)
        
        # Test queries
        test_queries = [
            "test", "document", "content", "example", "sample",
            "performance", "database", "search", "index", "metadata",
            "file", "text", "data", "information", "system",
            "query", "results", "analysis", "processing", "management"
        ]
        
        times = []
        cache_times = []
        
        for i in range(num_queries):
            query = test_queries[i % len(test_queries)]
            if i > 20:  # Add some variation
                query = f"{query} document"
            
            # First query (cache miss)
            start_time = time.time()
            results = await self.manager.search_documents(query, limit=10, use_cache=False)
            execution_time = (time.time() - start_time) * 1000
            times.append(execution_time)
            
            # Second query (potential cache hit)
            start_time = time.time()
            cached_results = await self.manager.search_documents(query, limit=10, use_cache=True)
            cache_execution_time = (time.time() - start_time) * 1000
            cache_times.append(cache_execution_time)
        
        # Calculate statistics
        return {
            "operation": "search_queries",
            "total_queries": num_queries,
            "non_cached": {
                "avg_time_ms": statistics.mean(times),
                "min_time_ms": min(times),
                "max_time_ms": max(times),
                "median_time_ms": statistics.median(times),
                "p95_time_ms": self._percentile(times, 95),
                "p99_time_ms": self._percentile(times, 99),
                "queries_under_200ms": len([t for t in times if t < 200]),
                "meets_performance_target": self._percentile(times, 95) < 200,
            },
            "cached": {
                "avg_time_ms": statistics.mean(cache_times),
                "min_time_ms": min(cache_times),
                "max_time_ms": max(cache_times),
                "median_time_ms": statistics.median(cache_times),
                "p95_time_ms": self._percentile(cache_times, 95),
                "p99_time_ms": self._percentile(cache_times, 99),
                "queries_under_200ms": len([t for t in cache_times if t < 200]),
                "meets_performance_target": self._percentile(cache_times, 95) < 50,  # Cached should be very fast
            }
        }
    
    async def test_document_retrieval_performance(self, num_retrievals: int = 100) -> Dict[str, Any]:
        """
        Test document retrieval performance.
        
        Args:
            num_retrievals: Number of document retrievals to test
            
        Returns:
            Performance metrics dictionary
        """
        self.logger.info(f"Testing document retrieval performance with {num_retrievals} operations")
        
        # First, create some documents
        document_ids = []
        for i in range(min(50, num_retrievals)):
            content = self._generate_test_document(i, 300)
            doc_id = await self.manager.index_document(
                file_path=f"/test/retrieval_{i}.md",
                content=content
            )
            if doc_id:
                document_ids.append(doc_id)
        
        if not document_ids:
            return {"operation": "document_retrieval", "error": "No documents to retrieve"}
        
        # Test retrievals
        times = []
        
        for i in range(num_retrievals):
            doc_id = document_ids[i % len(document_ids)]
            
            start_time = time.time()
            document = await self.manager.get_document(doc_id, include_metadata=True)
            execution_time = (time.time() - start_time) * 1000
            
            if document:
                times.append(execution_time)
            else:
                self.logger.warning(f"Failed to retrieve document {doc_id}")
        
        # Calculate statistics
        if times:
            return {
                "operation": "document_retrieval",
                "total_retrievals": num_retrievals,
                "successful_operations": len(times),
                "avg_time_ms": statistics.mean(times),
                "min_time_ms": min(times),
                "max_time_ms": max(times),
                "median_time_ms": statistics.median(times),
                "p95_time_ms": self._percentile(times, 95),
                "p99_time_ms": self._percentile(times, 99),
                "operations_under_200ms": len([t for t in times if t < 200]),
                "success_rate": (len(times) / num_retrievals) * 100,
                "meets_performance_target": self._percentile(times, 95) < 200,
            }
        else:
            return {"operation": "document_retrieval", "error": "No successful operations"}
    
    async def test_concurrent_operations(self, num_concurrent: int = 10) -> Dict[str, Any]:
        """
        Test concurrent database operations.
        
        Args:
            num_concurrent: Number of concurrent operations
            
        Returns:
            Performance metrics dictionary
        """
        self.logger.info(f"Testing concurrent operations with {num_concurrent} tasks")
        
        # Define concurrent tasks
        async def concurrent_task(task_id: int):
            start_time = time.time()
            
            # Mix of operations
            tasks = []
            
            # Index a document
            content = self._generate_test_document(task_id, 200)
            doc_id = await self.manager.index_document(
                file_path=f"/concurrent/task_{task_id}.md",
                content=content
            )
            
            if doc_id:
                # Search for documents
                search_results = await self.manager.search_documents(f"task {task_id}")
                
                # Retrieve the document
                retrieved_doc = await self.manager.get_document(doc_id)
            
            execution_time = (time.time() - start_time) * 1000
            return execution_time, doc_id is not None
        
        # Run concurrent tasks
        start_time = time.time()
        results = await asyncio.gather(
            *[concurrent_task(i) for i in range(num_concurrent)],
            return_exceptions=True
        )
        total_time = (time.time() - start_time) * 1000
        
        # Process results
        successful_results = [r for r in results if not isinstance(r, Exception) and r[1]]
        times = [r[0] for r in successful_results]
        
        if times:
            return {
                "operation": "concurrent_operations",
                "total_tasks": num_concurrent,
                "successful_tasks": len(successful_results),
                "total_time_ms": total_time,
                "avg_task_time_ms": statistics.mean(times),
                "max_task_time_ms": max(times),
                "throughput_tasks_per_second": len(successful_results) / (total_time / 1000),
                "success_rate": (len(successful_results) / num_concurrent) * 100,
                "meets_performance_target": max(times) < 2000,  # Allow 2s for complex concurrent ops
            }
        else:
            return {"operation": "concurrent_operations", "error": "No successful operations"}
    
    async def run_full_performance_test(self) -> Dict[str, Any]:
        """
        Run comprehensive performance test suite.
        
        Returns:
            Complete performance test results
        """
        self.logger.info("Starting comprehensive performance test suite")
        
        # Run all performance tests
        test_results = {
            "test_started": time.time(),
            "database_path": self.database_path,
            "performance_targets": {
                "search_queries_p95": "< 200ms",
                "document_retrieval_p95": "< 200ms",
                "document_indexing_max": "< 1000ms",
                "concurrent_operations_max": "< 2000ms"
            },
            "results": {}
        }
        
        try:
            # Test document indexing
            indexing_results = await self.test_document_indexing_performance(100)
            test_results["results"]["document_indexing"] = indexing_results
            
            # Test search performance
            search_results = await self.test_search_performance(50)
            test_results["results"]["search_queries"] = search_results
            
            # Test document retrieval
            retrieval_results = await self.test_document_retrieval_performance(100)
            test_results["results"]["document_retrieval"] = retrieval_results
            
            # Test concurrent operations
            concurrent_results = await self.test_concurrent_operations(10)
            test_results["results"]["concurrent_operations"] = concurrent_results
            
            # Calculate overall performance score
            test_results["overall_performance"] = self._calculate_performance_score(test_results["results"])
            
            test_results["test_completed"] = time.time()
            test_results["total_test_time_seconds"] = test_results["test_completed"] - test_results["test_started"]
            
            self.logger.info("Performance test suite completed successfully")
            return test_results
            
        except Exception as e:
            self.logger.error(f"Performance test suite failed: {e}")
            test_results["error"] = str(e)
            return test_results
    
    def _generate_test_document(self, doc_id: int, word_count: int = 500) -> str:
        """Generate test document content."""
        words = [
            "document", "content", "test", "example", "sample", "data", "information",
            "system", "database", "search", "index", "query", "results", "analysis",
            "processing", "management", "performance", "optimization", "benchmark",
            "evaluation", "testing", "validation", "verification", "implementation"
        ]
        
        content_words = []
        for i in range(word_count):
            word = words[i % len(words)]
            if i % 50 == 0:
                word = f"{word}_{doc_id}"  # Add unique identifier
            content_words.append(word)
        
        return f"# Test Document {doc_id}\n\n" + " ".join(content_words)
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _calculate_performance_score(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall performance score."""
        score = {
            "total_score": 0,
            "max_score": 0,
            "details": {}
        }
        
        # Search performance (40% weight)
        if "search_queries" in results and "non_cached" in results["search_queries"]:
            search_data = results["search_queries"]["non_cached"]
            if search_data.get("meets_performance_target", False):
                search_score = 40
            else:
                # Partial score based on how close to target
                p95_time = search_data.get("p95_time_ms", 1000)
                search_score = max(0, 40 * (1 - (p95_time - 200) / 800))
            
            score["details"]["search_performance"] = {
                "score": search_score,
                "max_score": 40,
                "meets_target": search_data.get("meets_performance_target", False)
            }
            score["total_score"] += search_score
        score["max_score"] += 40
        
        # Retrieval performance (30% weight)
        if "document_retrieval" in results:
            retrieval_data = results["document_retrieval"]
            if retrieval_data.get("meets_performance_target", False):
                retrieval_score = 30
            else:
                p95_time = retrieval_data.get("p95_time_ms", 1000)
                retrieval_score = max(0, 30 * (1 - (p95_time - 200) / 800))
            
            score["details"]["retrieval_performance"] = {
                "score": retrieval_score,
                "max_score": 30,
                "meets_target": retrieval_data.get("meets_performance_target", False)
            }
            score["total_score"] += retrieval_score
        score["max_score"] += 30
        
        # Indexing performance (20% weight)
        if "document_indexing" in results:
            indexing_data = results["document_indexing"]
            if indexing_data.get("meets_performance_target", False):
                indexing_score = 20
            else:
                max_time = indexing_data.get("max_time_ms", 5000)
                indexing_score = max(0, 20 * (1 - (max_time - 1000) / 4000))
            
            score["details"]["indexing_performance"] = {
                "score": indexing_score,
                "max_score": 20,
                "meets_target": indexing_data.get("meets_performance_target", False)
            }
            score["total_score"] += indexing_score
        score["max_score"] += 20
        
        # Concurrent operations (10% weight)
        if "concurrent_operations" in results:
            concurrent_data = results["concurrent_operations"]
            if concurrent_data.get("meets_performance_target", False):
                concurrent_score = 10
            else:
                max_time = concurrent_data.get("max_task_time_ms", 10000)
                concurrent_score = max(0, 10 * (1 - (max_time - 2000) / 8000))
            
            score["details"]["concurrent_performance"] = {
                "score": concurrent_score,
                "max_score": 10,
                "meets_target": concurrent_data.get("meets_performance_target", False)
            }
            score["total_score"] += concurrent_score
        score["max_score"] += 10
        
        # Calculate percentage
        score["percentage"] = (score["total_score"] / score["max_score"]) * 100 if score["max_score"] > 0 else 0
        score["grade"] = self._get_performance_grade(score["percentage"])
        
        return score
    
    def _get_performance_grade(self, percentage: float) -> str:
        """Convert percentage to letter grade."""
        if percentage >= 95:
            return "A+"
        elif percentage >= 90:
            return "A"
        elif percentage >= 85:
            return "B+"
        elif percentage >= 80:
            return "B"
        elif percentage >= 75:
            return "C+"
        elif percentage >= 70:
            return "C"
        else:
            return "F"


async def run_performance_test(database_path: str = None) -> Dict[str, Any]:
    """
    Run performance test and return results.
    
    Args:
        database_path: Optional database path (uses temp if None)
        
    Returns:
        Performance test results
    """
    test = PerformanceTest(database_path)
    
    try:
        # Setup
        success = await test.setup()
        if not success:
            return {"error": "Failed to setup performance test"}
        
        # Run tests
        results = await test.run_full_performance_test()
        
        return results
        
    finally:
        # Cleanup
        await test.teardown()


if __name__ == "__main__":
    async def main():
        """Main function for running performance tests."""
        print("Running mydocs-mcp Database Performance Test...")
        print("=" * 60)
        
        results = await run_performance_test()
        
        if "error" in results:
            print(f"ERROR: {results['error']}")
            return
        
        # Print summary
        print("\nPerformance Test Summary:")
        print("-" * 40)
        
        if "overall_performance" in results:
            score = results["overall_performance"]
            print(f"Overall Score: {score['total_score']:.1f}/{score['max_score']} ({score['percentage']:.1f}%)")
            print(f"Performance Grade: {score['grade']}")
            print()
        
        # Print detailed results
        for operation, data in results.get("results", {}).items():
            print(f"{operation.replace('_', ' ').title()}:")
            
            if operation == "search_queries" and "non_cached" in data:
                stats = data["non_cached"]
                print(f"  P95 Time: {stats.get('p95_time_ms', 0):.2f}ms")
                print(f"  Queries < 200ms: {stats.get('queries_under_200ms', 0)}")
                print(f"  Meets Target: {stats.get('meets_performance_target', False)}")
            elif "p95_time_ms" in data:
                print(f"  P95 Time: {data.get('p95_time_ms', 0):.2f}ms")
                print(f"  Operations < 200ms: {data.get('operations_under_200ms', 0)}")
                print(f"  Meets Target: {data.get('meets_performance_target', False)}")
            elif "max_task_time_ms" in data:
                print(f"  Max Task Time: {data.get('max_task_time_ms', 0):.2f}ms")
                print(f"  Throughput: {data.get('throughput_tasks_per_second', 0):.2f} ops/sec")
                print(f"  Meets Target: {data.get('meets_performance_target', False)}")
            
            print()
        
        print("Performance test completed!")
    
    asyncio.run(main())