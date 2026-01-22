import time

from openai import OpenAI


def benchmark_execution_time(messages: list[dict]) -> None:
    # those settings use vLLM server
    client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")
    for idx, user_message in enumerate(messages):
        chat_response = client.chat.completions.create(
            model="",  # use the default server model
            messages=[{"role": "developer", "content": "You are a helpful assistant."}, user_message],
            max_completion_tokens=1000,
            # turn off thinking for Qwen with /no_think
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )

        content = chat_response.choices[0].message.content.strip()
        print(f"Message {idx + 1} Response:\n", content)


if __name__ == "__main__":
    messages = [
        {"role": "user", "content": "How important is LLMOps on scale 0-10?"},
        {"role": "user", "content": "What are the main differences between Docker and Kubernetes?"},
        {"role": "user", "content": "Explain machine learning in one sentence."},
        {"role": "user", "content": "Rate the importance of data quality in ML projects on a scale of 0-10."},
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "user", "content": "Write a Python function to calculate factorial of a number."},
        {"role": "user", "content": "How would you handle missing data in a dataset?"},
        {"role": "user", "content": "What are the benefits of using vector databases?"},
        {"role": "user", "content": "Explain the difference between supervised and unsupervised learning."},
        {"role": "user", "content": "On a scale of 0-10, how important is model monitoring in production?"},
    ]

    start = time.time()
    benchmark_execution_time(messages)
    stop = time.time()

    print(f"Total execution time: {stop - start} seconds")
