"""Anthropic provider implementation."""

from anthropic import Anthropic
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(self, model: str, api_key: str = None):
        """Initialize Anthropic provider.

        Args:
            model: Model name (e.g., "claude-3-5-sonnet-20241022")
            api_key: Anthropic API key (if None, uses ANTHROPIC_API_KEY env var)
        """
        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()
        self.model = model

    def call_with_tools(self, system_prompt: str, user_message: str, tools: list) -> dict:
        """Call Anthropic with tool definitions.

        Args:
            system_prompt: System instructions for the LLM
            user_message: User message/observation
            tools: List of tool definitions in OpenAI format

        Returns:
            Standardized dict with tool call: {"name": str, "arguments": dict}
        """
        # Convert OpenAI tool format to Anthropic format
        anthropic_tools = []
        for tool in tools:
            func = tool["function"]
            anthropic_tools.append({
                "name": func["name"],
                "description": func["description"],
                "input_schema": func["parameters"]
            })

        # Enhance system prompt to encourage tool use
        enhanced_system = f"""{system_prompt}

IMPORTANT: You MUST respond by calling one of the available tools.
Do not provide a text response without calling a tool."""

        # Call Anthropic API
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=enhanced_system,
            messages=[{"role": "user", "content": user_message}],
            tools=anthropic_tools
        )

        # Parse tool_use blocks from response
        for block in resp.content:
            if block.type == "tool_use":
                return {
                    "name": block.name,
                    "arguments": block.input
                }

        # If no tool_use block found, raise error
        raise ValueError("Anthropic response did not contain a tool_use block")

    def synthesize_json(self, system_prompt: str, user_message: str) -> str:
        """Call Anthropic to produce structured JSON output.

        Args:
            system_prompt: System instructions for the LLM
            user_message: User message with JSON requirements

        Returns:
            JSON string
        """
        # Enhance system prompt for JSON output
        enhanced_system = f"""{system_prompt}

You MUST respond with valid JSON only. No markdown formatting, no other text.
Output only the JSON object."""

        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=enhanced_system,
            messages=[{"role": "user", "content": user_message}]
        )

        # Extract text from first content block
        for block in resp.content:
            if block.type == "text":
                return block.text

        raise ValueError("Anthropic response did not contain a text block")
