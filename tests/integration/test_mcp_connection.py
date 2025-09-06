#!/usr/bin/env python3
"""
Test script to verify MCP server connection and tool availability.
"""
import asyncio
import json
import subprocess
import sys
import logging

async def test_mcp_connection():
    """Test the MCP connection to the Docker container."""
    print("Testing MCP server connection...")
    
    # Command from claude_code_config.json
    cmd = [
        "docker", "exec", "-i", "mydocs-mcp-prod", 
        "python", "-m", "src.server"
    ]
    
    # Set up environment
    env = {
        "MCP_TRANSPORT": "stdio",
        "LOG_LEVEL": "INFO", 
        "DATABASE_PATH": "/app/data/mydocs.db",
        "DOCUMENT_DIRECTORIES": "/documents"
    }
    
    try:
        # Start the MCP server process
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Sending initialization request...")
        init_json = json.dumps(init_request) + "\n"
        
        # Send request
        process.stdin.write(init_json)
        process.stdin.flush()
        
        # Read response (with timeout)
        try:
            # Wait for response
            stdout_data, stderr_data = process.communicate(timeout=10)
            
            print("=== STDOUT ===")
            print(stdout_data)
            print("=== STDERR ===") 
            print(stderr_data)
            
            if stdout_data:
                try:
                    response = json.loads(stdout_data.strip())
                    print(f"Initialization response: {response}")
                    
                    if "result" in response:
                        print("✅ MCP server initialization successful!")
                        return True
                    else:
                        print("❌ MCP server initialization failed")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON response: {e}")
                    return False
            else:
                print("❌ No response received from MCP server")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ MCP server did not respond within timeout")
            process.kill()
            return False
            
    except Exception as e:
        print(f"❌ Error testing MCP connection: {e}")
        return False

async def test_tools_list():
    """Test listing available tools."""
    print("\nTesting tools/list...")
    
    cmd = [
        "docker", "exec", "-i", "mydocs-mcp-prod",
        "python", "-m", "src.server"
    ]
    
    env = {
        "MCP_TRANSPORT": "stdio",
        "LOG_LEVEL": "INFO",
        "DATABASE_PATH": "/app/data/mydocs.db", 
        "DOCUMENT_DIRECTORIES": "/documents"
    }
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Send both initialization and tools/list requests
        requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize", 
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
        ]
        
        # Send requests
        for req in requests:
            req_json = json.dumps(req) + "\n"
            process.stdin.write(req_json)
            process.stdin.flush()
        
        # Close stdin to signal we're done
        process.stdin.close()
        
        # Read all output
        stdout_data, stderr_data = process.communicate(timeout=15)
        
        print("=== STDOUT ===")
        print(stdout_data)
        print("=== STDERR ===")
        print(stderr_data)
        
        # Parse responses
        if stdout_data:
            lines = stdout_data.strip().split('\n')
            for line in lines:
                if line.strip():
                    try:
                        response = json.loads(line)
                        if response.get("id") == 2 and "result" in response:
                            tools = response["result"].get("tools", [])
                            print(f"\n✅ Found {len(tools)} tools:")
                            for tool in tools:
                                print(f"  - {tool.get('name')}: {tool.get('description')}")
                            return True
                    except json.JSONDecodeError:
                        continue
        
        print("❌ Could not get tools list")
        return False
        
    except Exception as e:
        print(f"❌ Error testing tools/list: {e}")
        return False

if __name__ == "__main__":
    print("MCP Server Connection Test")
    print("=" * 50)
    
    # Run tests
    loop = asyncio.get_event_loop()
    
    # Test basic connection
    success = loop.run_until_complete(test_mcp_connection())
    
    if success:
        # Test tools list
        loop.run_until_complete(test_tools_list())
    
    print("\nTest completed.")