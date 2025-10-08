#Taking inspiration from:
#https://github.com/astral-sh/uv-docker-example/blob/main/Dockerfile
# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set the working directory in the container
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    curl libsnappy-dev make gcc g++ libc6-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (to leverage caching)
COPY pyproject.toml uv.lock ./

#Copy models file
COPY models ./models

# Copy the rest of the application code
COPY src ./src

# Install project dependencies using uv
RUN uv sync --locked --no-dev

# Expose the application port
EXPOSE 8000

# Run the application with uv
CMD ["uv", "run", "uvicorn", "lab01_lib.app:app", "--host", "0.0.0.0", "--port", "8000"]