#!/usr/bin/env python3
"""
MCP-over-HTTP Bridge: Allows remote MCP clients to connect via HTTP
This enables hosting MCP servers in the cloud for multiple clients
"""

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import os
from typing import Dict, Any
import uuid

# Import your existing MCP components  
from salesforcemcp import sfdc_client
from salesforcemcp import definitions as sfmcpdef
from salesforcemcp import implementations as sfmcpimpl

app = FastAPI(
    title="MCP Bridge Server",
    description="HTTP/WebSocket bridge for Model Context Protocol",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Initialize Salesforce client
sf_client = sfdc_client.OrgHandler()
if not sf_client.establish_connection():
    print("Warning: Failed to establish Salesforce connection")

@app.get("/")
async def root():
    return {
        "service": "MCP Bridge Server",
        "version": "1.0.0",
        "protocols": ["http", "websocket"],
        "mcp_version": "2024-11-05",
        "endpoints": {
            "mcp_http": "/mcp",
            "mcp_ws": "/mcp/ws",
            "tools": "/mcp/tools"
        }
    }

@app.post("/mcp")
async def mcp_http(request: Dict[str, Any]):
    """HTTP endpoint that accepts MCP JSON-RPC requests"""
    try:
        # Validate MCP request format
        if not request.get("jsonrpc") == "2.0":
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC version")
        
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        # Handle MCP methods
        if method == "initialize":
            return {
                "jsonrpc": "2.0", 
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "salesforce-mcp-bridge",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": {}
                    }
                }
            }
            
        elif method == "tools/list":
            tools = sfmcpdef.get_tools()
            return {
                "jsonrpc": "2.0",
                "id": request_id, 
                "result": {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        } for tool in tools
                    ]
                }
            }
            
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Call the appropriate implementation
            if tool_name == "create_object":
                result = sfmcpimpl.create_object_impl(sf_client, arguments)
            elif tool_name == "create_object_with_fields":
                result = sfmcpimpl.create_object_with_fields_impl(sf_client, arguments)
            elif tool_name == "run_soql_query":
                result = sfmcpimpl.run_soql_query_impl(sf_client, arguments)
            elif tool_name == "run_sosl_search":
                result = sfmcpimpl.run_sosl_search_impl(sf_client, arguments)
            elif tool_name == "get_object_fields":
                result = sfmcpimpl.get_object_fields_impl(sf_client, arguments)
            elif tool_name == "describe_object":
                result = sfmcpimpl.describe_object_impl(sf_client, arguments)
            elif tool_name == "create_einstein_model":
                result = sfmcpimpl.create_einstein_model_impl(sf_client, arguments)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": r.text} for r in result]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
            
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32000,
                "message": str(e)
            }
        }

@app.websocket("/mcp/ws") 
async def mcp_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time MCP communication"""
    await websocket.accept()
    
    try:
        while True:
            # Receive MCP request
            data = await websocket.receive_text()
            request = json.loads(data)
            
            # Process same as HTTP endpoint
            response = await mcp_http(request)
            
            # Send response
            await websocket.send_text(json.dumps(response))
            
    except Exception as e:
        await websocket.close(code=1000)

@app.get("/mcp/tools")
async def list_tools():
    """List available MCP tools in a simple format"""
    tools = sfmcpdef.get_tools()
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "schema": tool.inputSchema
            } for tool in tools
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
