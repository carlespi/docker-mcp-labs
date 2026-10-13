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
    # STAGE 2: Define and start the MCP Server
    # ========================================================

    server = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with Client(server) as client:

        # ====================================================
        # STAGE 3: Discover the tools exposed by the server
        # ====================================================

        response = await client.list_tools()

        llm_tools = []

        # Convert MCP tool definitions into the format expected
        # by the OpenAI-compatible API used by Ollama.
        for tool in response.tools:
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

        # ====================================================
        # STAGE 4: Get the user's request
        # ====================================================

        user_message = input("What do you want to do? ")

        messages = [
            {
                "role": "user",
                "content": user_message,
            }
        ]

        # ====================================================
        # STAGE 5: Start the agent loop
        # ====================================================

        max_iterations = 10

        for iteration in range(max_iterations):

            print(f"\n--- Agent iteration {iteration + 1} ---")

            # Ask the LLM what it wants to do next.
            llm_response = ollama.chat.completions.create(
                model="qwen3:1.7b",
                messages=messages,
                tools=llm_tools,
            )

            message = llm_response.choices[0].message

            # =================================================
            # STAGE 6: Stop when the LLM no longer requests tools
            # =================================================

            if not message.tool_calls:
                print("\nFinal response:")
                print(message.content)
                break

            # =================================================
            # STAGE 7: Save the LLM's tool request
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
            # STAGE 8: Execute every tool requested by the LLM
            # =================================================

            for tool_call in message.tool_calls:

                tool_name = tool_call.function.name
                arguments = json.loads(
                    tool_call.function.arguments
                )

                print(f"LLM selected tool: {tool_name}")
                print(f"Arguments: {arguments}")

                result = await client.call_tool(
                    tool_name,
                    arguments,
                )

                tool_result = result.content[0].text

                print(f"Tool result: {tool_result}")

                # =============================================
                # STAGE 9: Add each tool result to the history
                # =============================================

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )

            # After adding the tool results, the loop starts again.
            # The LLM now sees everything that happened so far and
            # decides whether another tool is needed.

        else:
            print(
                "\nAgent stopped because the maximum number "
                "of iterations was reached."
            )


asyncio.run(main())
