FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
RUN uv sync

COPY url_agent.py /app/url_agent.py

ENV OPENAI_MODEL=gpt-4o-mini
CMD ["uv", "run", "python", "url_agent.py"]
