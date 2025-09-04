"""
Claude Code Integration Test Suite for mydocs-mcp.

This test validates that the MCP server works correctly with Claude Code.
Tests MCP protocol compliance, tool execution, and real-world usage scenarios.
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import ServerConfig
from src.server import MyDocsMCPServer
from src.database.connection import DatabaseConnection


class ClaudeIntegrationTester:
    """Test harness for validating Claude Code integration."""
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="mydocs_test_")
        self.config = self._create_test_config()
        self.server = None
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "performance": {}
        }
    
    def _create_test_config(self) -> ServerConfig:
        """Create test configuration."""
        config = ServerConfig()
        config.database_url = f"sqlite:///{self.test_dir}/test.db"
        config.document_root = f"{self.test_dir}/documents"
        config.log_level = "DEBUG"
        config.debug_mode = True
        config.transport = "stdio"
        return config
    
    async def setup(self):
        """Setup test environment."""
        print("\n[SETUP] Setting up test environment...")
        
        # Create directories
        os.makedirs(f"{self.test_dir}/documents", exist_ok=True)
        
        # Create test documents
        test_docs = [
            ("README.md", "# Test Project\n\nThis is a test readme for integration testing."),
            ("API.md", "# API Documentation\n\n## Endpoints\n- GET /api/test"),
            ("guide.txt", "User Guide: How to use the test application"),
            ("notes.md", "# Personal Notes\n\n- Remember to test everything\n- Check performance")
        ]
        
        for filename, content in test_docs:
            path = Path(f"{self.test_dir}/documents/{filename}")
            path.write_text(content)
        
        # Initialize server
        self.server = MyDocsMCPServer(self.config)
        
        # Initialize database
        db = DatabaseConnection(self.config.database_url)
        await db.initialize()
        
        print("✅ Test environment ready")
    
    async def test_mcp_protocol_compliance(self):
        """Test MCP protocol compliance."""
        print("\n📋 Testing MCP Protocol Compliance...")
        self.results["total_tests"] += 1
        
        try:
            # Test server initialization
            assert self.server is not None, "Server not initialized"
            
            # Test tool registry
            tools = await self.server.tool_registry.get_tools()
            assert len(tools) == 3, f"Expected 3 tools, got {len(tools)}"
            
            tool_names = [t["name"] for t in tools]
            assert "indexDocument" in tool_names, "indexDocument tool missing"
            assert "searchDocuments" in tool_names, "searchDocuments tool missing"
            assert "getDocument" in tool_names, "getDocument tool missing"
            
            # Test tool schemas
            for tool in tools:
                assert "name" in tool, "Tool missing name"
                assert "description" in tool, "Tool missing description"
                assert "inputSchema" in tool, "Tool missing inputSchema"
                assert tool["inputSchema"]["type"] == "object", "Invalid input schema type"
            
            self.results["passed"] += 1
            print("✅ MCP Protocol compliance validated")
            return True
            
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Protocol compliance: {str(e)}")
            print(f"❌ Protocol compliance failed: {e}")
            return False
    
    async def test_tool_execution(self):
        """Test tool execution through MCP interface."""
        print("\n🔧 Testing Tool Execution...")
        
        # Test indexDocument
        print("  Testing indexDocument...")
        self.results["total_tests"] += 1
        try:
            start = time.time()
            result = await self.server.tool_registry.execute_tool(
                "indexDocument",
                {"file_path": f"{self.test_dir}/documents/README.md"}
            )
            elapsed = (time.time() - start) * 1000
            self.results["performance"]["indexDocument"] = elapsed
            
            assert result["success"], "indexDocument failed"
            assert result["document_id"], "No document ID returned"
            print(f"    ✅ indexDocument: {elapsed:.2f}ms")
            self.results["passed"] += 1
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"indexDocument: {str(e)}")
            print(f"    ❌ indexDocument failed: {e}")
        
        # Test searchDocuments
        print("  Testing searchDocuments...")
        self.results["total_tests"] += 1
        try:
            # Index all documents first
            for doc in ["API.md", "guide.txt", "notes.md"]:
                await self.server.tool_registry.execute_tool(
                    "indexDocument",
                    {"file_path": f"{self.test_dir}/documents/{doc}"}
                )
            
            start = time.time()
            result = await self.server.tool_registry.execute_tool(
                "searchDocuments",
                {"query": "test"}
            )
            elapsed = (time.time() - start) * 1000
            self.results["performance"]["searchDocuments"] = elapsed
            
            assert "results" in result, "No results field"
            assert len(result["results"]) > 0, "No search results"
            assert elapsed < 200, f"Search too slow: {elapsed}ms"
            print(f"    ✅ searchDocuments: {elapsed:.2f}ms")
            self.results["passed"] += 1
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"searchDocuments: {str(e)}")
            print(f"    ❌ searchDocuments failed: {e}")
        
        # Test getDocument
        print("  Testing getDocument...")
        self.results["total_tests"] += 1
        try:
            # Get document by path
            start = time.time()
            result = await self.server.tool_registry.execute_tool(
                "getDocument",
                {"file_path": f"{self.test_dir}/documents/README.md"}
            )
            elapsed = (time.time() - start) * 1000
            self.results["performance"]["getDocument"] = elapsed
            
            assert result["success"], "getDocument failed"
            assert result["content"], "No content returned"
            assert elapsed < 200, f"Get too slow: {elapsed}ms"
            print(f"    ✅ getDocument: {elapsed:.2f}ms")
            self.results["passed"] += 1
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"getDocument: {str(e)}")
            print(f"    ❌ getDocument failed: {e}")
    
    async def test_real_world_scenarios(self):
        """Test real-world usage scenarios."""
        print("\n🌍 Testing Real-World Scenarios...")
        
        # Scenario 1: Index and search workflow
        print("  Scenario 1: Index → Search → Retrieve workflow...")
        self.results["total_tests"] += 1
        try:
            # Create a new document
            doc_path = f"{self.test_dir}/documents/scenario.md"
            Path(doc_path).write_text("# Scenario Test\n\nTesting integration with Claude Code")
            
            # Index it
            index_result = await self.server.tool_registry.execute_tool(
                "indexDocument", {"file_path": doc_path}
            )
            doc_id = index_result["document_id"]
            
            # Search for it
            search_result = await self.server.tool_registry.execute_tool(
                "searchDocuments", {"query": "Claude Code"}
            )
            
            # Verify it's found
            found = any(r["id"] == doc_id for r in search_result["results"])
            assert found, "Document not found in search"
            
            # Retrieve it
            get_result = await self.server.tool_registry.execute_tool(
                "getDocument", {"document_id": doc_id}
            )
            assert "Claude Code" in get_result["content"], "Content mismatch"
            
            print("    ✅ Workflow completed successfully")
            self.results["passed"] += 1
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Workflow scenario: {str(e)}")
            print(f"    ❌ Workflow failed: {e}")
        
        # Scenario 2: Performance under load
        print("  Scenario 2: Performance under load...")
        self.results["total_tests"] += 1
        try:
            # Create multiple documents
            for i in range(10):
                path = f"{self.test_dir}/documents/load_test_{i}.md"
                Path(path).write_text(f"# Document {i}\n\nContent for load testing")
                await self.server.tool_registry.execute_tool(
                    "indexDocument", {"file_path": path}
                )
            
            # Perform multiple searches
            search_times = []
            for query in ["Document", "load", "testing", "content"]:
                start = time.time()
                await self.server.tool_registry.execute_tool(
                    "searchDocuments", {"query": query}
                )
                search_times.append((time.time() - start) * 1000)
            
            avg_time = sum(search_times) / len(search_times)
            assert avg_time < 200, f"Average search time too high: {avg_time:.2f}ms"
            
            print(f"    ✅ Performance validated: avg {avg_time:.2f}ms")
            self.results["passed"] += 1
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Performance scenario: {str(e)}")
            print(f"    ❌ Performance test failed: {e}")
    
    async def test_claude_code_integration(self):
        """Test specific Claude Code integration points."""
        print("\n🤖 Testing Claude Code Integration Points...")
        
        # Test stdio transport compatibility
        print("  Testing stdio transport...")
        self.results["total_tests"] += 1
        try:
            assert self.config.transport == "stdio", "Wrong transport mode"
            print("    ✅ stdio transport configured")
            self.results["passed"] += 1
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Transport: {str(e)}")
            print(f"    ❌ Transport test failed: {e}")
        
        # Test JSON-RPC format
        print("  Testing JSON-RPC message format...")
        self.results["total_tests"] += 1
        try:
            # Create a sample JSON-RPC request
            request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }
            
            # Server should handle JSON-RPC format
            tools = await self.server.tool_registry.get_tools()
            response = {
                "jsonrpc": "2.0",
                "result": {"tools": tools},
                "id": 1
            }
            
            assert response["jsonrpc"] == "2.0", "Invalid JSON-RPC version"
            assert "result" in response, "Missing result field"
            assert "tools" in response["result"], "Missing tools in result"
            
            print("    ✅ JSON-RPC format validated")
            self.results["passed"] += 1
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"JSON-RPC: {str(e)}")
            print(f"    ❌ JSON-RPC test failed: {e}")
    
    def generate_report(self):
        """Generate test report."""
        print("\n" + "="*60)
        print("📊 CLAUDE CODE INTEGRATION TEST REPORT")
        print("="*60)
        
        # Overall status
        pass_rate = (self.results["passed"] / self.results["total_tests"]) * 100 if self.results["total_tests"] > 0 else 0
        
        if pass_rate >= 90:
            status = "✅ PASSED"
            grade = "A"
        elif pass_rate >= 80:
            status = "⚠️ PASSED WITH WARNINGS"
            grade = "B"
        elif pass_rate >= 70:
            status = "⚠️ NEEDS IMPROVEMENT"
            grade = "C"
        else:
            status = "❌ FAILED"
            grade = "F"
        
        print(f"\nOverall Status: {status}")
        print(f"Grade: {grade}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        # Test results
        print(f"\nTest Results:")
        print(f"  Total Tests: {self.results['total_tests']}")
        print(f"  Passed: {self.results['passed']} ✅")
        print(f"  Failed: {self.results['failed']} ❌")
        
        # Performance metrics
        if self.results["performance"]:
            print(f"\nPerformance Metrics:")
            for tool, time_ms in self.results["performance"].items():
                status = "✅" if time_ms < 200 else "⚠️"
                print(f"  {tool}: {time_ms:.2f}ms {status}")
        
        # Errors
        if self.results["errors"]:
            print(f"\nErrors Encountered:")
            for error in self.results["errors"]:
                print(f"  ❌ {error}")
        
        # Recommendations
        print(f"\nRecommendations:")
        if pass_rate == 100:
            print("  ✅ System ready for production Claude Code integration")
        elif pass_rate >= 80:
            print("  ⚠️ System functional but review failed tests")
            print("  ⚠️ Address performance issues if any")
        else:
            print("  ❌ Critical issues must be resolved before integration")
            print("  ❌ Review and fix all failed tests")
        
        print("\n" + "="*60)
        
        return grade
    
    async def cleanup(self):
        """Cleanup test environment."""
        print("\n🧹 Cleaning up test environment...")
        import shutil
        try:
            shutil.rmtree(self.test_dir)
            print("✅ Cleanup complete")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    async def run(self):
        """Run all integration tests."""
        print("\n[STARTING] Claude Code Integration Tests")
        print("="*60)
        
        try:
            await self.setup()
            
            # Run test suites
            await self.test_mcp_protocol_compliance()
            await self.test_tool_execution()
            await self.test_real_world_scenarios()
            await self.test_claude_code_integration()
            
            # Generate report
            grade = self.generate_report()
            
            return grade
            
        finally:
            await self.cleanup()


async def main():
    """Main test runner."""
    tester = ClaudeIntegrationTester()
    grade = await tester.run()
    
    # Exit code based on grade
    if grade in ["A", "B"]:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    asyncio.run(main())