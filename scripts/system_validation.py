#!/usr/bin/env python3
"""
mydocs-mcp Day 2 System Validation Script

Comprehensive system health check and validation for Day 2 completion.
Tests all major components and their integration.
"""

import asyncio
import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
import json

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.database_manager import DocumentManager
from database.connection import get_database_connection
from tools.indexDocument import IndexDocumentTool
from tools.searchDocuments import SearchDocumentsTool  
from tools.getDocument import GetDocumentTool
from parsers.parser_factory import ParserFactory
from watcher.file_watcher import FileWatcher
import logging_config

# Configure logging
logger = logging_config.setup_logging()

class SystemValidator:
    """Comprehensive system validation for Day 2 completion."""
    
    def __init__(self):
        self.test_results = []
        self.performance_metrics = {}
        self.temp_dir = None
        self.db_connection = None
        self.document_manager = None
        
    async def setup_test_environment(self):
        """Set up temporary test environment."""
        logger.info("Setting up test environment...")
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="mydocs_validation_"))
        logger.info(f"Test directory: {self.temp_dir}")
        
        # Create test database
        db_path = self.temp_dir / "test_validation.db"
        self.db_connection = await get_database_connection(str(db_path))
        self.document_manager = DocumentManager(self.db_connection)
        
        # Create test documents
        test_docs_dir = self.temp_dir / "documents"
        test_docs_dir.mkdir()
        
        # Sample document 1
        (test_docs_dir / "test_doc1.md").write_text("""
# AI and Machine Learning Guide

This document contains information about artificial intelligence and machine learning concepts.

## Key Topics
- Neural networks
- Deep learning
- Natural language processing

The future of AI looks promising with advances in transformer architectures.
""")
        
        # Sample document 2
        (test_docs_dir / "test_doc2.txt").write_text("""
Project Management Best Practices

This file outlines essential project management methodologies:

1. Agile development practices
2. Scrum framework implementation  
3. Kanban workflow optimization
4. Risk assessment and mitigation

Effective project management requires clear communication and stakeholder alignment.
""")
        
        # Sample document 3
        (test_docs_dir / "test_doc3.md").write_text("""
---
title: Python Programming Tutorial
author: Test Author
date: 2025-09-03
tags: [python, programming, tutorial]
---

# Python Programming Tutorial

## Introduction
Python is a versatile programming language used for:
- Web development
- Data science
- Machine learning
- Automation scripts

## Code Examples
```python
def hello_world():
    print("Hello, World!")
```

Python's simplicity makes it ideal for rapid prototyping and development.
""")
        
        logger.info("Test environment setup complete")
        
    async def cleanup_test_environment(self):
        """Clean up test environment."""
        if self.db_connection:
            await self.db_connection.close()
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        logger.info("Test environment cleaned up")
        
    def record_test_result(self, test_name: str, passed: bool, details: str = "", performance: float = None):
        """Record test result."""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": time.time()
        }
        if performance is not None:
            result["performance_ms"] = performance
            self.performance_metrics[test_name] = performance
            
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        perf_info = f" ({performance:.2f}ms)" if performance else ""
        logger.info(f"{status}: {test_name}{perf_info}")
        if details:
            logger.info(f"  Details: {details}")
            
    async def test_database_functionality(self):
        """Test database operations."""
        logger.info("Testing database functionality...")
        
        try:
            # Test database initialization
            start_time = time.time()
            await self.document_manager.initialize_database()
            init_time = (time.time() - start_time) * 1000
            
            self.record_test_result(
                "Database Initialization", 
                True, 
                "Database initialized successfully",
                init_time
            )
            
            # Test document insertion
            start_time = time.time()
            doc_id = await self.document_manager.add_document(
                file_path=str(self.temp_dir / "documents" / "test_doc1.md"),
                title="Test Document 1",
                content="Test content for validation",
                metadata={"test": "true"}
            )
            insert_time = (time.time() - start_time) * 1000
            
            self.record_test_result(
                "Document Insertion",
                doc_id is not None,
                f"Document ID: {doc_id}",
                insert_time
            )
            
            # Test document retrieval
            start_time = time.time()
            retrieved_doc = await self.document_manager.get_document_by_id(doc_id)
            retrieval_time = (time.time() - start_time) * 1000
            
            self.record_test_result(
                "Document Retrieval",
                retrieved_doc is not None,
                f"Retrieved document: {retrieved_doc.title if retrieved_doc else 'None'}",
                retrieval_time
            )
            
        except Exception as e:
            self.record_test_result("Database Functionality", False, str(e))
            
    async def test_document_parsers(self):
        """Test document parser functionality."""
        logger.info("Testing document parsers...")
        
        try:
            parser_factory = ParserFactory()
            
            # Test Markdown parser
            md_file = self.temp_dir / "documents" / "test_doc3.md"
            start_time = time.time()
            md_parser = parser_factory.get_parser(str(md_file))
            parsed_doc = await md_parser.parse(str(md_file))
            md_parse_time = (time.time() - start_time) * 1000
            
            self.record_test_result(
                "Markdown Parser",
                parsed_doc is not None and parsed_doc.title == "Python Programming Tutorial",
                f"Parsed title: {parsed_doc.title if parsed_doc else 'None'}",
                md_parse_time
            )
            
            # Test Text parser  
            txt_file = self.temp_dir / "documents" / "test_doc2.txt"
            start_time = time.time()
            txt_parser = parser_factory.get_parser(str(txt_file))
            parsed_txt = await txt_parser.parse(str(txt_file))
            txt_parse_time = (time.time() - start_time) * 1000
            
            self.record_test_result(
                "Text Parser", 
                parsed_txt is not None and len(parsed_txt.content) > 0,
                f"Content length: {len(parsed_txt.content) if parsed_txt else 0}",
                txt_parse_time
            )
            
        except Exception as e:
            self.record_test_result("Document Parsers", False, str(e))
            
    async def test_mcp_tools(self):
        """Test all three core MCP tools."""
        logger.info("Testing MCP tools...")
        
        try:
            # Initialize tools
            index_tool = IndexDocumentTool(self.document_manager, logger)
            search_tool = SearchDocumentsTool(self.document_manager, logger)
            get_tool = GetDocumentTool(self.document_manager, logger)
            
            # Test indexDocument tool
            start_time = time.time()
            index_result = await index_tool.execute({
                "file_path": str(self.temp_dir / "documents" / "test_doc1.md")
            })
            index_time = (time.time() - start_time) * 1000
            
            self.record_test_result(
                "indexDocument Tool",
                index_result.get("success", False),
                index_result.get("message", "No message"),
                index_time
            )
            
            # Wait a moment for indexing to complete
            await asyncio.sleep(0.1)
            
            # Test searchDocuments tool
            start_time = time.time()
            search_result = await search_tool.execute({
                "query": "machine learning",
                "limit": 10
            })
            search_time = (time.time() - start_time) * 1000
            
            self.record_test_result(
                "searchDocuments Tool",
                isinstance(search_result.get("documents"), list),
                f"Found {len(search_result.get('documents', []))} documents",
                search_time
            )
            
            # Test getDocument tool (if we have indexed documents)
            if search_result.get("documents"):
                doc_id = search_result["documents"][0].get("id")
                start_time = time.time()
                get_result = await get_tool.execute({
                    "document_id": str(doc_id)
                })
                get_time = (time.time() - start_time) * 1000
                
                self.record_test_result(
                    "getDocument Tool",
                    get_result.get("success", False),
                    f"Retrieved document: {get_result.get('document', {}).get('title', 'Unknown')}",
                    get_time
                )
            
        except Exception as e:
            self.record_test_result("MCP Tools", False, str(e))
            
    async def test_performance_requirements(self):
        """Validate performance requirements."""
        logger.info("Testing performance requirements...")
        
        # Check all recorded performance metrics
        for test_name, performance_ms in self.performance_metrics.items():
            if "Tool" in test_name:
                # MCP tools should be < 200ms
                passed = performance_ms < 200
                self.record_test_result(
                    f"Performance: {test_name}",
                    passed,
                    f"Target: <200ms, Actual: {performance_ms:.2f}ms"
                )
            elif "Database" in test_name:
                # Database operations should be < 200ms 
                passed = performance_ms < 200
                self.record_test_result(
                    f"Performance: {test_name}",
                    passed,
                    f"Target: <200ms, Actual: {performance_ms:.2f}ms"
                )
            elif "Parser" in test_name:
                # Parsing should be < 500ms
                passed = performance_ms < 500
                self.record_test_result(
                    f"Performance: {test_name}",
                    passed,
                    f"Target: <500ms, Actual: {performance_ms:.2f}ms"
                )
                
    async def test_integration_workflow(self):
        """Test complete end-to-end workflow."""
        logger.info("Testing end-to-end integration workflow...")
        
        try:
            # Complete workflow: Index → Search → Retrieve
            tools = {
                "index": IndexDocumentTool(self.document_manager, logger),
                "search": SearchDocumentsTool(self.document_manager, logger), 
                "get": GetDocumentTool(self.document_manager, logger)
            }
            
            # Step 1: Index all test documents
            doc_files = list((self.temp_dir / "documents").glob("*.md")) + list((self.temp_dir / "documents").glob("*.txt"))
            indexed_count = 0
            
            for doc_file in doc_files:
                result = await tools["index"].execute({"file_path": str(doc_file)})
                if result.get("success"):
                    indexed_count += 1
                    
            self.record_test_result(
                "Integration: Document Indexing",
                indexed_count == len(doc_files),
                f"Indexed {indexed_count}/{len(doc_files)} documents"
            )
            
            # Step 2: Search for documents
            search_result = await tools["search"].execute({
                "query": "python programming",
                "limit": 5
            })
            
            found_docs = search_result.get("documents", [])
            self.record_test_result(
                "Integration: Document Search",
                len(found_docs) > 0,
                f"Found {len(found_docs)} relevant documents"
            )
            
            # Step 3: Retrieve specific document
            if found_docs:
                doc_id = found_docs[0].get("id")
                get_result = await tools["get"].execute({"document_id": str(doc_id)})
                
                self.record_test_result(
                    "Integration: Document Retrieval", 
                    get_result.get("success", False),
                    f"Successfully retrieved document: {get_result.get('document', {}).get('title', 'Unknown')}"
                )
                
            # Overall integration test
            self.record_test_result(
                "End-to-End Integration",
                indexed_count > 0 and len(found_docs) > 0,
                "Complete workflow: Index → Search → Retrieve validated"
            )
            
        except Exception as e:
            self.record_test_result("Integration Workflow", False, str(e))
            
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test["passed"])
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Performance summary
        perf_summary = {}
        for category in ["Tool", "Database", "Parser"]:
            category_metrics = {k: v for k, v in self.performance_metrics.items() if category.lower() in k.lower()}
            if category_metrics:
                perf_summary[category] = {
                    "avg_ms": sum(category_metrics.values()) / len(category_metrics),
                    "max_ms": max(category_metrics.values()),
                    "count": len(category_metrics)
                }
        
        report = {
            "validation_timestamp": time.time(),
            "overall_status": "PASS" if pass_rate >= 75 else "FAIL",
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "pass_rate": f"{pass_rate:.1f}%"
            },
            "performance_summary": perf_summary,
            "detailed_results": self.test_results,
            "day2_readiness": {
                "core_functionality": passed_tests >= 8,  # Minimum 8 core tests passing
                "performance_targets": all(
                    perf < 200 for perf in self.performance_metrics.values()
                    if "tool" in perf or "database" in perf
                ),
                "integration_complete": any(
                    test["test_name"] == "End-to-End Integration" and test["passed"]
                    for test in self.test_results
                )
            }
        }
        
        return report
        
    async def run_validation(self):
        """Run complete system validation."""
        logger.info("🚀 Starting mydocs-mcp Day 2 System Validation...")
        
        try:
            await self.setup_test_environment()
            
            # Run all validation tests
            await self.test_database_functionality()
            await self.test_document_parsers()
            await self.test_mcp_tools()
            await self.test_integration_workflow()
            await self.test_performance_requirements()
            
            # Generate final report
            report = self.generate_validation_report()
            
            # Print summary
            logger.info(f"\n{'='*60}")
            logger.info("📊 VALIDATION SUMMARY")
            logger.info(f"{'='*60}")
            logger.info(f"Overall Status: {report['overall_status']}")
            logger.info(f"Test Results: {report['test_summary']['passed_tests']}/{report['test_summary']['total_tests']} passed ({report['test_summary']['pass_rate']})")
            
            logger.info(f"\n🎯 DAY 2 READINESS ASSESSMENT:")
            readiness = report["day2_readiness"]
            logger.info(f"✅ Core Functionality: {'READY' if readiness['core_functionality'] else 'NOT READY'}")
            logger.info(f"⚡ Performance Targets: {'MET' if readiness['performance_targets'] else 'NOT MET'}")
            logger.info(f"🔗 Integration Complete: {'YES' if readiness['integration_complete'] else 'NO'}")
            
            # Performance highlights
            if report["performance_summary"]:
                logger.info(f"\n⚡ PERFORMANCE HIGHLIGHTS:")
                for category, metrics in report["performance_summary"].items():
                    logger.info(f"{category}: Avg {metrics['avg_ms']:.1f}ms, Max {metrics['max_ms']:.1f}ms")
            
            day2_ready = all(readiness.values())
            logger.info(f"\n🚀 DAY 2 COMPLETION STATUS: {'✅ COMPLETE' if day2_ready else '⚠️ NEEDS ATTENTION'}")
            
            return report
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"status": "ERROR", "error": str(e)}
        finally:
            await self.cleanup_test_environment()

async def main():
    """Main validation entry point."""
    validator = SystemValidator()
    report = await validator.run_validation()
    
    # Save report to file
    report_file = Path(__file__).parent.parent / "tests" / "SYSTEM_VALIDATION_REPORT.md"
    
    with open(report_file, "w") as f:
        f.write(f"# mydocs-mcp System Validation Report\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Status**: {report.get('overall_status', 'UNKNOWN')}\n\n")
        
        if "test_summary" in report:
            f.write(f"## Test Summary\n")
            f.write(f"- **Total Tests**: {report['test_summary']['total_tests']}\n")
            f.write(f"- **Passed**: {report['test_summary']['passed_tests']}\n") 
            f.write(f"- **Failed**: {report['test_summary']['failed_tests']}\n")
            f.write(f"- **Pass Rate**: {report['test_summary']['pass_rate']}\n\n")
        
        if "day2_readiness" in report:
            f.write(f"## Day 2 Readiness\n")
            readiness = report["day2_readiness"]
            f.write(f"- **Core Functionality**: {'✅ Ready' if readiness['core_functionality'] else '❌ Not Ready'}\n")
            f.write(f"- **Performance Targets**: {'✅ Met' if readiness['performance_targets'] else '❌ Not Met'}\n")
            f.write(f"- **Integration Complete**: {'✅ Yes' if readiness['integration_complete'] else '❌ No'}\n\n")
        
        if "detailed_results" in report:
            f.write(f"## Detailed Results\n")
            for test in report["detailed_results"]:
                status = "✅ PASS" if test["passed"] else "❌ FAIL"
                f.write(f"- **{test['test_name']}**: {status}")
                if "performance_ms" in test:
                    f.write(f" ({test['performance_ms']:.2f}ms)")
                if test["details"]:
                    f.write(f" - {test['details']}")
                f.write(f"\n")
    
    print(f"\n📋 Full validation report saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())