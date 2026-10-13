import asyncio
import json

from openai import OpenAI
from mcp import Client
from mcp.client.stdio import StdioServerParameters


ollama = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)


async def main():
    server = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with Client(server) as client:
        response = await client.list_tools()

        llm_tools = []

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

        user_message = input("What do you want to do? ")

        messages = [
            {
                "role": "user",
                "content": user_message,
            }
        ]

        llm_response = ollama.chat.completions.create(
            model="qwen3:1.7b",
            messages=messages,
            tools=llm_tools,
        )

        message = llm_response.choices[0].message

        if not message.tool_calls:
            print("\nLLM response:")
            print(message.content)
            return

        tool_call = message.tool_calls[0]

        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        print(f"\nLLM selected tool: {tool_name}")
        print(f"Arguments: {arguments}")

        result = await client.call_tool(
            tool_name,
            arguments,
        )

        tool_result = result.content[0].text

        print(f"Tool result: {tool_result}")

        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                ],
            }
        )

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result,
            }
        )

        final_response = ollama.chat.completions.create(
            model="qwen3:1.7b",
            messages=messages,
        )

        print("\nFinal response:")
        print(final_response.choices[0].message.content)


asyncio.run(main())
