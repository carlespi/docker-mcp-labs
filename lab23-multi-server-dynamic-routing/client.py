import asyncio
import json

from jsonschema import ValidationError, validate
from ollama import chat

from github_connection import connect_github_mcp
from huggingface_connection import connect_huggingface_mcp


# ============================================================
# STAGE 1: Configure the local LLM and tools used in the lab
# ============================================================

MODEL = "qwen3:1.7b"

GITHUB_TOOL_NAME = "get_file_contents"

TRANSLATION_TOOL_NAME = (
    "gr1_milmmt_46_4b_translation_translate"
)

ALLOWED_TOOL_NAMES = {
    GITHUB_TOOL_NAME,
    TRANSLATION_TOOL_NAME,
}


def extract_tool_result(result):

    # ========================================================
    # Extract text from MCP TextContent and EmbeddedResource
    # responses
    # ========================================================

    result_parts = []

    for item in result.content:

        if hasattr(item, "text"):
            result_parts.append(item.text)

        elif hasattr(item, "resource"):

            resource = item.resource

            if hasattr(resource, "text"):
                result_parts.append(resource.text)

    return "\n".join(result_parts)


async def main():

    # ========================================================
    # STAGE 2: Connect to both remote MCP servers
    # ========================================================

    async with connect_github_mcp() as github_client:
        async with connect_huggingface_mcp() as huggingface_client:

            print("\nConnected to GitHub MCP Server.")
            print("Connected to Hugging Face MCP Server.")

            # =================================================
            # STAGE 3: Discover tools from both MCP servers
            # =================================================

            github_response = await github_client.list_tools()
            huggingface_response = await huggingface_client.list_tools()

            # =================================================
            # STAGE 4: Build a unified tool catalog
            # =================================================

            discovered_tools = (
                github_response.tools
                + huggingface_response.tools
            )

            selected_tools = [
                tool
                for tool in discovered_tools
                if tool.name in ALLOWED_TOOL_NAMES
            ]

            if len(selected_tools) != len(ALLOWED_TOOL_NAMES):

                discovered_names = {
                    tool.name
                    for tool in selected_tools
                }

                missing_tools = (
                    ALLOWED_TOOL_NAMES - discovered_names
                )

                raise RuntimeError(
                    "Required tools were not found: "
                    + ", ".join(missing_tools)
                )

            # =================================================
            # STAGE 5: Build the tool-to-server routing table
            # =================================================

            tool_to_server = {}

            for tool in github_response.tools:

                if tool.name in ALLOWED_TOOL_NAMES:
                    tool_to_server[tool.name] = github_client

            for tool in huggingface_response.tools:

                if tool.name in ALLOWED_TOOL_NAMES:
                    tool_to_server[tool.name] = huggingface_client

            # =================================================
            # STAGE 6: Store each dynamically discovered schema
            # by tool name
            # =================================================

            tool_schemas = {
                tool.name: tool.input_schema
                for tool in selected_tools
            }

            # =================================================
            # STAGE 7: Convert the MCP tools to Ollama tool
            # format using their runtime-discovered schemas
            # =================================================

            llm_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.input_schema,
                    },
                }
                for tool in selected_tools
            ]

            print("\n======================================")
            print("AVAILABLE TOOLS")
            print("======================================")

            for tool in selected_tools:
                print(f"- {tool.name}")

            # =================================================
            # STAGE 8: Receive the user request
            # =================================================

            user_message = input("\nEnter your request: ")

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You have access to tools from multiple MCP "
                        "servers. Use the tools when needed to complete "
                        "the user's request. Read each tool schema "
                        "carefully and generate arguments using only "
                        "parameter names defined by that schema. "
                        "When the user asks to read repository content "
                        "and then translate it, first use the GitHub "
                        "tool to retrieve the content and then use the "
                        "translation tool with the retrieved content."
                    ),
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ]

            # =================================================
            # STAGE 9: Run the multi-server agent loop
            # =================================================

            max_iterations = 5
            translation_completed = False

            for iteration in range(1, max_iterations + 1):

                print("\n======================================")
                print(f"ITERATION {iteration}")
                print("======================================")

                # =============================================
                # STAGE 10: Ask Qwen what tool to use next
                # =============================================

                llm_response = chat(
                    model=MODEL,
                    messages=messages,
                    tools=llm_tools,
                    think=False,
                )

                assistant_message = llm_response.message

                # =============================================
                # STAGE 11: If Qwen does not request a tool,
                # return its answer directly
                # =============================================

                if not assistant_message.tool_calls:

                    print("\n======================================")
                    print("FINAL RESPONSE")
                    print("======================================")
                    print(assistant_message.content)

                    return

                # =============================================
                # STAGE 12: Add the assistant message and
                # requested tool calls to conversation history
                # =============================================

                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_message.content,
                        "tool_calls": [
                            {
                                "function": {
                                    "name": (
                                        tool_call.function.name
                                    ),
                                    "arguments": (
                                        tool_call.function.arguments
                                    ),
                                }
                            }
                            for tool_call
                            in assistant_message.tool_calls
                        ],
                    }
                )

                # =============================================
                # STAGE 13: Process every requested tool call
                # =============================================

                for tool_call in assistant_message.tool_calls:

                    tool_name = tool_call.function.name
                    arguments = tool_call.function.arguments

                    print("\n======================================")
                    print("TOOL CALL")
                    print("======================================")
                    print(f"Tool: {tool_name}")

                    print("\nArguments:")
                    print(
                        json.dumps(
                            arguments,
                            indent=2,
                        )
                    )

                    # =========================================
                    # STAGE 14: Confirm that the requested tool
                    # exists in the routing table
                    # =========================================

                    if tool_name not in tool_to_server:
                        raise RuntimeError(
                            f"No MCP server is mapped to tool: "
                            f"{tool_name}"
                        )

                    # =========================================
                    # STAGE 15: Validate the generated arguments
                    # against the dynamically discovered schema
                    # =========================================

                    try:
                        validate(
                            instance=arguments,
                            schema=tool_schemas[tool_name],
                        )

                    except ValidationError as error:
                        raise RuntimeError(
                            f"Tool argument validation failed: "
                            f"{error.message}"
                        ) from error

                    # =========================================
                    # STAGE 16: Route the tool call to the MCP
                    # server that owns the requested tool
                    # =========================================

                    mcp_client = tool_to_server[tool_name]

                    result = await mcp_client.call_tool(
                        tool_name,
                        arguments,
                    )

                    # =========================================
                    # STAGE 17: Extract the MCP tool result
                    # =========================================

                    tool_result = extract_tool_result(result)

                    print("\nTool result:")
                    print(tool_result)

                    # =========================================
                    # STAGE 18: Add the MCP tool result to the
                    # conversation history
                    # =========================================

                    messages.append(
                        {
                            "role": "tool",
                            "tool_name": tool_name,
                            "content": tool_result,
                        }
                    )

                    # =========================================
                    # STAGE 19: Mark the workflow complete once
                    # the translation tool has executed
                    # =========================================

                    if tool_name == TRANSLATION_TOOL_NAME:
                        translation_completed = True

                # =============================================
                # STAGE 20: Stop exposing tools after the
                # translation has been completed
                # =============================================

                if translation_completed:
                    break

            # =================================================
            # STAGE 21: Generate the final user-facing response
            # without exposing MCP tools again
            # =================================================

            if translation_completed:

                final_messages = messages + [
                    {
                        "role": "system",
                        "content": (
                            "The required tools have already been "
                            "executed. Answer the user's original "
                            "request using the tool results in the "
                            "conversation. Do not request another tool."
                        ),
                    }
                ]

                final_response = chat(
                    model=MODEL,
                    messages=final_messages,
                    think=False,
                )

                print("\n======================================")
                print("FINAL RESPONSE")
                print("======================================")
                print(final_response.message.content)

                return

            # =================================================
            # STAGE 22: Stop if the task could not be completed
            # within the allowed number of iterations
            # =================================================

            raise RuntimeError(
                "Maximum number of agent iterations reached "
                "before the translation was completed."
            )


asyncio.run(main())
