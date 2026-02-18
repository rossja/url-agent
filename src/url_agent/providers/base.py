"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Providers must implement two core methods:
    1. call_with_tools: Make LLM call with tool definitions
    2. synthesize_json: Make LLM call to produce structured JSON
    """

    @abstractmethod
    def call_with_tools(self, system_prompt: str, user_message: str, tools: list) -> dict:
        """Call LLM with tool definitions.

        Args:
            system_prompt: System instructions for the LLM
            user_message: User message/observation
            tools: List of tool definitions in OpenAI format

        Returns:
            Standardized dict with tool call: {"name": str, "arguments": dict}
        """
        pass

    @abstractmethod
    def synthesize_json(self, system_prompt: str, user_message: str) -> str:
        """Call LLM to produce structured JSON output.

        Args:
            system_prompt: System instructions for the LLM
            user_message: User message with JSON requirements

        Returns:
            JSON string
        """
        pass
