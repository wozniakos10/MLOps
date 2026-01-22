"""Test the Visualization MCP server via LLM (like exercise3)."""

import asyncio
import base64
import json
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from openai import OpenAI


class MCPManager:
    def __init__(self, servers: dict[str, str]):
        self.servers = servers
        self.clients = {}
        self.tools = []  # in OpenAI format
        self._stack = AsyncExitStack()

    async def __aenter__(self):
        for url in self.servers.values():
            # initialize MCP session with Streamable HTTP client
            read, write, session_id = await self._stack.enter_async_context(
                streamable_http_client(url)
            )
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            # use /list_tools MCP endpoint to get tools
            # parse each one to get OpenAI-compatible schema
            tools_resp = await session.list_tools()
            for t in tools_resp.tools:
                self.clients[t.name] = session
                self.tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.inputSchema,
                        },
                    }
                )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._stack.aclose()

    async def call_tool(self, name: str, args: dict) -> dict | str:
        # call the MCP tool with given arguments
        result = await self.clients[name].call_tool(name, arguments=args)
        return result.content[0].text


def save_image(base64_data: str, filename: str):
    """Decode base64 image and save to disk."""
    image_bytes = base64.b64decode(base64_data)
    output_path = Path(__file__).parent / filename
    output_path.write_bytes(image_bytes)
    print(f"  Saved: {output_path}")


async def make_llm_request(prompt: str, image_filename: str) -> str:
    mcp_servers = {
        "visualization": "http://localhost:8004/mcp",
    }

    vllm_client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

    async with MCPManager(mcp_servers) as mcp:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Use tools if you need to."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        # guard: loop limit, we break as soon as we get an answer
        for _ in range(10):
            response = vllm_client.chat.completions.create(
                model="",
                messages=messages,
                tools=mcp.tools,
                tool_choice="auto",
                max_completion_tokens=1000,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )

            response = response.choices[0].message
            if not response.tool_calls:
                return response.content

            messages.append(response)
            for tool_call in response.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                print(f"Executing tool '{func_name}'")
                func_result = await mcp.call_tool(func_name, func_args)

                # If it's a line_plot, save the base64 image to disk
                if func_name == "line_plot":
                    save_image(func_result, image_filename)
                    # Send short message to LLM to avoid token overflow
                    tool_content = "Image generated successfully and saved to disk."
                else:
                    tool_content = str(func_result)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": tool_content,
                    }
                )


if __name__ == "__main__":
    # Test 1: Simple line plot
    print("=" * 80)
    print("Test 1: Create a simple line plot")
    print("=" * 80)
    prompt = """Create a line plot with data [[1, 4, 2, 5, 3, 6, 4, 7], [7, 6, 5, 4, 3, 2, 1, 0]] 
    with title "Sales Comparison", x_label "Month", y_label "Revenue", and legend true."""
    
    response = asyncio.run(make_llm_request(prompt, "test1_sales_comparison.png"))
    print("Response:\n", response)

    print()

    # Test 2: Temperature visualization
    print("=" * 80)
    print("Test 2: Visualize temperature data")
    print("=" * 80)
    prompt = """Create a line plot with data [[20, 22, 25, 23, 21, 19, 24]] 
    with title "Weekly Temperature", x_label "Day", y_label "Temperature"."""
    
    response = asyncio.run(make_llm_request(prompt, "test2_temperature.png"))
    print("Response:\n", response)

    print("\nAll tests completed!")
