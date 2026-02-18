"""Ollama provider implementation."""

from openai import OpenAI
from .openai_provider import OpenAIProvider


class OllamaProvider(OpenAIProvider):
    """Ollama provider using OpenAI-compatible API.

    Ollama provides an OpenAI-compatible API at localhost:11434/v1,
    so we can reuse the OpenAI provider with a custom base_url.
    """

    def __init__(self, model: str, base_url: str = "http://localhost:11434/v1"):
        """Initialize Ollama provider.

        Args:
            model: Model name (e.g., "llama3")
            base_url: Ollama API base URL (default: http://localhost:11434/v1)
        """
        self.client = OpenAI(base_url=base_url, api_key="ollama")
        self.model = model
