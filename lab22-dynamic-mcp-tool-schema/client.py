import asyncio
import json

from jsonschema import ValidationError, validate
from ollama import chat

from huggingface_connection import connect_huggingface_mcp


# ============================================================
# STAGE 1: Configure the local LLM
# ============================================================

MODEL = "qwen3:1.7b"

TRANSLATION_TOOL_NAME = (
    "gr1_milmmt_46_4b_translation_translate"
)


async def main():

    # ========================================================
    # STAGE 2: Connect to the Hugging Face MCP Server
    # ========================================================

    async with connect_huggingface_mcp() as mcp_client:

        print("\nConnected to Hugging Face MCP Server.")

        # ====================================================
        # STAGE 3: Discover the tools exposed by the server
        # ====================================================

        response = await mcp_client.list_tools()

        # ====================================================
        # STAGE 4: Find the translation tool
        # ====================================================

        translation_tool = next(
            (
                tool
                for tool in response.tools
                if tool.name == TRANSLATION_TOOL_NAME
            ),
            None,
        )

        if translation_tool is None:
            raise RuntimeError(
                "Translation tool was not found."
            )

        # ====================================================
        # STAGE 5: Read the MCP input schema dynamically
        # ====================================================

        tool_schema = translation_tool.input_schema

        print("\n======================================")
        print("TRANSLATION TOOL")
        print("======================================")
        print(f"Name: {translation_tool.name}")
        print(f"Description: {translation_tool.description}")

        print("\n======================================")
        print("INPUT SCHEMA")
        print("======================================")
        print(
            json.dumps(
                tool_schema,
                indent=2,
            )
        )

        # ====================================================
        # STAGE 6: Convert the MCP tool to Ollama tool format
        # using the schema discovered at runtime
        # ====================================================

        llm_tools = [
            {
                "type": "function",
                "function": {
                    "name": translation_tool.name,
                    "description": (
                        translation_tool.description or ""
                    ),
                    "parameters": tool_schema,
                },
            }
        ]

        # ====================================================
        # STAGE 7: Receive the user request
        # ====================================================

        user_message = input("\nAsk for a translation: ")

        messages = [
            {
                "role": "system",
                "content": (
                    "Use the available translation tool whenever "
                    "the user asks for a translation. "
                    "Read the tool input schema and generate arguments "
                    "using actual values from the user's request. "
                    "Infer the source language and target language "
                    "when they are clear from the request. "
                    "Do not invent parameter names. "
                    "Use only parameter names defined by the tool schema."
                ),
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        # ====================================================
        # STAGE 8: Ask Qwen to generate the tool call
        # using Ollama's native tool-calling API
        # ====================================================

        llm_response = chat(
            model=MODEL,
            messages=messages,
            tools=llm_tools,
            think=False,
        )

        assistant_message = llm_response.message

        print("\n======================================")
        print("RAW LLM MESSAGE")
        print("======================================")
        print(assistant_message)

        if not assistant_message.tool_calls:
            raise RuntimeError(
                "The LLM did not generate a tool call."
            )

        # ====================================================
        # STAGE 9: Add the assistant message and requested
        # tool call to the conversation history
        # ====================================================

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

        # ====================================================
        # STAGE 10: Read the tool arguments generated by Qwen
        # ====================================================

        tool_call = assistant_message.tool_calls[0]

        tool_name = tool_call.function.name
        arguments = tool_call.function.arguments

        print("\n======================================")
        print("LLM GENERATED ARGUMENTS")
        print("======================================")
        print(f"Tool: {tool_name}")
        print(
            json.dumps(
                arguments,
                indent=2,
            )
        )

        # ====================================================
        # STAGE 11: Validate the LLM-generated arguments
        # against the MCP input schema
        # ====================================================

        try:
            validate(
                instance=arguments,
                schema=tool_schema,
            )

        except ValidationError as error:
            raise RuntimeError(
                "Tool argument validation failed: "
                f"{error.message}"
            ) from error

        # ====================================================
        # STAGE 12: Execute the validated MCP tool call
        # ====================================================

        result = await mcp_client.call_tool(
            tool_name,
            arguments,
        )

        # ====================================================
        # STAGE 13: Extract text returned by the MCP tool
        # ====================================================

        result_parts = []

        for item in result.content:

            if hasattr(item, "text"):
                result_parts.append(
                    item.text
                )

            elif hasattr(item, "resource"):

                resource = item.resource

                if hasattr(resource, "text"):
                    result_parts.append(
                        resource.text
                    )

        tool_result = "\n".join(
            result_parts
        )

        print("\n======================================")
        print("TRANSLATION TOOL RESULT")
        print("======================================")
        print(tool_result)

        # ====================================================
        # STAGE 14: Add the real MCP tool result to the
        # conversation history
        # ====================================================

        messages.append(
            {
                "role": "tool",
                "content": tool_result,
            }
        )

        # ====================================================
        # STAGE 15: Ask Qwen to generate the final answer
        # without exposing tools again
        # ====================================================

        final_messages = messages + [
            {
                "role": "system",
                "content": (
                    "Answer the user using the actual translation "
                    "returned by the tool. "
                    "State clearly what text was translated, "
                    "the target language, and the translated result."
                ),
            }
        ]

        final_response = chat(
            model=MODEL,
            messages=final_messages,
            think=False,
        )

        # ====================================================
        # STAGE 16: Display the final LLM response
        # ====================================================

        print("\n======================================")
        print("FINAL LLM RESPONSE")
        print("======================================")
        print(final_response.message.content)


asyncio.run(main())
