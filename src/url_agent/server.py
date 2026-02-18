"""URL Agent - MCP server for web crawling with ReAct agent.

This is the main entry point that wires together:
- Provider factory (OpenAI, Ollama, Anthropic)
- ReactAgent (provider-agnostic ReAct logic)
- MCP server (tool interface)
"""

import os
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from url_agent.providers import get_provider
from url_agent.react_agent import ReactAgent

# Load environment variables from .env file if it exists
# override=True ensures .env takes precedence over existing env vars
load_dotenv(override=True)

# Get configuration from environment
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "openai").lower()

# Initialize provider and agent
try:
    provider = get_provider(MODEL_PROVIDER, MODEL)
    agent = ReactAgent(provider)
except Exception as e:
    print(f"Error initializing provider: {e}")
    raise

# Initialize MCP server
mcp = FastMCP("url-agent")


@mcp.tool()
def summarize_url(url: str, max_depth: int = 2, max_pages: int = 4) -> str:
    """Crawl and analyze a URL using a ReAct agent.

    The agent will intelligently explore the website, deciding which links
    to follow and when to stop based on the information gathered.

    Args:
        url: Root URL to analyze
        max_depth: Maximum depth to crawl (default: 2)
        max_pages: Maximum number of pages to fetch (default: 4)

    Returns:
        JSON string with structured analysis containing:
        - feature_summary: Brief description of what the website/tool does
        - key_requirements: List of important requirements or features
        - interfaces_or_artifacts: APIs, schemas, configs, etc.
        - edge_cases: Notable limitations or edge cases
        - implementation_notes: Technical details for implementation
    """
    return agent.crawl(url, max_depth, max_pages)


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
