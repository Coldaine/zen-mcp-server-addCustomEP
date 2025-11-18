"""Kilo Code provider for OpenRouter models via Kilo endpoint."""

import os

from .base import ModelCapabilities, ProviderType
from .openai_compatible import OpenAICompatibleProvider


class KiloProvider(OpenAICompatibleProvider):
    """Provider for Kilo Code API, substituting for OpenRouter models."""

    def __init__(self, api_key=None, **kwargs):
        # Kilo uses the same API format as OpenAI/OpenRouter
        super().__init__(
            api_key=api_key or os.getenv("KILO_API_KEY"), base_url="https://api.kilocodex.com/v1", **kwargs
        )

    def get_provider_type(self) -> ProviderType:
        return ProviderType.KILO

    def validate_model_name(self, model_name: str) -> bool:
        # Kilo supports OpenRouter models; validate against OpenRouter registry for compatibility
        from .openrouter_registry import OpenRouterModelRegistry

        return OpenRouterModelRegistry().resolve(model_name) is not None

    def get_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get model capabilities for Kilo-proxied models."""
        # Delegate to OpenRouter registry for capabilities, as Kilo forwards to OpenRouter
        from .openrouter_registry import OpenRouterModelRegistry

        config = OpenRouterModelRegistry().resolve(model_name)
        if config:
            # Update provider to KILO while keeping other capabilities
            config.provider = ProviderType.KILO
            return config
        # Fallback for unknown models
        return ModelCapabilities(
            model_name=model_name,
            friendly_name="Kilo",
            provider=ProviderType.KILO,
            context_window=128000,
            max_output_tokens=32768,
        )
