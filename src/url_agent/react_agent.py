"""Provider-agnostic ReAct agent for web crawling."""

import json
from urllib.parse import urlparse
from url_agent.providers.base import LLMProvider
from url_agent.web_fetcher import fetch, same_origin


class ReactAgent:
    """Provider-agnostic ReAct agent for web crawling."""

    def __init__(self, provider: LLMProvider):
        """Initialize ReactAgent with a specific LLM provider.

        Args:
            provider: LLMProvider instance (OpenAI, Ollama, or Anthropic)
        """
        self.provider = provider

        # Define tools once for reuse
        self.tools = [
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

    def build_observation(
        self,
        root_url: str,
        corpus: list,
        available_links: list,
        max_depth: int,
        max_pages: int,
        last_error: str | None
    ) -> str:
        """Build a text observation for the LLM that describes the current state.

        Args:
            root_url: Root URL being crawled
            corpus: List of crawled pages with url, depth, text
            available_links: List of discovered but not yet visited links
            max_depth: Maximum crawl depth
            max_pages: Maximum pages to crawl
            last_error: Error from last action (if any)

        Returns:
            Formatted observation string
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

    def react_step(self, observation: str) -> dict:
        """Make one ReAct step: send observation to LLM with tools, return chosen action.

        Args:
            observation: Current state observation

        Returns:
            Tool call dict with {"name": str, "arguments": dict}
        """
        system_prompt = "You are a web crawling agent. Your goal is to efficiently gather comprehensive information about a website."

        return self.provider.call_with_tools(system_prompt, observation, self.tools)

    def synthesize(self, corpus: list, root_url: str) -> str:
        """Synthesize final output using the configured provider.

        Args:
            corpus: List of crawled pages with url, depth, text
            root_url: Root URL that was crawled

        Returns:
            JSON string with structured output
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

        system_prompt = "You are a technical analyst. Synthesize the crawled content into structured output."

        # Limit prompt length to avoid token limits
        return self.provider.synthesize_json(system_prompt, prompt[:240000])

    def crawl(self, url: str, max_depth: int, max_pages: int) -> str:
        """Main ReAct loop - provider-agnostic.

        Args:
            url: Root URL to crawl
            max_depth: Maximum crawl depth
            max_pages: Maximum pages to crawl

        Returns:
            JSON string with structured analysis
        """
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
            observation = self.build_observation(
                root_url=url,
                corpus=corpus,
                available_links=[u for u in all_discovered_links if u not in visited],
                max_depth=max_depth,
                max_pages=max_pages,
                last_error=last_error
            )

            # LLM reasons and chooses action (with tools)
            tool_call = self.react_step(observation)

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
        return self.synthesize(corpus, url)
