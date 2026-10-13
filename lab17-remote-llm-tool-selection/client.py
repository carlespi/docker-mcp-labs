import asyncio
import json

from openai import OpenAI

from mcp_connection import connect_mcp


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
    # STAGE 2: Connect to the remote MCP server
    # ========================================================

    async with connect_mcp() as mcp_client:

        print("\nConnected to remote MCP server.")

        # ====================================================
        # STAGE 3: Discover the remote MCP tools
        # ====================================================

        response = await mcp_client.list_tools()

        # For this lab, expose only simple tools that are easy
        # for the LLM to choose between.
        allowed_tools = {
            "add",
            "echo",
        }

        mcp_tools = [
            tool
            for tool in response.tools
            if tool.name in allowed_tools
        ]

        print("\n======================================")
        print("REMOTE MCP TOOLS")
        print("======================================")

        for tool in mcp_tools:
            print(f"{tool.name} | {tool.description}")

        # ====================================================
        # STAGE 4: Convert MCP tools to OpenAI tool format
        # ====================================================

        llm_tools = []

        for tool in mcp_tools:
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
        # STAGE 5: Receive the user request
        # ====================================================

        user_message = input("\nAsk something: ")

        messages = [
            {
                "role": "system",
                "content": (
                    "Use the available tools whenever they are needed. "
                    "Do not calculate or simulate a tool result yourself "
                    "when an appropriate tool is available."
                ),
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        # ====================================================
        # STAGE 6: Ask the LLM what to do
        # ====================================================

        first_response = llm.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=llm_tools,
        )

        assistant_message = first_response.choices[0].message

        # ====================================================
        # STAGE 7: Check whether the LLM selected a tool
        # ====================================================

        if not assistant_message.tool_calls:
            print("\n======================================")
            print("LLM RESPONSE")
            print("======================================")
            print(assistant_message.content)
            return

        # ========================================================
        # STAGE 8: Add the assistant message and requested tool calls to the conversation history
        # ========================================================

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

        # ====================================================
        # STAGE 9: Execute the selected remote MCP tool
        # ====================================================

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

            result = await mcp_client.call_tool(
                tool_name,
                arguments,
            )

            tool_result = "\n".join(
                item.text
                for item in result.content
                if hasattr(item, "text")
            )

            print("\n======================================")
            print("REMOTE MCP TOOL RESULT")
            print("======================================")
            print(tool_result)

            # =================================================
            # STAGE 9: Add the tool result to the conversation
            # =================================================

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                }
            )

        # ====================================================
        # STAGE 10: Ask the LLM for the final response
        # ====================================================

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
