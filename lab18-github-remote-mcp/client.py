import asyncio

from github_connection import connect_github_mcp


async def main():

    # ============================================================
    # STAGE 1: Connect to the GitHub Remote MCP Server
    # ============================================================

    async with connect_github_mcp() as client:

        print("\nConnected to GitHub MCP Server.")

        # ========================================================
        # STAGE 2: Discover the tools exposed by GitHub
        # ========================================================

        response = await client.list_tools()

        # ========================================================
        # STAGE 3: Display the available GitHub MCP tools
        # ========================================================

        print("\n======================================")
        print("AVAILABLE GITHUB MCP TOOLS")
        print("======================================")

        for index, tool in enumerate(
            response.tools,
            start=1,
        ):
            print(
                f"{index}. {tool.name} | "
                f"{tool.description}"
            )


asyncio.run(main())
