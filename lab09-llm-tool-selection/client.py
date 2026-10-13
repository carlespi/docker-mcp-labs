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

        llm_response = ollama.chat.completions.create(
            model="qwen3:1.7b",
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
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

        print("\nTool result:")
        print(result.content[0].text)


asyncio.run(main())
