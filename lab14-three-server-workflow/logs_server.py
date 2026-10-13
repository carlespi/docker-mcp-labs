from mcp.server import MCPServer


mcp = MCPServer("Logs MCP Server")


@mcp.tool()
def get_meeting_logs(meeting_id: str) -> dict:
    """Get technical log findings for a meeting using its meeting ID."""

    logs = {
        "meet-abc-123": {
            "meeting_id": "meet-abc-123",
            "packet_loss_percent": 3.8,
            "average_jitter_ms": 42,
            "disconnect_events": 2,
            "errors": [
                "High packet loss detected",
                "Media quality degradation detected",
            ],
        },
        "meet-xyz-789": {
            "meeting_id": "meet-xyz-789",
            "packet_loss_percent": 0.2,
            "average_jitter_ms": 8,
            "disconnect_events": 0,
            "errors": [],
        },
    }

    return logs.get(
        meeting_id,
        {
            "error": f"No logs were found for meeting {meeting_id}."
        },
    )


if __name__ == "__main__":
    mcp.run()
