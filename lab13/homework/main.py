import asyncio
import json
from contextlib import AsyncExitStack

from guardrails import Guard, OnFailAction
from guardrails.hub import DetectJailbreak
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from openai import OpenAI

from config import settings
from logger import get_configured_logger
from prompts import TRIP_PLANNING_SYSTEM_PROMPT


logger = get_configured_logger(
    "trip-assistant", log_file="trip-assistant.log", log_to_console=False
)


class MCPManager:
    def __init__(self, servers: dict[str, str]):
        self.servers = servers
        self.clients = {}
        self.tools = []
        self._stack = AsyncExitStack()

    async def __aenter__(self):
        for name, url in self.servers.items():
            try:
                logger.info(f"Connecting to MCP server: {name} at {url}")
                read, write, _ = await self._stack.enter_async_context(
                    streamable_http_client(url)
                )
                session = await self._stack.enter_async_context(
                    ClientSession(read, write)
                )
                await session.initialize()

                tools_resp = await session.list_tools()
                tool_names = []
                for t in tools_resp.tools:
                    self.clients[t.name] = session
                    tool_names.append(t.name)
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
                logger.info(f"Connected to {name}, registered tools: {tool_names}")
            except Exception as e:
                logger.warning(f"Could not connect to {name}: {e}")

        logger.info(f"MCPManager initialized with {len(self.tools)} tools")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Closing MCP connections")
        await self._stack.aclose()

    async def call_tool(self, name: str, args: dict) -> str:
        logger.debug(f"Calling tool: {name} with args: {args}")
        result = await self.clients[name].call_tool(name, arguments=args)
        logger.debug(f"Tool {name} returned {len(result.content[0].text)} chars")
        return result.content[0].text


def create_guards():
    logger.info("Initializing guardrails")

    jailbreak_guard = Guard().use(
        DetectJailbreak,
        on_fail=OnFailAction.EXCEPTION,
        disable_llm=True,
        disable_classifier=False,
    )
    logger.info("Guardrails initialized: DetectJailbreak")
    return [jailbreak_guard]


def validate_response(content: str, guards: list) -> str:
    try:
        for guard in guards:
            guard.validate(content)
        logger.debug("Response passed all guardrails")
        return content
    except Exception as e:
        logger.warning(f"Guardrail violation: {e}")
        return "I can only help with travel planning. Please ask me about trips, destinations, or travel arrangements."


async def chat_loop():
    logger.info("Starting Trip Planning Assistant")
    model = settings.gemini_model
    logger.info(f"Using model: {model}")

    mcp_servers = {
        # custom mcp server
        "weather": settings.weather_mcp_url,
        # tavily remote mcp server
        "tavily": f"{settings.tavily_mcp_url}{settings.tavily_api_key}",
    }

    client = OpenAI(api_key=settings.gemini_api_key, base_url=settings.gemini_base_url)

    guards = create_guards()

    print("=" * 60)
    print("Trip Planning Assistant")
    print("=" * 60)
    print("I can help you plan your trip! Ask me about:")
    print("- Weather at your destination")
    print("- Travel tips and recommendations")
    print("- Local attractions and restaurants")
    print("\nType 'quit' or 'exit' to end the conversation.")
    print("=" * 60)
    messages = [{"role": "system", "content": TRIP_PLANNING_SYSTEM_PROMPT}]

    async with MCPManager(mcp_servers) as mcp:
        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                logger.info("Session ended by user interrupt")
                print("\nGoodbye!")
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit"):
                logger.info("Session ended by user command")
                print("\nGoodbye! Have a great trip!")
                break

            logger.info(f"User input received: {user_input[:50]}...")
            messages.append({"role": "user", "content": user_input})

            for iteration in range(10):
                logger.debug(f"LLM request iteration {iteration + 1}")
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=mcp.tools if mcp.tools else None,
                    tool_choice="auto" if mcp.tools else None,
                    max_completion_tokens=1000,
                )

                assistant_msg = response.choices[0].message
                usage = response.usage
                if usage:
                    logger.info(
                        f"LLM usage - prompt: {usage.prompt_tokens}, "
                        f"completion: {usage.completion_tokens}, "
                        f"total: {usage.total_tokens}"
                    )

                if not assistant_msg.tool_calls:
                    content = assistant_msg.content or ""
                    validated = validate_response(content, guards)
                    messages.append({"role": "assistant", "content": validated})
                    logger.info(f"Assistant response: {validated[:300]}...")
                    print(f"\nAssistant: {validated}")
                    break

                messages.append(assistant_msg)
                logger.info(f"Tool calls requested: {len(assistant_msg.tool_calls)}")

                for tool_call in assistant_msg.tool_calls:
                    func_name = tool_call.function.name
                    raw_args = tool_call.function.arguments

                    try:
                        func_args = json.loads(raw_args)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parse error for {func_name}: {e}")
                        logger.error(f"Raw arguments: {raw_args}")
                        func_args = {}

                    logger.info(f"Executing tool: {func_name}")
                    try:
                        result = await mcp.call_tool(func_name, func_args)
                        logger.info(f"Tool result preview: {result[:500]}...")
                    except Exception as e:
                        logger.error(f"Tool execution failed: {func_name} - {e}")
                        result = f"Tool error: {e}"

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": str(result),
                        }
                    )


def main():
    logger.info("Application starting")
    asyncio.run(chat_loop())
    logger.info("Application shutdown")


if __name__ == "__main__":
    main()
