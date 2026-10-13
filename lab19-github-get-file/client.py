import asyncio

from github_connection import connect_github_mcp


# ============================================================
# Repository to use in this lab
# ============================================================

GITHUB_OWNER = "carlespi"
GITHUB_REPO = "docker-mcp-labs"
FILE_PATH = "README.md"


async def main():

    # ============================================================
    # STAGE 1: Connect to the GitHub Remote MCP Server
    # ============================================================

    async with connect_github_mcp() as client:

        print("\nConnected to GitHub MCP Server.")

        # ========================================================
        # STAGE 2: Discover the available GitHub MCP tools
        # ========================================================

        response = await client.list_tools()

        # ========================================================
        # STAGE 3: Find the get_file_contents tool
        # ========================================================

        get_file_tool = next(
            (
                tool
                for tool in response.tools
                if tool.name == "get_file_contents"
            ),
            None,
        )

        if get_file_tool is None:
            print("\nThe 'get_file_contents' tool was not found.")
            return

        print("\n======================================")
        print("TOOL FOUND")
        print("======================================")
        print(f"Name: {get_file_tool.name}")
        print(f"Description: {get_file_tool.description}")
        print(f"Input schema: {get_file_tool.input_schema}")

        # ========================================================
        # STAGE 4: Prepare the tool arguments
        # ========================================================

        arguments = {
            "owner": GITHUB_OWNER,
            "repo": GITHUB_REPO,
            "path": FILE_PATH,
        }

        print("\n======================================")
        print("CALLING GITHUB MCP TOOL")
        print("======================================")
        print(f"Tool: {get_file_tool.name}")
        print(f"Arguments: {arguments}")

        # ========================================================
        # STAGE 5: Execute the tool on the GitHub MCP Server
        # ========================================================

        result = await client.call_tool(
            get_file_tool.name,
            arguments,
        )

        # ========================================================
        # STAGE 6: Extract text content from the tool result
        # ========================================================

        tool_result = "\n".join(
            item.text
            for item in result.content
            if hasattr(item, "text")
        )

        # ========================================================
        # STAGE 7: Display the file contents
        # ========================================================

        print("\n======================================")
        print("GITHUB FILE CONTENT")
        print("======================================")
        print(tool_result)


asyncio.run(main())
