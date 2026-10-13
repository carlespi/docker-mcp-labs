import asyncio
import json

from openai import OpenAI
from mcp import Client
from mcp.client.stdio import StdioServerParameters


# ============================================================
# STAGE 1: Configure the LLM client
# ============================================================

ollama = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)


async def main():

    # ========================================================
    # STAGE 2: Define both MCP Servers
    # ========================================================

    math_server = StdioServerParameters(
        command="python",
        args=["math_server.py"],
    )

    text_server = StdioServerParameters(
        command="python",
        args=["text_server.py"],
    )

    # ========================================================
    # STAGE 3: Start and connect to both MCP Servers
    # ========================================================

    async with Client(math_server) as math_client:
        async with Client(text_server) as text_client:

            # =================================================
            # STAGE 4: Discover tools from both MCP Servers
            # =================================================

            math_response = await math_client.list_tools()
            text_response = await text_client.list_tools()

            llm_tools = []

            # Maps each tool name to the MCP client/server
            # responsible for executing that tool.
            tool_routes = {}

            # Register tools exposed by the Math MCP Server.
            for tool in math_response.tools:
                llm_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.input_schema,
                        },
                    }
                )

                tool_routes[tool.name] = math_client

            # Register tools exposed by the Text MCP Server.
            for tool in text_response.tools:
                llm_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.input_schema,
                        },
                    }
                )

                tool_routes[tool.name] = text_client

            # =================================================
            # STAGE 5: Get the user's request
            # =================================================

            user_message = input("What do you want to do? ")

            messages = [
                {
                    "role": "user",
                    "content": user_message,
                }
            ]

            # =================================================
            # STAGE 6: Start the agent loop
            # =================================================

            max_iterations = 10

            for iteration in range(max_iterations):

                print(f"\n--- Agent iteration {iteration + 1} ---")

                # Give the LLM all tools from both MCP Servers.
                llm_response = ollama.chat.completions.create(
                    model="qwen3:1.7b",
                    messages=messages,
                    tools=llm_tools,
                )

                message = llm_response.choices[0].message

                # =================================================
                # STAGE 7: Stop when no more tools are needed
                # =================================================

                if not message.tool_calls:
                    print("\nFinal response:")
                    print(message.content)
                    break

                # =================================================
                # STAGE 8: Save the LLM tool requests
                # =================================================

                assistant_tool_calls = []

                for tool_call in message.tool_calls:
                    assistant_tool_calls.append(
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    )

                messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": assistant_tool_calls,
                    }
                )

                # =================================================
                # STAGE 9: Route every tool call to its MCP Server
                # =================================================

                for tool_call in message.tool_calls:

                    tool_name = tool_call.function.name
                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                    # Find which MCP client owns this tool.
                    selected_client = tool_routes[tool_name]

                    print(f"\nLLM selected tool: {tool_name}")
                    print(f"Arguments: {arguments}")

                    # Execute the tool against the correct MCP Server.
                    result = await selected_client.call_tool(
                        tool_name,
                        arguments,
                    )

                    tool_result = result.content[0].text

                    print(f"Tool result: {tool_result}")

                    # =============================================
                    # STAGE 10: Add the tool result to the history
                    # =============================================

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result,
                        }
                    )

                # The loop starts again. The LLM receives the
                # updated history and can request tools from
                # either MCP Server.

            else:
                print(
                    "\nAgent stopped because the maximum number "
                    "of iterations was reached."
                )


asyncio.run(main())
