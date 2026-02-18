# URL Agent

MCP server for intelligent web crawling using a ReAct agent. Adaptively explores websites and returns structured analysis.

## Features

- **ReAct Loop**: Agent reasons about which links to follow
- **Multiple Providers**: OpenAI, Anthropic Claude, or local Ollama
- **Structured Output**: Returns JSON with features, requirements, APIs, edge cases, and implementation notes
- **MCP Server**: Single `summarize_url` tool for IDE integration

## Quick Start

### Using Docker (Recommended)

```bash
docker build -t url-agent .
docker run --rm -i -e OPENAI_API_KEY=your_key url-agent
```

### Local Installation

```bash
# Install dependencies
uv sync

# Run the server
uv run urlagent
```

## Configuration

Set via environment variables or `.env` file:

```bash
MODEL_PROVIDER=openai              # openai, anthropic, or ollama
OPENAI_MODEL=gpt-4o-mini          # Model name for any provider
OPENAI_API_KEY=your_key           # For OpenAI
ANTHROPIC_API_KEY=your_key        # For Anthropic
OLLAMA_BASE_URL=http://localhost:11434/v1  # For Ollama (optional)
```

**Using Ollama (local, free):**

```bash
ollama pull llama3
export MODEL_PROVIDER=ollama
export OPENAI_MODEL=llama3
uv run urlagent
```

**Using Anthropic Claude:**

```bash
export MODEL_PROVIDER=anthropic
export OPENAI_MODEL=claude-3-5-sonnet-20241022
export ANTHROPIC_API_KEY=your_key
uv run urlagent
```

## MCP Integration

**Option 1: Docker**

```json
{
  "mcpServers": {
    "url-agent": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "-e", "OPENAI_API_KEY=YOUR_KEY", "url-agent"]
    }
  }
}
```

**Option 2: Local (after `uv sync`)**

```json
{
  "mcpServers": {
    "url-agent": {
      "command": "urlagent",
      "env": {
        "OPENAI_API_KEY": "YOUR_KEY"
      }
    }
  }
}
```

## Usage

Once registered with your MCP client:

```
Use summarize_url on https://example.com
```

The agent will:
1. Fetch the root page
2. Intelligently explore promising links
3. Stop when it has enough information or hits limits
4. Return structured JSON analysis

## Tool Parameters

```
summarize_url(
  url: str,           # URL to analyze
  max_depth: int = 2, # Maximum crawl depth
  max_pages: int = 4  # Maximum pages to fetch
)
```

## Project Structure

```
url-agent/
  src/url_agent/      # Main package
    server.py         # MCP server entry point
    react_agent.py    # ReAct loop logic
    web_fetcher.py    # Web scraping utilities
    providers/        # LLM provider implementations
  pyproject.toml
  Dockerfile
```

## License

Apache 2.0
