from datetime import datetime

from fastmcp import FastMCP

mcp = FastMCP("Date and Time Server")


@mcp.tool(description="Get the current date in the format Year-Month-Day (YYYY-MM-DD)")
def get_current_date() -> str:
    """Returns the current date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


@mcp.tool(description="Get the current date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)")
def get_current_datetime() -> str:
    """Returns the current date and time in ISO 8601 format up to seconds."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8002)
