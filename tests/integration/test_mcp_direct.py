#!/usr/bin/env python3
"""Test MCP server tools directly via JSON-RPC."""
import json
import subprocess
import sys

def test_mcp_tools():
    """Test the MCP server tools directly."""
    cmd = ["docker", "exec", "-i", "mydocs-mcp-prod", "python", "-m", "src.server"]
    
    # Prepare requests
    requests = [
        # Initialize
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        },
        # List tools
        {
            "jsonrpc": "2.0", 
            "id": 2,
            "method": "tools/list",
            "params": {}
        },
        # Create test directory and file first
        {
            "jsonrpc": "2.0",
            "id": 3, 
            "method": "tools/call",
            "params": {
                "name": "indexDocument",
                "arguments": {
                    "path": "/documents/test.md",
                    "type": "markdown"
                }
            }
        }
    ]
    
    try:
        # Start process
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send all requests
        input_data = ""
        for req in requests:
            input_data += json.dumps(req) + "\n"
        
        # Execute and get response
        stdout, stderr = process.communicate(input=input_data, timeout=30)
        
        print("=== STDOUT ===")
        print(stdout)
        print("=== STDERR ===") 
        print(stderr)
        
        # Parse responses
        if stdout:
            for line in stdout.strip().split('\n'):
                if line.strip():
                    try:
                        response = json.loads(line)
                        print(f"\nParsed response: {json.dumps(response, indent=2)}")
                    except json.JSONDecodeError:
                        print(f"Non-JSON line: {line}")
        
    except subprocess.TimeoutExpired:
        process.kill()
        print("Process timed out")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # First ensure test file exists
    print("Creating test file...")
    subprocess.run([
        "docker", "exec", "mydocs-mcp-prod", 
        "sh", "-c", 
        "mkdir -p /documents && echo '# Test Document\n\nThis is a test markdown file.' > /documents/test.md"
    ])
    
    print("Testing MCP tools...")
    test_mcp_tools()