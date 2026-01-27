# Copy uv from official image
FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:3.12-slim

WORKDIR /app

ARG GUARDRAILS_API_KEY

# Copy uv binary from the official image
COPY --from=uv /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

# install guardrails
RUN echo "n" | uv run guardrails configure --token ${GUARDRAILS_API_KEY} --enable-metrics
RUN uv run guardrails hub install hub://guardrails/detect_jailbreak --quiet

COPY . .

CMD ["uv", "run", "python", "main.py"]
