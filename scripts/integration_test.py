#!/usr/bin/env python3
"""
mydocs-mcp Integration Test

Simple integration test to validate the complete workflow:
Parser → Database → Tools → Search → Retrieve
"""

import asyncio
import tempfile
import shutil
import os
import sys
import time
from pathlib import Path

# Add src to Python path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Direct imports to avoid relative import issues
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "parsers"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "tools"))

from database_manager import DocumentManager
from connection import get_database_connection
from parser_factory import ParserFactory
from base import BaseMCPTool
import logging_config

# Configure logging
logger = logging_config.setup_logging()

class SimpleIntegrationTest:
    """Simple integration test for Day 2 completion validation."""
    
    def __init__(self):
        self.temp_dir = None
        self.db_connection = None
        self.document_manager = None
        self.test_results = []
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({"name": test_name, "passed": passed, "details": details})
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"  Details: {details}")
    
    async def setup(self):
        """Setup test environment."""
        logger.info("Setting up integration test environment...")
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="mydocs_integration_"))
        
        # Create database
        db_path = self.temp_dir / "integration_test.db"
        self.db_connection = await get_database_connection(str(db_path))
        self.document_manager = DocumentManager(self.db_connection)
        
        # Initialize database
        await self.document_manager.initialize_database()
        
        # Create test documents
        docs_dir = self.temp_dir / "documents"
        docs_dir.mkdir()
        
        # Test document 1 (Markdown)
        (docs_dir / "test1.md").write_text("""# Integration Test Document
        
This is a test document for integration validation.

## Keywords
- integration
- testing
- validation

The document contains relevant content for search testing.
""")
        
        # Test document 2 (Text)
        (docs_dir / "test2.txt").write_text("""Integration Test Text File

This file contains text content for testing the complete integration workflow.

Key terms: integration, workflow, testing, complete validation
""")
        
        logger.info(f"Test environment ready: {self.temp_dir}")
        
    async def cleanup(self):
        """Clean up test environment."""
        if self.db_connection:
            await self.db_connection.close()
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    async def test_parser_integration(self):
        """Test parser integration with documents."""
        logger.info("Testing parser integration...")
        
        try:
            parser_factory = ParserFactory()
            
            # Test Markdown parsing
            md_file = self.temp_dir / "documents" / "test1.md"
            md_parser = parser_factory.get_parser(str(md_file))
            parsed_md = await md_parser.parse(str(md_file))
            
            self.log_result(
                "Markdown Parser Integration",
                parsed_md is not None and len(parsed_md.content) > 0,
                f"Parsed content length: {len(parsed_md.content) if parsed_md else 0}"
            )
            
            # Test Text parsing
            txt_file = self.temp_dir / "documents" / "test2.txt"
            txt_parser = parser_factory.get_parser(str(txt_file))
            parsed_txt = await txt_parser.parse(str(txt_file))
            
            self.log_result(
                "Text Parser Integration", 
                parsed_txt is not None and len(parsed_txt.content) > 0,
                f"Parsed content length: {len(parsed_txt.content) if parsed_txt else 0}"
            )
            
        except Exception as e:
            self.log_result("Parser Integration", False, str(e))
            
    async def test_database_integration(self):
        """Test database integration."""
        logger.info("Testing database integration...")
        
        try:
            # Test document insertion
            doc_id = await self.document_manager.add_document(
                file_path="/test/integration.md",
                title="Integration Test",
                content="This is test content for database integration.",
                metadata={"test": "integration"}
            )
            
            self.log_result(
                "Database Document Insertion",
                doc_id is not None,
                f"Document ID: {doc_id}"
            )
            
            # Test document retrieval
            retrieved_doc = await self.document_manager.get_document_by_id(doc_id)
            
            self.log_result(
                "Database Document Retrieval",
                retrieved_doc is not None and retrieved_doc.title == "Integration Test",
                f"Retrieved: {retrieved_doc.title if retrieved_doc else 'None'}"
            )
            
            # Test search functionality
            search_results = await self.document_manager.search_documents("integration")
            
            self.log_result(
                "Database Search Integration",
                len(search_results) > 0,
                f"Found {len(search_results)} documents"
            )
            
        except Exception as e:
            self.log_result("Database Integration", False, str(e))
            
    async def test_tool_integration(self):
        """Test MCP tool integration without actual MCP tools."""
        logger.info("Testing tool-like integration...")
        
        try:
            # Simulate tool workflow using document manager directly
            
            # 1. Index documents (simulate indexDocument tool)
            parser_factory = ParserFactory()
            indexed_count = 0
            
            for doc_file in (self.temp_dir / "documents").glob("*"):
                try:
                    parser = parser_factory.get_parser(str(doc_file))
                    parsed_doc = await parser.parse(str(doc_file))
                    
                    doc_id = await self.document_manager.add_document(
                        file_path=str(doc_file),
                        title=parsed_doc.title or doc_file.name,
                        content=parsed_doc.content,
                        metadata=parsed_doc.metadata or {}
                    )
                    
                    if doc_id:
                        indexed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to index {doc_file}: {e}")
                    
            self.log_result(
                "Tool Integration - Document Indexing",
                indexed_count > 0,
                f"Indexed {indexed_count} documents"
            )
            
            # 2. Search documents (simulate searchDocuments tool)
            search_results = await self.document_manager.search_documents("integration testing")
            
            self.log_result(
                "Tool Integration - Document Search",
                len(search_results) > 0,
                f"Found {len(search_results)} documents matching 'integration testing'"
            )
            
            # 3. Get document (simulate getDocument tool)
            if search_results:
                doc_id = search_results[0].id
                retrieved_doc = await self.document_manager.get_document_by_id(doc_id)
                
                self.log_result(
                    "Tool Integration - Document Retrieval",
                    retrieved_doc is not None,
                    f"Retrieved document: {retrieved_doc.title if retrieved_doc else 'None'}"
                )
            
        except Exception as e:
            self.log_result("Tool Integration", False, str(e))
            
    async def test_performance_integration(self):
        """Test performance requirements in integrated workflow."""
        logger.info("Testing performance in integrated workflow...")
        
        try:
            # Test search performance
            start_time = time.perf_counter()
            search_results = await self.document_manager.search_documents("test", limit=10)
            search_time = (time.perf_counter() - start_time) * 1000
            
            self.log_result(
                "Integration Performance - Search",
                search_time < 200,
                f"Search took {search_time:.2f}ms (target: <200ms)"
            )
            
            # Test retrieval performance (if we have documents)
            if search_results:
                doc_id = search_results[0].id
                start_time = time.perf_counter()
                document = await self.document_manager.get_document_by_id(doc_id)
                retrieval_time = (time.perf_counter() - start_time) * 1000
                
                self.log_result(
                    "Integration Performance - Retrieval",
                    retrieval_time < 200,
                    f"Retrieval took {retrieval_time:.2f}ms (target: <200ms)"
                )
            
        except Exception as e:
            self.log_result("Performance Integration", False, str(e))
            
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        logger.info("Testing complete end-to-end workflow...")
        
        try:
            # Complete workflow: Parse → Index → Search → Retrieve
            
            # Step 1: Parse document
            parser_factory = ParserFactory()
            test_file = self.temp_dir / "documents" / "test1.md"
            parser = parser_factory.get_parser(str(test_file))
            parsed_doc = await parser.parse(str(test_file))
            
            # Step 2: Index document
            doc_id = await self.document_manager.add_document(
                file_path=str(test_file),
                title=parsed_doc.title,
                content=parsed_doc.content,
                metadata=parsed_doc.metadata or {}
            )
            
            # Step 3: Search for document
            search_results = await self.document_manager.search_documents("Integration Test Document")
            
            # Step 4: Retrieve document
            if search_results:
                retrieved_doc = await self.document_manager.get_document_by_id(search_results[0].id)
                
                self.log_result(
                    "End-to-End Workflow",
                    (doc_id is not None and 
                     len(search_results) > 0 and 
                     retrieved_doc is not None and 
                     "Integration Test Document" in retrieved_doc.title),
                    "Complete workflow: Parse → Index → Search → Retrieve"
                )
            else:
                self.log_result("End-to-End Workflow", False, "Search failed to find indexed document")
                
        except Exception as e:
            self.log_result("End-to-End Workflow", False, str(e))
            
    def generate_summary(self):
        """Generate test summary."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test["passed"])
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"\n{'='*60}")
        logger.info("📊 INTEGRATION TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Pass Rate: {pass_rate:.1f}%")
        
        overall_status = "PASS" if pass_rate >= 75 else "FAIL"
        logger.info(f"Overall Status: {overall_status}")
        
        if total_tests - passed_tests > 0:
            logger.info(f"\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test["passed"]:
                    logger.info(f"  - {test['name']}: {test['details']}")
                    
        logger.info(f"\n🎯 INTEGRATION READINESS: {'✅ READY' if overall_status == 'PASS' else '⚠️ NEEDS ATTENTION'}")
        
        return {
            "overall_status": overall_status,
            "pass_rate": pass_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "detailed_results": self.test_results
        }
        
    async def run_integration_tests(self):
        """Run all integration tests."""
        logger.info("🚀 Starting mydocs-mcp Integration Tests...")
        
        try:
            await self.setup()
            
            # Run all integration tests
            await self.test_parser_integration()
            await self.test_database_integration()
            await self.test_tool_integration()
            await self.test_performance_integration()
            await self.test_end_to_end_workflow()
            
            # Generate summary
            summary = self.generate_summary()
            
            return summary
            
        finally:
            await self.cleanup()

async def main():
    """Main integration test entry point."""
    tester = SimpleIntegrationTest()
    summary = await tester.run_integration_tests()
    
    # Save results
    report_file = Path(__file__).parent.parent / "tests" / "INTEGRATION_TEST_REPORT.md"
    
    with open(report_file, "w") as f:
        f.write(f"# mydocs-mcp Integration Test Report\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Status**: {summary['overall_status']}\n\n")
        
        f.write(f"## Summary\n")
        f.write(f"- **Total Tests**: {summary['total_tests']}\n")
        f.write(f"- **Passed**: {summary['passed_tests']}\n")
        f.write(f"- **Failed**: {summary['failed_tests']}\n")
        f.write(f"- **Pass Rate**: {summary['pass_rate']:.1f}%\n\n")
        
        f.write(f"## Detailed Results\n")
        for test in summary["detailed_results"]:
            status = "✅ PASS" if test["passed"] else "❌ FAIL"
            f.write(f"- **{test['name']}**: {status}")
            if test["details"]:
                f.write(f" - {test['details']}")
            f.write(f"\n")
    
    print(f"\n📋 Integration test report saved to: {report_file}")
    return summary

if __name__ == "__main__":
    asyncio.run(main())