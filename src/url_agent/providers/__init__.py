"""Provider factory for LLM providers."""

import os
from .base import LLMProvider
from .openai_provider import OpenAIProvider
from .ollama_provider import OllamaProvider
from .anthropic_provider import AnthropicProvider


def get_provider(provider_name: str, model: str) -> LLMProvider:
    """Factory function to create provider based on config.

    Args:
        provider_name: Provider name ("openai", "ollama", or "anthropic")
        model: Model name to use

    Returns:
        Configured LLMProvider instance

    Raises:
        ValueError: If provider_name is not recognized
    """
    provider_name = provider_name.lower()

    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        return OpenAIProvider(model, api_key)

    elif provider_name == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        return OllamaProvider(model, base_url)

    elif provider_name == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required for Anthropic provider"
            )
        return AnthropicProvider(model, api_key)

    else:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Supported providers: openai, ollama, anthropic"
        )


__all__ = ["LLMProvider", "OpenAIProvider", "OllamaProvider", "AnthropicProvider", "get_provider"]
