import asyncio

from mcp import Client
from mcp.client.stdio import StdioServerParameters


async def main():
    server = StdioServerParameters(
        command="python",
        args=["../lab06-first-mcp-server/server.py"],
    )

    async with Client(server) as client:
        tools = await client.list_tools()

        print("Available tools:")
        for tool in tools.tools:
            print(f"- {tool.name}")

        result = await client.call_tool(
            "say_hello",
            {"name": "Carlos"},
        )

        print("\nTool result:")
        print(result.content[0].text)


asyncio.run(main())
