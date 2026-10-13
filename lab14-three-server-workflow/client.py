import asyncio
import json

from openai import OpenAI
from mcp import Client
from mcp.client.stdio import StdioServerParameters

# ============================================================
# STAGE 1: Initialize the LLM client
# ============================================================

ollama = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)


async def main():

    # ========================================================
    # STAGE 2: Define the MCP servers
    # ========================================================

    support_request_server = StdioServerParameters(
        command="python",
        args=["support_request_server.py"],
    )

    meeting_server = StdioServerParameters(
        command="python",
        args=["meeting_server.py"],
    )

    logs_server = StdioServerParameters(
        command="python",
        args=["logs_server.py"],
    )

    # ========================================================
    # STAGE 3: Start the MCP clients and connect to each server
    # ========================================================

    async with Client(support_request_server) as sr_client:
        async with Client(meeting_server) as meeting_client:
            async with Client(logs_server) as logs_client:

                # =================================================
                # STAGE 4: Discover the tools exposed by each server
                # =================================================

                sr_response = await sr_client.list_tools()
                meeting_response = await meeting_client.list_tools()
                logs_response = await logs_client.list_tools()

                # =================================================
                # STAGE 5: Transform MCP tools into LLM tool format
                # =================================================

                llm_tools = []
                tool_routes = {}

                for tool in sr_response.tools:
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

                    tool_routes[tool.name] = sr_client

                for tool in meeting_response.tools:
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

                    tool_routes[tool.name] = meeting_client

                for tool in logs_response.tools:
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

                    tool_routes[tool.name] = logs_client

                # =================================================
                # STAGE 6: Receive the user's request
                # =================================================

                user_message = input("What do you want to know? ")

                messages = [
                    {
                        "role": "system",
                        "content": (
                            "Use the available tools whenever needed. "
                            "Call tools step by step and respect their required inputs. "
                            "Never use a meeting_number where a meeting_id is required. "
                            "If a tool requires meeting_id and you only have meeting_number, "
                            "first call the meeting details tool to obtain the meeting_id. "
                            "Use the output of one tool as input for another tool when necessary."
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ]

                # =================================================
                # STAGE 7: Send the request and available tools to the LLM
                # =================================================

                max_iterations = 10

                for iteration in range(max_iterations):

                    print(f"\n--- Agent iteration {iteration + 1} ---")

                    llm_response = ollama.chat.completions.create(
                        model="qwen3:1.7b",
                        messages=messages,
                        tools=llm_tools,
                    )

                    message = llm_response.choices[0].message

                    if not message.tool_calls:
                        print("\nFinal response:")
                        print(message.content)
                        break

                    # =================================================
                    # STAGE 8: Process the tool calls selected by the LLM
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
                    # STAGE 9: Route each tool call to the correct MCP server
                    # =================================================

                    for tool_call in message.tool_calls:

                        tool_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)

                        selected_client = tool_routes[tool_name]

                        print(f"\nLLM selected tool: {tool_name}")
                        print(f"Arguments: {arguments}")

                        result = await selected_client.call_tool(
                            tool_name,
                            arguments,
                        )

                        tool_result = result.content[0].text

                        print(f"Tool result: {tool_result}")

                        # =================================================
                        # STAGE 10: Add tool results and continue the loop
                        # =================================================

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": tool_result,
                            }
                        )

                else:
                    print(
                        "\nAgent stopped because the maximum number "
                        "of iterations was reached."
                    )


asyncio.run(main())
