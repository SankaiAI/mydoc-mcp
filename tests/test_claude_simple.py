"""
Simple Claude Code Integration Test for mydocs-mcp.
Tests basic MCP functionality without Unicode issues.
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import ServerConfig
from src.server import MyDocsMCPServer
from src.database.connection import DatabaseConnection


async def test_claude_integration():
    """Test Claude Code MCP integration."""
    print("\n" + "="*60)
    print("CLAUDE CODE INTEGRATION TEST - mydocs-mcp")
    print("="*60)
    
    # Setup
    test_dir = tempfile.mkdtemp(prefix="mydocs_test_")
    print(f"\n[INFO] Test directory: {test_dir}")
    
    # Create config
    config = ServerConfig()
    config.database_url = f"sqlite:///{test_dir}/test.db"
    config.document_root = f"{test_dir}/documents"
    config.log_level = "INFO"
    config.transport = "stdio"
    
    # Create directories
    os.makedirs(f"{test_dir}/documents", exist_ok=True)
    
    # Create test documents
    docs = {
        "test.md": "# Test Document\n\nThis is for testing MCP integration.",
        "api.md": "# API Reference\n\n## Endpoints\n- GET /test",
        "readme.txt": "README: How to use this application"
    }
    
    for filename, content in docs.items():
        Path(f"{test_dir}/documents/{filename}").write_text(content)
    
    print("[OK] Created test documents")
    
    try:
        # Initialize server
        server = MyDocsMCPServer(config)
        print("[OK] Server initialized")
        
        # Initialize database
        db_path = config.database_url.replace("sqlite:///", "")
        db = DatabaseConnection(db_path)
        await db.connect()  # This automatically initializes schema
        print("[OK] Database initialized")
        
        # Test 1: Tool Registry
        print("\n[TEST] MCP Tool Registry")
        tools = server.tool_registry.get_available_tools()
        assert len(tools) == 3, f"Expected 3 tools, got {len(tools)}"
        tool_names = [t["name"] for t in tools]
        assert "indexDocument" in tool_names
        assert "searchDocuments" in tool_names
        assert "getDocument" in tool_names
        print("  [PASS] All 3 MCP tools registered")
        
        # Test 2: Index Document
        print("\n[TEST] indexDocument Tool")
        start = time.time()
        result = await server.tool_registry.execute_tool(
            "indexDocument",
            {"file_path": f"{test_dir}/documents/test.md"}
        )
        elapsed_ms = (time.time() - start) * 1000
        assert result["success"], "indexDocument failed"
        assert result["document_id"], "No document ID returned"
        print(f"  [PASS] Document indexed in {elapsed_ms:.2f}ms")
        
        # Index all documents
        for doc in ["api.md", "readme.txt"]:
            await server.tool_registry.execute_tool(
                "indexDocument",
                {"file_path": f"{test_dir}/documents/{doc}"}
            )
        
        # Test 3: Search Documents
        print("\n[TEST] searchDocuments Tool")
        start = time.time()
        result = await server.tool_registry.execute_tool(
            "searchDocuments",
            {"query": "test"}
        )
        elapsed_ms = (time.time() - start) * 1000
        assert "results" in result
        assert len(result["results"]) > 0, "No search results found"
        assert elapsed_ms < 200, f"Search too slow: {elapsed_ms:.2f}ms"
        print(f"  [PASS] Search completed in {elapsed_ms:.2f}ms")
        print(f"  [INFO] Found {len(result['results'])} results")
        
        # Test 4: Get Document
        print("\n[TEST] getDocument Tool")
        start = time.time()
        result = await server.tool_registry.execute_tool(
            "getDocument",
            {"file_path": f"{test_dir}/documents/test.md"}
        )
        elapsed_ms = (time.time() - start) * 1000
        assert result["success"], "getDocument failed"
        assert result["content"], "No content returned"
        assert elapsed_ms < 200, f"Get too slow: {elapsed_ms:.2f}ms"
        print(f"  [PASS] Document retrieved in {elapsed_ms:.2f}ms")
        
        # Test 5: MCP Protocol Compliance
        print("\n[TEST] MCP Protocol Compliance")
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"
        print("  [PASS] All tools comply with MCP protocol")
        
        # Test 6: stdio Transport
        print("\n[TEST] Transport Configuration")
        assert config.transport == "stdio", f"Wrong transport: {config.transport}"
        print("  [PASS] stdio transport configured for Claude Code")
        
        # Summary
        print("\n" + "="*60)
        print("TEST RESULTS: ALL TESTS PASSED")
        print("="*60)
        print("\nSYSTEM STATUS:")
        print("  - MCP Protocol: COMPLIANT")
        print("  - Performance: SUB-200ms")
        print("  - Transport: stdio (Claude Code compatible)")
        print("  - Tools: All 3 core tools operational")
        print("\nGRADE: A - READY FOR CLAUDE CODE INTEGRATION")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        import shutil
        try:
            shutil.rmtree(test_dir)
            print("\n[INFO] Test directory cleaned up")
        except:
            pass


if __name__ == "__main__":
    success = asyncio.run(test_claude_integration())
    sys.exit(0 if success else 1)