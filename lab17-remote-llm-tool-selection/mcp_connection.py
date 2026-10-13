import asyncio
from contextlib import asynccontextmanager
from urllib.parse import parse_qs, urlparse

import httpx2
from pydantic import AnyUrl

from mcp import Client
from mcp.client.auth import AuthorizationCodeResult, OAuthClientProvider
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import (
    OAuthClientInformationFull,
    OAuthClientMetadata,
    OAuthToken,
)


# ============================================================
# Remote MCP server configuration
# ============================================================

SERVER_URL = "https://example-server.modelcontextprotocol.io/mcp"

CALLBACK_HOST = "127.0.0.1"
CALLBACK_PORT = 3030
CALLBACK_URL = f"http://localhost:{CALLBACK_PORT}/callback"


# ============================================================
# OAuth token storage
# ============================================================

class InMemoryTokenStorage:
    def __init__(self):
        self.tokens: OAuthToken | None = None
        self.client_info: OAuthClientInformationFull | None = None

    async def get_tokens(self):
        return self.tokens

    async def set_tokens(self, tokens):
        self.tokens = tokens

    async def get_client_info(self):
        return self.client_info

    async def set_client_info(self, client_info):
        self.client_info = client_info


# ============================================================
# OAuth browser authorization
# ============================================================

async def open_browser(authorization_url: str):
    print("\nOpen this URL in your browser:\n")
    print(authorization_url)
    print()


# ============================================================
# OAuth callback listener
# ============================================================

async def wait_for_callback() -> AuthorizationCodeResult:
    callback_future = asyncio.get_running_loop().create_future()

    async def handle_callback(reader, writer):
        request_line = await reader.readline()
        request = request_line.decode()

        path = request.split(" ")[1]
        params = parse_qs(urlparse(path).query)

        if "error" in params:
            error = params["error"][0]
            response_body = f"OAuth authentication failed: {error}"

            writer.write(
                (
                    "HTTP/1.1 400 Bad Request\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "\r\n"
                    f"{response_body}"
                ).encode()
            )

            await writer.drain()
            writer.close()
            await writer.wait_closed()

            callback_future.set_exception(
                RuntimeError(response_body)
            )
            return

        code = params["code"][0]
        state = params.get("state", [None])[0]
        iss = params.get("iss", [None])[0]

        response_body = (
            "OAuth authentication completed successfully. "
            "You can close this browser tab."
        )

        writer.write(
            (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "\r\n"
                f"{response_body}"
            ).encode()
        )

        await writer.drain()
        writer.close()
        await writer.wait_closed()

        callback_future.set_result(
            AuthorizationCodeResult(
                code=code,
                state=state,
                iss=iss,
            )
        )

    server = await asyncio.start_server(
        handle_callback,
        CALLBACK_HOST,
        CALLBACK_PORT,
    )

    print(
        f"Waiting for OAuth authentication callback "
        f"on localhost:{CALLBACK_PORT}"
    )

    async with server:
        return await callback_future


# ============================================================
# OAuth configuration
# ============================================================

oauth = OAuthClientProvider(
    server_url=SERVER_URL,
    client_metadata=OAuthClientMetadata(
        client_name="Lab 15 Remote MCP Client",
        redirect_uris=[
            AnyUrl(CALLBACK_URL)
        ],
        token_endpoint_auth_method="client_secret_post",
    ),
    storage=InMemoryTokenStorage(),
    redirect_handler=open_browser,
    callback_handler=wait_for_callback,
)


# ============================================================
# Public connection function
# ============================================================

@asynccontextmanager
async def connect_mcp():
    async with httpx2.AsyncClient(
        auth=oauth
    ) as http_client:

        transport = streamable_http_client(
            SERVER_URL,
            http_client=http_client,
        )

        async with Client(transport) as client:
            yield client