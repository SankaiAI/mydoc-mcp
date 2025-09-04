"""
Basic MCP Integration Test
Tests core functionality without full server initialization
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that core modules import correctly."""
    print("\n[TEST] Module Imports")
    try:
        from src.config import ServerConfig
        print("  [OK] ServerConfig imported")
        
        from src.server import MyDocsMCPServer
        print("  [OK] MyDocsMCPServer imported")
        
        from src.database.connection import DatabaseConnection
        print("  [OK] DatabaseConnection imported")
        
        from src.tool_registry import ToolRegistry
        print("  [OK] ToolRegistry imported")
        
        # Test tool imports
        from src.tools.indexDocument import IndexDocumentTool
        print("  [OK] IndexDocumentTool imported")
        
        from src.tools.searchDocuments import SearchDocumentsTool
        print("  [OK] SearchDocumentsTool imported")
        
        from src.tools.getDocument import GetDocumentTool
        print("  [OK] GetDocumentTool imported")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Import error: {e}")
        return False

def test_config():
    """Test configuration setup."""
    print("\n[TEST] Configuration")
    try:
        from src.config import ServerConfig
        config = ServerConfig()
        
        # Test default values
        assert config.transport == "stdio", f"Wrong transport: {config.transport}"
        print(f"  [OK] Default transport: {config.transport}")
        
        assert config.log_level == "INFO", f"Wrong log level: {config.log_level}"
        print(f"  [OK] Default log level: {config.log_level}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Config error: {e}")
        return False

def test_tool_registry():
    """Test tool registry functionality."""
    print("\n[TEST] Tool Registry")
    try:
        from src.tool_registry import ToolRegistry
        registry = ToolRegistry()
        
        # Test registration
        from src.tools.indexDocument import IndexDocumentTool
        from src.tools.searchDocuments import SearchDocumentsTool
        from src.tools.getDocument import GetDocumentTool
        
        # Create tools
        tools = [
            IndexDocumentTool(),
            SearchDocumentsTool(),
            GetDocumentTool()
        ]
        
        # Register tools
        for tool in tools:
            registry.register_tool(
                name=tool.name,
                handler=tool.execute,
                description=tool.description,
                input_schema=tool.input_schema
            )
        
        # Check registration
        tool_names = registry.get_tool_names()
        assert len(tool_names) == 3, f"Expected 3 tools, got {len(tool_names)}"
        print(f"  [OK] Registered {len(tool_names)} tools")
        
        assert "indexDocument" in tool_names, "indexDocument not registered"
        assert "searchDocuments" in tool_names, "searchDocuments not registered"
        assert "getDocument" in tool_names, "getDocument not registered"
        print("  [OK] All core tools registered")
        
        # Check MCP compliance
        available = registry.get_available_tools()
        for tool in available:
            assert "name" in tool, f"Tool missing name: {tool}"
            assert "description" in tool, f"Tool missing description: {tool['name']}"
            assert "inputSchema" in tool, f"Tool missing inputSchema: {tool['name']}"
        print("  [OK] All tools MCP compliant")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Registry error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("BASIC MCP INTEGRATION TEST")
    print("=" * 60)
    
    results = {
        "imports": test_imports(),
        "config": test_config(),
        "registry": test_tool_registry()
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {test}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nSTATUS: ALL TESTS PASSED - READY FOR INTEGRATION")
        return 0
    else:
        print("\nSTATUS: TESTS FAILED - REVIEW ERRORS")
        return 1

if __name__ == "__main__":
    sys.exit(main())