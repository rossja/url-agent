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
url-agent/
  src/
    url_agent/              # Main package
      __init__.py           # Package marker
      __main__.py           # Entry point for 'python -m url_agent'
      server.py             # Main entry point (MCP server)
      react_agent.py        # Core ReAct logic (provider-agnostic)
      web_fetcher.py        # Web scraping utilities
      providers/
        __init__.py         # Provider factory
        base.py             # Abstract base class
        openai_provider.py  # OpenAI implementation
        ollama_provider.py  # Ollama implementation
        anthropic_provider.py # Anthropic implementation
  pyproject.toml
  Dockerfile
  README.md
```

---

# Requirements

- Docker (recommended)
- API key for your chosen provider:
  - OpenAI API key (for OpenAI models)
  - Anthropic API key (for Claude models)
  - Or use Ollama for local models (no API key needed)

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

For local runs with `uv`, you can use a `.env` file instead of exporting variables manually (see Configuration section below).

---

# MCP Configuration Example

Example MCP client configuration:

**Option 1: Using Docker (Recommended for isolation)**

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

**Option 2: Using installed package (faster, requires local install)**

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

Replace `YOUR_KEY` with your actual key or inject it via your IDE's secret manager.

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

| Variable          | Default                       | Description                                           |
|-------------------|-------------------------------|-------------------------------------------------------|
| MODEL_PROVIDER    | openai                        | Provider to use: `openai`, `ollama`, or `anthropic`  |
| OPENAI_MODEL      | gpt-4o-mini                   | Model used for ReAct steps + synthesis               |
| OPENAI_API_KEY    | required (for openai)         | OpenAI API key                                       |
| ANTHROPIC_API_KEY | required (for anthropic)      | Anthropic API key                                    |
| OLLAMA_BASE_URL   | http://localhost:11434/v1     | Ollama endpoint (optional)                           |

---

# Using Anthropic Claude Models

URL Agent supports Anthropic's Claude models, which offer excellent reasoning capabilities and strong tool use (function calling).

## Prerequisites

1. **Get an Anthropic API key**: Sign up at https://console.anthropic.com
2. **Choose a Claude model**: See model recommendations below

## Quick Start

**Option 1: Using .env file (Recommended)**

```bash
# Create and configure .env file
cp .env.example .env
# Edit .env to set:
# MODEL_PROVIDER=anthropic
# OPENAI_MODEL=claude-3-5-sonnet-20241022
# ANTHROPIC_API_KEY=your-api-key-here

# Run the agent (automatically loads .env)
uv run urlagent
```

**Option 2: Using environment variables**

```bash
# Set environment variables
export MODEL_PROVIDER=anthropic
export OPENAI_MODEL=claude-3-5-sonnet-20241022
export ANTHROPIC_API_KEY=your-api-key-here

# Run the agent
uv run urlagent
```

## Model Recommendations

**Recommended (Production)**:
- `claude-3-5-sonnet-20241022` - Best balance of speed, cost, and capability
- Strong tool use and structured output
- Excellent at following instructions

**Maximum Quality**:
- `claude-3-opus-20240229` - Most capable Claude model
- Use for complex multi-page sites requiring deep reasoning
- Higher cost and slower than Sonnet

**Development/Testing**:
- `claude-3-haiku-20240307` - Fast and economical
- Good for testing and simple sites
- May struggle with complex multi-step reasoning

## MCP Configuration with Anthropic

Example MCP client configuration for using url-agent with Claude:

```json
{
  "mcpServers": {
    "url-agent-claude": {
      "command": "urlagent",
      "env": {
        "MODEL_PROVIDER": "anthropic",
        "OPENAI_MODEL": "claude-3-5-sonnet-20241022",
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Note: This assumes you've installed url-agent with `uv sync`. If you prefer to run from source without installing, use `uv --directory /path/to/url-agent run urlagent` as the command.

## Docker Usage with Anthropic

```bash
docker run --rm -i \
  -e MODEL_PROVIDER=anthropic \
  -e OPENAI_MODEL=claude-3-5-sonnet-20241022 \
  -e ANTHROPIC_API_KEY=your-api-key-here \
  url-agent
```

## Why Use Anthropic?

**Advantages**:
- Excellent reasoning and tool use capabilities
- Strong at following complex instructions
- Good balance of speed and quality with Sonnet models
- Competitive pricing

**Considerations**:
- Requires API key and internet connection (unlike Ollama)
- API costs per request (though Sonnet is very cost-effective)
- Rate limits on API usage

---

# Using Local Models with Ollama

URL Agent supports running with local Ollama models as a cost-free, privacy-preserving alternative to cloud-based OpenAI models.

## Prerequisites

1. **Install Ollama**: Download from https://ollama.ai
2. **Pull a model**: Run `ollama pull llama3` (or any model you prefer)
3. **Verify Ollama is running**: Run `ollama list` to see installed models

## Quick Start (Local Usage)

This is the primary use case - running both Ollama and url-agent locally.

**Option 1: Using .env file (Recommended)**

```bash
# Check what models you have installed
ollama list

# Create and configure .env file
cp .env.example .env
# Edit .env to set MODEL_PROVIDER=ollama and OPENAI_MODEL=your-model

# Run the agent (automatically loads .env)
uv run urlagent
```

**Option 2: Using environment variables**

```bash
# Set environment variables
export MODEL_PROVIDER=ollama
export OPENAI_MODEL=llama3  # or whatever model you have

# Run the agent
uv run urlagent
```

## Configuration with .env File (Recommended)

Create a `.env` file for persistent configuration:

```bash
cp .env.example .env
```

Edit `.env` to configure your provider and model:

```bash
MODEL_PROVIDER=ollama
OPENAI_MODEL=llama3
```

The `.env` file is automatically loaded when you run the agent:

```bash
uv run urlagent
```

No need to manually export variables - the agent loads them automatically from `.env`.

## Model Selection and Function Calling Quality

**Important**: Not all Ollama models handle function calling equally well. The ReAct loop relies on the model's ability to correctly use the `fetch_url` and `finish` tools.

**Recommendations**:
- Models with strong instruction-following work best
- Larger parameter counts generally perform better
- Test your specific model - if function calling fails, try a different model

**Popular models to try**:
```bash
ollama pull llama3          # Good balance of size/quality
ollama pull mistral         # Fast and capable
ollama pull qwen2.5         # Strong reasoning abilities
```

## MCP Configuration with Ollama

Example MCP client configuration for using url-agent with Ollama:

```json
{
  "mcpServers": {
    "url-agent-ollama": {
      "command": "urlagent",
      "env": {
        "MODEL_PROVIDER": "ollama",
        "OPENAI_MODEL": "llama3"
      }
    }
  }
}
```

Note: This assumes you've installed url-agent with `uv sync`. If you prefer to run from source without installing, use `uv --directory /path/to/url-agent run urlagent` as the command.

## Docker Usage (Advanced)

If you're running url-agent in Docker while Ollama is on the host machine, you need to adjust the `OLLAMA_BASE_URL`:

**macOS/Windows**:
```bash
docker run --rm -i \
  -e MODEL_PROVIDER=ollama \
  -e OPENAI_MODEL=llama3 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434/v1 \
  url-agent
```

**Linux**:
```bash
# Option 1: Use host networking
docker run --rm -i --network host \
  -e MODEL_PROVIDER=ollama \
  -e OPENAI_MODEL=llama3 \
  url-agent

# Option 2: Use host IP address
docker run --rm -i \
  -e MODEL_PROVIDER=ollama \
  -e OPENAI_MODEL=llama3 \
  -e OLLAMA_BASE_URL=http://172.17.0.1:11434/v1 \
  url-agent
```

## Troubleshooting

### "Connection refused" or "Cannot connect to Ollama"

**Check if Ollama is running**:
```bash
ollama list
```

If this fails, start Ollama (it usually runs as a background service after installation).

**Verify the endpoint**:
```bash
curl http://localhost:11434/v1/models
```

Should return a JSON response with available models.

### "Model not found"

**List installed models**:
```bash
ollama list
```

**Pull the model you want**:
```bash
ollama pull llama3
```

### Function calling errors or invalid tool calls

Some models struggle with function calling. Try:
1. A different model (larger models generally work better)
2. Setting a lower `max_pages` limit to reduce complexity
3. Checking Ollama logs for hints: `ollama logs`

### Performance is slow

- Ollama runs models locally - inference speed depends on your hardware
- Larger models (70B+) require significant RAM/VRAM
- Consider using smaller models (7B-13B) for faster responses
- GPU acceleration significantly improves speed (Ollama uses GPU automatically if available)

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
# Install the package in development mode
uv sync

# Run the server
uv run urlagent
```

Alternatively, you can run it as a module:

```bash
uv run python -m url_agent
```

---

# License

Apache 2 License

