import asyncio

from huggingface_connection import connect_huggingface_mcp


TOOL_NAME = "gr1_milmmt_46_4b_translation_translate"


async def main():

    async with connect_huggingface_mcp() as client:

        response = await client.list_tools()

        translation_tool = next(
            (
                tool
                for tool in response.tools
                if tool.name == TOOL_NAME
            ),
            None,
        )

        if translation_tool is None:
            print("Translation tool not found.")
            return

        print("\n======================================")
        print("TRANSLATION TOOL")
        print("======================================")
        print(f"Name: {translation_tool.name}")
        print(f"Description: {translation_tool.description}")
        print(f"Input schema: {translation_tool.input_schema}")


asyncio.run(main())
