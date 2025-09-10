import asyncio

import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions

import mcp.server.stdio

from . import sfdc_client
from . import definitions as sfmcpdef  
from . import implementations as sfmcpimpl
    
server = Server("salesforce-mcp")

sf_client = sfdc_client.OrgHandler()
if not sf_client.establish_connection():
    print("Failed to initialize Salesforce connection")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Returns object creation, data query, and Einstein Studio model tools.
    """
    return sfmcpdef.get_tools()

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, str]) -> list[types.TextContent]:
    # Object Creation Tools
    if name == "create_object":
        return sfmcpimpl.create_object_impl(sf_client, arguments)
    elif name == "create_object_with_fields":
        return sfmcpimpl.create_object_with_fields_impl(sf_client, arguments)
    
    # Data Query Tools
    elif name == "run_soql_query":
        return sfmcpimpl.run_soql_query_impl(sf_client, arguments)
    elif name == "run_sosl_search":
        return sfmcpimpl.run_sosl_search_impl(sf_client, arguments)
    elif name == "get_object_fields":
        return sfmcpimpl.get_object_fields_impl(sf_client, arguments)
    elif name == "describe_object":
        return sfmcpimpl.describe_object_impl(sf_client, arguments)
    
    # Einstein Studio Model Tools
    elif name == "create_einstein_model":
        return sfmcpimpl.create_einstein_model_impl(sf_client, arguments)
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def run():
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="salesforce-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(run())

def main():
    asyncio.run(run())