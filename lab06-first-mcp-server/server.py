from mcp.server import MCPServer


mcp = MCPServer("Lab 6 MCP Server")


@mcp.tool()
def say_hello(name: str) -> str:
    """Return a greeting for the provided name."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run()
