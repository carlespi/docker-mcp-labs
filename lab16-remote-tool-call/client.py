import asyncio

from mcp_connection import connect_mcp


async def main():

    # ============================================================
    # STAGE 1: Connect to the remote MCP server
    # ============================================================

    async with connect_mcp() as client:

        print("\nConnected to remote MCP server.")

        # ========================================================
        # STAGE 2: Discover the tools exposed by the server
        # ========================================================

        response = await client.list_tools()

        print("\nSearching for the 'add' tool...")

        add_tool = next(
            (
                tool
                for tool in response.tools
                if tool.name == "add"
            ),
            None,
        )

        if add_tool is None:
            print("\nThe 'add' tool was not found.")
            return

        # ========================================================
        # STAGE 3: Inspect the selected tool
        # ========================================================

        print("\n======================================")
        print("TOOL FOUND")
        print("======================================")
        print(f"Name: {add_tool.name}")
        print(f"Description: {add_tool.description}")
        print(f"Input schema: {add_tool.input_schema}")

        # ========================================================
        # STAGE 4: Prepare the arguments for the tool
        # ========================================================

        arguments = {
            "a": 5,
            "b": 7,
        }

        print("\n======================================")
        print("CALLING TOOL")
        print("======================================")
        print(f"Tool: {add_tool.name}")
        print(f"Arguments: {arguments}")

        # ========================================================
        # STAGE 5: Execute the tool on the remote MCP server
        # ========================================================

        result = await client.call_tool(
            add_tool.name,
            arguments,
        )

        # ========================================================
        # STAGE 6: Display the result returned by the server
        # ========================================================

        print("\n======================================")
        print("TOOL RESULT")
        print("======================================")

        for item in result.content:
            if hasattr(item, "text"):
                print(item.text)
            else:
                print(item)


asyncio.run(main())
