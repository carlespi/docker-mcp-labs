import os
from contextlib import asynccontextmanager

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


HUGGINGFACE_MCP_URL = "https://huggingface.co/mcp"


@asynccontextmanager
async def connect_huggingface_mcp():

    # ========================================================
    # STAGE 1: Read the Hugging Face token from the environment
    # ========================================================

    hf_token = os.getenv("HF_TOKEN")

    if not hf_token:
        raise RuntimeError(
            "HF_TOKEN environment variable is not set."
        )

    # ========================================================
    # STAGE 2: Configure authentication
    # ========================================================

    headers = {
        "Authorization": f"Bearer {hf_token}",
    }

    # ========================================================
    # STAGE 3: Create the HTTP transport and MCP client
    # ========================================================

    async with httpx2.AsyncClient(headers=headers) as http_client:

        transport = streamable_http_client(
            HUGGINGFACE_MCP_URL,
            http_client=http_client,
        )

        async with Client(transport) as client:
            yield client
