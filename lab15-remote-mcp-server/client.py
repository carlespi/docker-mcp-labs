import asyncio

from mcp_connection import connect_mcp


async def main():

    # Connect to the remote MCP server
    async with connect_mcp() as client:

        print("\nConnected to remote MCP server.")

        # Discover available tools
        response = await client.list_tools()

        print("\nAvailable tools:\n")

        for index, tool in enumerate(
            response.tools,
            start=1,
        ):
            print(f"{index}. {tool.name}")

            if tool.description:
                print(f"   {tool.description}")

            print()

        # Display each tool input schema
        print("\nTool schemas:\n")

        for tool in response.tools:
            print("=" * 60)
            print(f"Tool: {tool.name}")
            print(f"Input schema: {tool.input_schema}")


asyncio.run(main())