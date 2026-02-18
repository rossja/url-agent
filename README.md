# URL Agent — ReAct Loop (MCP Tool)

Adaptive autonomous URL ingestion agent with:

- ReAct (Reason + Act) loop architecture
- Intelligent, adaptive crawling
- Structured synthesis output
- MCP server interface
- Docker support

---

# Overview

This project demonstrates an adaptive agent using the ReAct pattern:

1. Fetch root URL
2. Enter ReAct loop where the agent:
   - Observes current state (crawled pages, available links, errors)
   - Reasons about what to do next (using LLM with function calling)
   - Acts by either fetching a promising URL or finishing early
3. Synthesize structured output from gathered content

The agent exposes a single MCP tool:

```
summarize_url(url: str, max_depth: int = 2, max_pages: int = 4)
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

> "Use summarize_url on https://example.com and help implement what it describes."

The agent will:

1. Fetch the root page
2. Adaptively explore promising same-origin links based on their content
3. Stop early when sufficient information is gathered (or hit max_pages limit)
4. Handle errors gracefully (dead links, timeouts, etc.)
5. Return structured JSON suitable for code generation

---

# Environment Variables

| Variable        | Default       | Description                              |
|----------------|--------------|------------------------------------------|
| OPENAI_MODEL   | gpt-4o-mini  | Model used for ReAct steps + synthesis   |
| OPENAI_API_KEY | required     | OpenAI API key                          |

---

# Design Notes

- Uses ReAct (Reason + Act) loop with OpenAI function calling
- Agent adaptively chooses which links to explore based on content
- Agent can stop early via `finish()` tool when it has sufficient information
- Crawl is bounded by hard limits (`max_depth` and `max_pages`)
- Same-origin links only
- Errors are passed to agent as observations for adaptive recovery
- Synthesis happens at the end (single LLM call)

This makes the agent more intelligent and adaptive while maintaining safety through hard limits.

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

