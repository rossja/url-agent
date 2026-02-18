"""OpenAI provider implementation."""

import json
from openai import OpenAI
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, model: str, api_key: str = None):
        """Initialize OpenAI provider.

        Args:
            model: Model name (e.g., "gpt-4o-mini")
            api_key: OpenAI API key (if None, uses OPENAI_API_KEY env var)
        """
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.model = model

    def call_with_tools(self, system_prompt: str, user_message: str, tools: list) -> dict:
        """Call OpenAI with tool definitions.

        Args:
            system_prompt: System instructions for the LLM
            user_message: User message/observation
            tools: List of tool definitions in OpenAI format

        Returns:
            Standardized dict with tool call: {"name": str, "arguments": dict}
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
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

    def synthesize_json(self, system_prompt: str, user_message: str) -> str:
        """Call OpenAI to produce structured JSON output.

        Args:
            system_prompt: System instructions for the LLM
            user_message: User message with JSON requirements

        Returns:
            JSON string
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"}
        )

        return resp.choices[0].message.content
