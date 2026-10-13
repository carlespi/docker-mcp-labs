from mcp.server import MCPServer


mcp = MCPServer("Text MCP Server")


@mcp.tool()
def say_hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"


@mcp.tool()
def uppercase_text(text: str) -> str:
    """Convert text to uppercase."""
    return text.upper()


if __name__ == "__main__":
    mcp.run()
