from mcp.server import MCPServer


mcp = MCPServer("Meeting MCP Server")


@mcp.tool()
def get_meeting_details(meeting_number: str) -> dict:
    """Get technical details for a meeting using its meeting number."""

    meetings = {
        "987654321": {
            "meeting_number": "987654321",
            "meeting_id": "meet-abc-123",
            "region": "US-East",
            "duration_minutes": 47,
            "participants": 23,
        },
        "123456789": {
            "meeting_number": "123456789",
            "meeting_id": "meet-xyz-789",
            "region": "US-West",
            "duration_minutes": 62,
            "participants": 41,
        },
    }

    return meetings.get(
        meeting_number,
        {
            "error": f"Meeting {meeting_number} was not found."
        },
    )


if __name__ == "__main__":
    mcp.run()
