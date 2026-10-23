import os
from contextlib import asynccontextmanager

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"


@asynccontextmanager
async def connect_github_mcp():

    # ========================================================
    # STAGE 1: Read the GitHub token from the environment
    # ========================================================

    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        raise RuntimeError(
            "GITHUB_TOKEN environment variable is not set."
        )

    # ========================================================
    # STAGE 2: Configure authentication and restrict the
    # GitHub MCP Server to read-only repository tools
    # ========================================================

    headers = {
        "Authorization": f"Bearer {github_token}",
        "X-MCP-Toolsets": "repos",
        "X-MCP-Readonly": "true",
    }

    # ========================================================
    # STAGE 3: Create the HTTP transport and MCP client
    # ========================================================

    async with httpx2.AsyncClient(headers=headers) as http_client:

        transport = streamable_http_client(
            GITHUB_MCP_URL,
            http_client=http_client,
        )

        async with Client(transport) as client:
            yield client
