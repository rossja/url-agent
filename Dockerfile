FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml /app/pyproject.toml

# Install dependencies
RUN uv sync

# Copy the entire source package
COPY src /app/src

# Set default environment
ENV OPENAI_MODEL=gpt-4o-mini

# Run via the entry point
CMD ["uv", "run", "urlagent"]
