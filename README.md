# URL Agent — Single-Pass Planner (MCP Tool)

Minimal autonomous URL ingestion agent with:

- Single-pass LLM planning
- Deterministic execution
- Structured synthesis output
- MCP server interface
- Docker support

---

# Overview

This project demonstrates a narrow but functional definition of an “agent”:

1. Fetch root URL
2. Use one LLM call to generate a bounded crawl plan
3. Execute that plan deterministically
4. Use one LLM call to synthesize structured output

The agent exposes a single MCP tool:

```
agent_summarize_url(url: str, max_depth: int = 2, max_pages: int = 4)
```

It returns structured JSON describing:

- Feature summary
- Key requirements
- Interfaces / artifacts
- Edge cases
- Implementation notes

---

# Project Structure

```
url_agent/
  url_agent.py
  pyproject.toml
  Dockerfile
```

---

# Requirements

- Docker (recommended)
- OpenAI API key

---

# Build

From the directory containing the Dockerfile:

```bash
docker build -t url-agent .
```

---

# Run (MCP server over stdio)

```bash
docker run --rm -i \
  -e OPENAI_API_KEY=your_key_here \
  url-agent
```

The container runs an MCP server over standard I/O.

---

# MCP Configuration Example

Example MCP client configuration:

```json
{
  "mcpServers": {
    "url-agent": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "OPENAI_API_KEY=YOUR_KEY",
        "url-agent"
      ]
    }
  }
}
```

Replace `YOUR_KEY` with your actual key or inject it via your IDE’s secret manager.

---

# Usage Example (Agentic IDE)

Once registered:

> “Use agent_summarize_url on https://example.com and help implement what it describes.”

The agent will:

1. Fetch the page
2. Decide which same-origin links to follow
3. Aggregate relevant content
4. Return structured JSON suitable for code generation

---

# Environment Variables

| Variable        | Default       | Description                          |
|----------------|--------------|--------------------------------------|
| OPENAI_MODEL   | gpt-4o-mini  | Model used for planning + synthesis  |
| OPENAI_API_KEY | required     | OpenAI API key                      |

---

# Design Notes

- Planning is single-pass (one LLM call)
- Execution is deterministic
- Synthesis is single-pass
- Crawl is bounded by `max_depth` and `max_pages`
- Same-origin links only

This keeps autonomy minimal, observable, and constrained.

---

# Local (Non-Docker) Development

If you prefer uv locally:

```bash
uv sync
uv run python url_agent.py
```

---

# License

Apache 2 License

