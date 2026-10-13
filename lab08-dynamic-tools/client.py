import asyncio

from mcp import Client
from mcp.client.stdio import StdioServerParameters


async def main():
    server = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with Client(server) as client:
        response = await client.list_tools()

        print("\nAvailable tools:\n")

        for index, tool in enumerate(response.tools, start=1):
            print(f"{index}. {tool.name}")

        selected_number = int(input("\nSelect a tool: ")) - 1
        selected_tool = response.tools[selected_number]

        print(f"\nSelected tool: {selected_tool.name}")
        print(f"Input schema: {selected_tool.input_schema}")

        arguments = {}

        properties = selected_tool.input_schema.get("properties", {})

        for parameter_name, parameter_info in properties.items():
            value = input(f"Enter value for {parameter_name}: ")

            parameter_type = parameter_info.get("type")

            if parameter_type == "integer":
                value = int(value)

            arguments[parameter_name] = value

        result = await client.call_tool(
            selected_tool.name,
            arguments,
        )

        print("\nTool result:")
        print(result.content[0].text)


asyncio.run(main())
