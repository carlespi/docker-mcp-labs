import os
from contextlib import asynccontextmanager

import httpx2

from mcp import Client
from mcp.client.streamable_http import streamable_http_client


# ============================================================
# GitHub Remote MCP Server configuration
# ============================================================

GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"


# ============================================================
# Reusable GitHub MCP connection
# ============================================================

@asynccontextmanager
async def connect_github_mcp():

    # Read the GitHub PAT from the environment
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        raise RuntimeError(
            "GITHUB_TOKEN environment variable is not set."
        )

    # Configure authentication and limit the server to
    # repository-related read-only tools
    headers = {
        "Authorization": f"Bearer {github_token}",
        "X-MCP-Toolsets": "repos",
        "X-MCP-Readonly": "true",
    }

    # Create the authenticated HTTP client
    async with httpx2.AsyncClient(
        headers=headers
    ) as http_client:

        # Create the Streamable HTTP transport
        transport = streamable_http_client(
            GITHUB_MCP_URL,
            http_client=http_client,
        )

        # Create and expose the MCP client
        async with Client(transport) as client:
            yield client
