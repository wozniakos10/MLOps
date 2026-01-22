import json
from typing import Callable

import polars as pl
from openai import OpenAI


def make_llm_request(prompt: str) -> str:
    client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

    messages = [
        {"role": "developer", "content": "You are a helpful data analysis assistant."},
        {"role": "user", "content": prompt},
    ]

    tool_definitions, tool_name_to_func = get_tool_definitions()

    # guard: loop limit, we break as soon as we get an answer
    for _ in range(10):
        response = client.chat.completions.create(
            model="",
            messages=messages,
            tools=tool_definitions,  # always pass all tools in this example
            tool_choice="auto",
            max_completion_tokens=1000,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        resp_message = response.choices[0].message
        messages.append(resp_message.model_dump())

        print(f"Generated message: {resp_message.model_dump()}")
        print()

        # parse possible tool calls (assume only "function" tools)
        if resp_message.tool_calls:
            for tool_call in resp_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                # call tool, serialize result, append to messages
                func = tool_name_to_func[func_name]
                func_result = func(**func_args)

                messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(func_result),
                        "tool_call_id": tool_call.id,
                    }
                )
        else:
            # no tool calls, we're done
            return resp_message.content

    # we should not get here
    last_response = resp_message.content
    return f"Could not resolve request, last response: {last_response}"


def get_tool_definitions() -> tuple[list[dict], dict[str, Callable]]:
    tool_definitions = [
        {
            "type": "function",
            "function": {
                "name": "read_remote_csv",
                "description": "Read a CSV file from a remote URL and return its contents as text. Use this to analyze CSV data from the web.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the CSV file to read.",
                        },
                        "max_rows": {
                            "type": "integer",
                            "description": "Maximum number of rows to return (default: 50). Use smaller values for large datasets.",
                            "default": 50,
                        },
                    },
                    "required": ["url"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_remote_parquet",
                "description": "Read a Parquet file from a remote URL and return its contents as text. Use this to analyze Parquet data from the web.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the Parquet file to read.",
                        },
                        "max_rows": {
                            "type": "integer",
                            "description": "Maximum number of rows to return (default: 50). Use smaller values for large datasets.",
                            "default": 50,
                        },
                    },
                    "required": ["url"],
                },
            },
        },
    ]

    tool_name_to_callable = {
        "read_remote_csv": read_remote_csv_tool,
        "read_remote_parquet": read_remote_parquet_tool,
    }

    return tool_definitions, tool_name_to_callable


def read_remote_csv_tool(url: str, max_rows: int = 50) -> str:
    """Read a CSV file from a URL and return it as a string representation."""
    try:
        # Read the CSV file using Polars
        df = pl.read_csv(url)

        # Limit rows if needed
        df_limited = df.head(max_rows)

        # Get basic statistics
        n_rows, n_cols = df.shape
        info = f"Dataset info: {n_rows} total rows, {n_cols} columns\n"
        info += f"Showing first {min(max_rows, n_rows)} rows:\n\n"

        # Return string representation
        return info + str(df_limited)
    except Exception as e:
        return f"Error reading CSV from {url}: {str(e)}"


def read_remote_parquet_tool(url: str, max_rows: int = 50) -> str:
    """Read a Parquet file from a URL and return it as a string representation."""
    try:
        # Read the Parquet file using Polars
        df = pl.read_parquet(url)

        # Limit rows if needed
        df_limited = df.head(max_rows)

        # Get basic statistics
        n_rows, n_cols = df.shape
        info = f"Dataset info: {n_rows} total rows, {n_cols} columns\n"
        info += f"Showing first {min(max_rows, n_rows)} rows:\n\n"

        # Return string representation
        return info + str(df_limited)
    except Exception as e:
        return f"Error reading Parquet from {url}: {str(e)}"


if __name__ == "__main__":
    # Example 1: NYC Yellow Taxi data (Parquet)
    print("=" * 80)
    print("Example 1: NYC Yellow Taxi Data")
    print("=" * 80)
    prompt = """Read this Parquet file with NYC yellow taxi data:
    https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet
    
    Show me the first few rows and tell me what columns are available."""
    response = make_llm_request(prompt)
    print("Response:\n", response)


    print("\n" + "=" * 80)
    print("Example 2: ApisTox Dataset (CSV)")
    print("=" * 80)
    # Note: GitHub URLs need to be raw URLs
    prompt = """Read this CSV file with ApisTox dataset:
    https://raw.githubusercontent.com/j-adamczyk/ApisTox_dataset/master/outputs/dataset_final.csv
    
   How mayn rows have that dataset"""
    response = make_llm_request(prompt)
    print("Response:\n", response)
