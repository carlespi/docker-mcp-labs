import asyncio
import json

from openai import OpenAI

from mcp_connection import connect_mcp
from github_connection import connect_github_mcp


# ============================================================
# STAGE 1: Configure the local LLM
# ============================================================

llm = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

MODEL = "qwen3:1.7b"


async def main():

    # ========================================================
    # STAGE 2: Connect to both remote MCP servers
    # ========================================================

    async with connect_mcp() as example_client:
        async with connect_github_mcp() as github_client:

            print("\nConnected to Example MCP Server.")
            print("Connected to GitHub MCP Server.")

            # =================================================
            # STAGE 3: Discover tools from both MCP servers
            # =================================================

            example_response = await example_client.list_tools()
            github_response = await github_client.list_tools()

            # =================================================
            # STAGE 4: Select the tools used in this lab
            # =================================================

            example_allowed_tools = {
                "add",
                "echo",
            }

            github_allowed_tools = {
                "get_file_contents",
            }

            example_tools = [
                tool
                for tool in example_response.tools
                if tool.name in example_allowed_tools
            ]

            github_tools = [
                tool
                for tool in github_response.tools
                if tool.name in github_allowed_tools
            ]

            all_tools = example_tools + github_tools

            print("\n======================================")
            print("AVAILABLE MCP TOOLS")
            print("======================================")

            for tool in all_tools:
                print(f"{tool.name} | {tool.description}")

            # =================================================
            # STAGE 5: Convert MCP tools to LLM format and map
            # each tool to the server that can execute it
            # =================================================

            llm_tools = []
            tool_to_server = {}

            for tool in example_tools:

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

                tool_to_server[tool.name] = example_client

            for tool in github_tools:

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

                tool_to_server[tool.name] = github_client

            # =================================================
            # STAGE 6: Receive the user request
            # =================================================

            user_message = input("\nAsk something: ")

            messages = [
                {
                    "role": "system",
                    "content": (
                        "Use the available tools whenever needed. "
                        "Choose the tool that matches the user's request. "
                        "Do not invent tool results."
                    ),
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ]

            # =================================================
            # STAGE 7: Send the request and available tools
            # to the LLM
            # =================================================

            first_response = llm.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=llm_tools,
            )

            assistant_message = first_response.choices[0].message

            # =================================================
            # STAGE 8: Return directly if the LLM did not
            # request any tool calls
            # =================================================

            if not assistant_message.tool_calls:

                print("\n======================================")
                print("LLM RESPONSE")
                print("======================================")
                print(assistant_message.content)

                return

            # =================================================
            # STAGE 9: Add the assistant message and requested
            # tool calls to the conversation history
            # =================================================

            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in assistant_message.tool_calls
                    ],
                }
            )

            # =================================================
            # STAGE 10: Find the correct MCP server and execute
            # each tool requested by the LLM
            # =================================================

            for tool_call in assistant_message.tool_calls:

                tool_name = tool_call.function.name

                arguments = json.loads(
                    tool_call.function.arguments
                )

                print("\n======================================")
                print("LLM TOOL DECISION")
                print("======================================")
                print(f"Tool: {tool_name}")
                print(f"Arguments: {arguments}")

                selected_server = tool_to_server.get(tool_name)

                if selected_server is None:
                    raise RuntimeError(
                        f"No MCP server found for tool: {tool_name}"
                    )

                result = await selected_server.call_tool(
                    tool_name,
                    arguments,
                )

                # =============================================
                # STAGE 11: Extract text and embedded resource
                # content returned by the MCP tool
                # =============================================

                result_parts = []

                for item in result.content:

                    if hasattr(item, "text"):
                        result_parts.append(item.text)

                    elif hasattr(item, "resource"):
                        resource = item.resource

                        if hasattr(resource, "text"):
                            result_parts.append(resource.text)

                tool_result = "\n".join(result_parts)

                print("\n======================================")
                print("MCP TOOL RESULT")
                print("======================================")
                print(tool_result)

                # =============================================
                # STAGE 12: Add the tool result to the
                # conversation history
                # =============================================

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )

            # =================================================
            # STAGE 13: Send the tool result back to the LLM
            # and generate the final response
            # =================================================

            final_response = llm.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=llm_tools,
            )

            final_message = final_response.choices[0].message

            print("\n======================================")
            print("FINAL LLM RESPONSE")
            print("======================================")
            print(final_message.content)


asyncio.run(main())
