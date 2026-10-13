import asyncio
import json

from openai import OpenAI
from mcp import Client
from mcp.client.stdio import StdioServerParameters


# ============================================================
# STAGE 1: Initialize the LLM client
# ============================================================

# The OpenAI SDK is used as the client for Ollama's
# OpenAI-compatible API.
ollama = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)


async def main():

    # ========================================================
    # STAGE 2: Define the MCP servers
    # ========================================================

    # Define how each MCP server must be started.
    # At this point they are only configured, not running yet.
    support_request_server = StdioServerParameters(
        command="python",
        args=["support_request_server.py"],
    )

    meeting_server = StdioServerParameters(
        command="python",
        args=["meeting_server.py"],
    )


    # ========================================================
    # STAGE 3: Start the MCP clients and connect to each server
    # ========================================================

    # Each Client starts and communicates with its corresponding
    # MCP server through stdio.
    async with Client(support_request_server) as sr_client:
        async with Client(meeting_server) as meeting_client:


            # =================================================
            # STAGE 4: Discover the tools exposed by each server
            # =================================================

            # Ask each MCP server which tools it exposes.
            sr_response = await sr_client.list_tools()
            meeting_response = await meeting_client.list_tools()


            # =================================================
            # STAGE 5: Transform MCP tools into LLM tool format
            # =================================================

            # llm_tools contains the tool definitions in the format
            # expected by the OpenAI-compatible API.
            #
            # tool_routes keeps track of which MCP client/server
            # is responsible for executing each tool.
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


            # =================================================
            # STAGE 6: Receive the user's request
            # =================================================

            user_message = input("What do you want to know? ")

            # messages stores the conversation history that will
            # be sent back to the LLM on every iteration.
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Use the available tools whenever needed. "
                        "If the user asks for information that requires multiple tools, "
                        "call them step by step. Use the output of one tool as input "
                        "for another tool when necessary."
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

            # The loop allows the LLM to request additional tools
            # after seeing the result of a previous tool.
            max_iterations = 10

            for iteration in range(max_iterations):

                print(f"\n--- Agent iteration {iteration + 1} ---")

                llm_response = ollama.chat.completions.create(
                    model="qwen3:1.7b",
                    messages=messages,
                    tools=llm_tools,
                )

                message = llm_response.choices[0].message


                # If the LLM does not request another tool,
                # its response is considered the final answer.
                if not message.tool_calls:
                    print("\nFinal response:")
                    print(message.content)
                    break


                # =================================================
                # STAGE 8: Process the tool calls selected by the LLM
                # =================================================

                # The LLM already decided which tools to use and
                # generated their arguments.
                #
                # Convert those tool calls into the message format
                # expected by the OpenAI-compatible API so they can
                # be stored correctly in the conversation history.
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

                # Execute every tool requested by the LLM.
                for tool_call in message.tool_calls:

                    tool_name = tool_call.function.name
                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                    # Use tool_routes to find the MCP client connected
                    # to the server that owns this tool.
                    selected_client = tool_routes[tool_name]

                    print(f"\nLLM selected tool: {tool_name}")
                    print(f"Arguments: {arguments}")

                    # Execute the tool on the correct MCP server.
                    result = await selected_client.call_tool(
                        tool_name,
                        arguments,
                    )

                    tool_result = result.content[0].text

                    print(f"Tool result: {tool_result}")


                    # =================================================
                    # STAGE 10: Add tool results and continue the loop
                    # =================================================

                    # Store the tool result in the conversation history.
                    # On the next iteration, the LLM receives this result
                    # and can either call another tool or produce the
                    # final natural-language response.
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