git commit --amend --no-edit ## Thoughts on vLLM setup on macOS

As I'm a macOS user and the provided pyproject.toml didn't work for me because of hardware setup, I followed the official vLLM guide to set it up: https://docs.vllm.ai/en/latest/getting_started/installation/cpu/#apple-silicon I cloned the repo and installed it by `uv pip install -r requirements/cpu.txt --index-strategy unsafe-best-match`. The problem is that currently there are no pre-compiled Python wheels or distributions for macOS users but only for Linux users (with GPU acceleration I believe). It's a common practice in the ML world as I believe Linux + GPU + CUDA is the most frequently used setup. I often find official paper repositories that have hardcoded `.cuda()` in every place and make it impossible to run outside the Linux + GPU + CUDA setup.

Later I found that there is [vllm-metal](https://github.com/vllm-project/vllm-metal) which is a plugin that enables vLLM to run on Apple Silicon Macs using MLX as the primary compute backend. `It unifies MLX and PyTorch under a single lowering path`. I needed to change the project Python version to `3.12` (there were problems with `3.11`) and then simply execute `uv add vllm-metal`. That repository provides a script that installs both vLLM and vllm-metal as a plugin, but it creates a new venv in the `$HOME` directory called `.venv-vllm-metal`. That script installs vLLM in the same way that I mentioned above, so I prefer to install vLLM manually and add the vllm-metal plugin with `uv add vllm-metal` and in that way I have everything in one venv.


It turned out that installing vllm-metal directly with uv doesn't work and the GPU is not utilized. Again I switched approaches, and installed vllm-metal with vLLM directly with the script provided in the vllm-metal repo and it works. Using Metal as a backend sped up generation from 100 to 79 seconds with Qwen-3-0.6b.

I think that, right now I'll use the `.venv-vllm-metal` venv to serve vLLM, and the project venv created by uv to run app logic. If I want to use Metal GPU acceleration I have to keep that approach as Docker containers don't support Metal. If I decide to skip GPU acceleration, I believe interacting with vLLM via Docker is a better approach - again I will have to build the image by myself as vLLM officially doesn't support macOS images but it can be built from the Dockerfile that they provide via:
```bash
docker build -f docker/Dockerfile.cpu --tag vllm-cpu-env .
```

I've tried to build, received an error, found some [issue](https://github.com/vllm-project/vllm/issues/21714) about bugs with building that Docker on macOS and skipped it.

To summarize, I tried many approaches to set up vLLM on macOS and I personally vote for using it via [vllm-metal](https://github.com/vllm-project/vllm-metal) by running the script provided by the authors:
```bash
curl -fsSL https://raw.githubusercontent.com/vllm-project/vllm-metal/main/install.sh | bash
```

It's straightforward, creates a Python venv in `$HOME/.venv-vllm-metal` so we can activate that venv, serve vLLM from it and access the LLM via the `openai` library in our app logic.
For homework, I will use llm via API provider as docker is necessary.

## Exercise 1
vllm on macos doesn't support a lot of quantization methods, basically only fp32, fp16/bfloat16 are available so I tested fp32 and bf16
Here are statistics for 10 examples:
Qwen-3-1.7B:
 - fp32: 37,376 token KV cache size
 - bf16: 74,880 token KV cache size
 - fp32: 723 seconds
 - bf16: 320 seconds

Qwen-3-0.6B:
- bf16: 100 seconds
- bf16 with metal: 79 seconds

Based on that results, I decided to use Qwen-3-0.6B with bf16 and metal acceleration.

## Exercise 5
I had problem with run RestrictToTopic guardrail, it returned an error:
`The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable`