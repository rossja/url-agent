import json, os
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from openai import OpenAI
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# override=True ensures .env takes precedence over existing env vars
load_dotenv(override=True)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "openai").lower()

# Configure client based on provider
if MODEL_PROVIDER == "ollama":
    # Ollama uses OpenAI-compatible API at localhost:11434
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    client = OpenAI(base_url=base_url, api_key="ollama")
elif MODEL_PROVIDER == "openai":
    client = OpenAI()  # Uses OPENAI_API_KEY from environment
else:
    raise ValueError(f"Unknown MODEL_PROVIDER: {MODEL_PROVIDER}")
mcp = FastMCP("url-agent")

def fetch(url: str, timeout=20) -> tuple[str, list[str]]:
    r = httpx.get(url, timeout=timeout, follow_redirects=True)
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    links = [a.get("href") for a in soup.find_all("a", href=True)]
    links = [urljoin(url, h) for h in links if h]
    return text[:20000], links[:60]

def same_origin(root: str, u: str) -> bool:
    return urlparse(root).netloc == urlparse(u).netloc

def build_observation(
    root_url: str,
    corpus: list,
    available_links: list,
    max_depth: int,
    max_pages: int,
    last_error: str | None
) -> str:
    """
    Build a text observation for the LLM that describes the current state.
    """
    obs = []

    obs.append("# Current Crawl State")
    obs.append(f"Root URL: {root_url}")
    obs.append(f"Pages fetched: {len(corpus)}/{max_pages}")
    obs.append(f"Max depth: {max_depth}")
    obs.append("")

    obs.append("## Corpus Summary")
    for item in corpus:
        obs.append(f"- [{item['depth']}] {item['url']}")
        obs.append(f"  Preview: {item['text'][:200]}...")
    obs.append("")

    obs.append("## Available Links (not yet visited)")
    for link in available_links[:20]:  # Limit to 20 to avoid token bloat
        obs.append(f"- {link}")
    if len(available_links) > 20:
        obs.append(f"  ... and {len(available_links) - 20} more")
    obs.append("")

    if last_error:
        obs.append(f"## Last Action Error")
        obs.append(f"⚠️ {last_error}")
        obs.append("")

    obs.append("## Your Task")
    obs.append("Analyze the current state and decide:")
    obs.append("- Call `fetch_url(url, reason)` to explore a promising link")
    obs.append("- Call `finish(reason)` if you have sufficient information")
    obs.append("")
    obs.append("Choose wisely to gather comprehensive information efficiently.")

    return "\n".join(obs)

def react_step(observation: str) -> dict:
    """
    Make one ReAct step: send observation to LLM with tools, return chosen action.
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "fetch_url",
                "description": "Fetch and analyze a URL. Returns page content and links.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "reason": {"type": "string"}
                    },
                    "required": ["url", "reason"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "finish",
                "description": "Stop crawling. Call when you have sufficient information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {"type": "string"}
                    },
                    "required": ["reason"]
                }
            }
        }
    ]

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a web crawling agent. Your goal is to efficiently gather comprehensive information about a website."},
            {"role": "user", "content": observation}
        ],
        tools=tools,
        tool_choice="required"  # Force tool call (no free-form text)
    )

    # Extract tool call
    tool_call = resp.choices[0].message.tool_calls[0]

    return {
        "name": tool_call.function.name,
        "arguments": json.loads(tool_call.function.arguments)
    }

def synthesize_react(corpus: list, root_url: str) -> str:
    """
    Synthesize final structured output from crawled corpus.
    Similar to original synthesize() but adapted for ReAct output.
    """
    # Build synthesis prompt
    prompt_parts = []
    prompt_parts.append(f"# URL Analysis Task")
    prompt_parts.append(f"Root URL: {root_url}")
    prompt_parts.append(f"")
    prompt_parts.append(f"## Crawled Pages ({len(corpus)} total)")

    for item in corpus:
        prompt_parts.append(f"### {item['url']} (depth {item['depth']})")
        prompt_parts.append(item['text'])
        prompt_parts.append("")

    prompt_parts.append("## Output Requirements")
    prompt_parts.append("Synthesize the above into structured JSON:")
    prompt_parts.append(json.dumps({
        "feature_summary": "Brief description of what this website/tool does",
        "key_requirements": ["List of important requirements or features"],
        "interfaces_or_artifacts": ["APIs, schemas, configs, etc."],
        "edge_cases": ["Notable limitations or edge cases"],
        "implementation_notes": ["Technical details for implementation"]
    }, indent=2))

    prompt = "\n".join(prompt_parts)

    # Call LLM for synthesis
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a technical analyst. Synthesize the crawled content into structured output."},
            {"role": "user", "content": prompt[:240000]}  # Token limit
        ],
        response_format={"type": "json_object"}
    )

    return resp.choices[0].message.content

@mcp.tool()
def summarize_url(url: str, max_depth: int = 2, max_pages: int = 4) -> str:
    """Main entry point with ReAct loop."""

    # Initialize state
    corpus = []
    visited = set()
    all_discovered_links = []
    last_error = None

    # Fetch root URL
    try:
        root_text, root_links = fetch(url)
        visited.add(url)
        corpus.append({"url": url, "depth": 0, "text": root_text[:12000]})
        all_discovered_links.extend([u for u in root_links if same_origin(url, u)])
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch root URL: {str(e)}"})

    # ReAct loop
    while len(corpus) < max_pages:
        # Build observation for LLM
        observation = build_observation(
            root_url=url,
            corpus=corpus,
            available_links=[u for u in all_discovered_links if u not in visited],
            max_depth=max_depth,
            max_pages=max_pages,
            last_error=last_error
        )

        # LLM reasons and chooses action (with tools)
        tool_call = react_step(observation)

        if tool_call["name"] == "finish":
            # Agent decided it has enough info
            break

        elif tool_call["name"] == "fetch_url":
            target_url = tool_call["arguments"]["url"]
            reason = tool_call["arguments"]["reason"]

            # Validate URL
            if target_url in visited:
                last_error = f"URL already visited: {target_url}"
                continue

            if not same_origin(url, target_url):
                last_error = f"URL not same-origin: {target_url}"
                continue

            # Determine depth (simple heuristic: count path segments)
            depth = urlparse(target_url).path.count('/') if urlparse(target_url).path else 1
            if depth > max_depth:
                last_error = f"URL exceeds max_depth: {target_url}"
                continue

            # Attempt fetch
            try:
                text, links = fetch(target_url)
                visited.add(target_url)
                corpus.append({"url": target_url, "depth": depth, "text": text[:12000]})

                # Add newly discovered links
                new_links = [u for u in links if same_origin(url, u) and u not in all_discovered_links]
                all_discovered_links.extend(new_links)

                last_error = None  # Clear error on success

            except Exception as e:
                last_error = f"Failed to fetch {target_url}: {str(e)}"
                # Continue loop - agent will see error in next observation

    # Synthesize final output
    return synthesize_react(corpus, url)

if __name__ == "__main__":
    mcp.run()
