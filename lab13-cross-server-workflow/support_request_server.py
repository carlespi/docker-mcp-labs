from mcp.server import MCPServer


mcp = MCPServer("Support Request MCP Server")


@mcp.tool()
def get_support_request_details(sr_id: str) -> dict:
    """Get details for a support request, including its meeting number."""

    support_requests = {
        "SR12345": {
            "sr_id": "SR12345",
            "customer": "Acme Corp",
            "issue": "Intermittent video quality",
            "meeting_number": "987654321",
        },
        "SR67890": {
            "sr_id": "SR67890",
            "customer": "Globex",
            "issue": "Users unable to join meeting",
            "meeting_number": "123456789",
        },
    }

    return support_requests.get(
        sr_id,
        {
            "error": f"Support request {sr_id} was not found."
        },
    )


if __name__ == "__main__":
    mcp.run()
