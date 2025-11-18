"""Moonshot AI provider for kimi-k2 models."""

import os

from .base import ModelCapabilities, ProviderType
from .openai_compatible import OpenAICompatibleProvider


class MoonshotProvider(OpenAICompatibleProvider):
    """Provider for Moonshot AI models (e.g., kimi-k2-instruct)."""

    def __init__(self, api_key=None, **kwargs):
        super().__init__(
            api_key=api_key or os.getenv("MOONSHOT_API_KEY"), base_url="https://api.moonshot.cn/v1", **kwargs
        )

    def get_provider_type(self) -> ProviderType:
        return ProviderType.MOONSHOT

    def validate_model_name(self, model_name: str) -> bool:
        # Moonshot supports kimi-k2 series
        return model_name.startswith("kimi-") or model_name == "kimi-k2-instruct"

    def get_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get model capabilities for Moonshot models."""
        return ModelCapabilities(
            model_name=model_name,
            friendly_name="Moonshot",
            provider=ProviderType.MOONSHOT,
            context_window=262144,
            max_output_tokens=32768,
            supports_extended_thinking=True,
        )
