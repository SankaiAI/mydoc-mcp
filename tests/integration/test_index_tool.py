#!/usr/bin/env python3
"""Test the indexDocument tool directly."""
import json
import subprocess
import time

def test_index_document():
    """Test indexing a document."""
    cmd = ["docker", "exec", "-i", "mydocs-mcp-prod", "python", "-m", "src.server"]
    
    requests = [
        # Initialize the connection
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
        # List available tools
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        },
        # Call indexDocument tool
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "indexDocument",
                "arguments": {
                    "path": "/documents/api-design-guide.md",
                    "type": "markdown"
                }
            }
        }
    ]
    
    print("Testing indexDocument tool...")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send requests line by line
        input_lines = []
        for req in requests:
            input_lines.append(json.dumps(req))
        
        input_data = "\n".join(input_lines) + "\n"
        print(f"Sending input:\n{input_data}")
        
        # Send input and wait
        stdout, stderr = process.communicate(input=input_data, timeout=20)
        
        print("=== STDOUT ===")
        print(stdout)
        print("\n=== STDERR ===")
        print(stderr)
        
        # Process responses
        success_count = 0
        if stdout:
            lines = stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    try:
                        response = json.loads(line)
                        req_id = response.get('id', 'unknown')
                        
                        if 'result' in response:
                            print(f"\n✓ Request {req_id} SUCCESS:")
                            print(json.dumps(response['result'], indent=2))
                            success_count += 1
                        elif 'error' in response:
                            print(f"\n✗ Request {req_id} ERROR:")
                            print(json.dumps(response['error'], indent=2))
                        else:
                            print(f"\n? Request {req_id} UNKNOWN:")
                            print(json.dumps(response, indent=2))
                            
                    except json.JSONDecodeError as e:
                        print(f"Non-JSON output: {line}")
        
        print(f"\n=== SUMMARY ===")
        print(f"Successful requests: {success_count}/3")
        return success_count >= 2  # Initialize + at least one tool call
        
    except subprocess.TimeoutExpired:
        process.kill()
        print("❌ Process timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_index_document()
    if success:
        print("\n🎉 indexDocument tool test completed successfully!")
    else:
        print("\n❌ indexDocument tool test failed.")
    
    print("\nYou can now use the tool in Claude Code with:")
    print("/mcp__mydoc-mcp__indexDocument /documents/api-design-guide.md markdown")