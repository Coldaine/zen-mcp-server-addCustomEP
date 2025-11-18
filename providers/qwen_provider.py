"""Qwen provider for native Qwen API models."""

import os

from .base import ModelCapabilities, ProviderType
from .openai_compatible import OpenAICompatibleProvider


class QwenProvider(OpenAICompatibleProvider):
    """Provider for Qwen models via native Qwen API."""

    def __init__(self, api_key=None, **kwargs):
        super().__init__(
            api_key=api_key or os.getenv("QWEN_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            **kwargs,
        )

    def get_provider_type(self) -> ProviderType:
        return ProviderType.QWEN

    def validate_model_name(self, model_name: str) -> bool:
        # Qwen supports qwen, qwen2, qwen3, qwq series
        return (
            model_name.startswith("qwen")
            or model_name.startswith("qw")
            or model_name == "qwen3-0.6b"
            or model_name == "qwen3max"
        )

    def get_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get model capabilities for Qwen models."""
        # Default capabilities for Qwen models
        context_window = 128000
        max_output = 32768
        supports_thinking = False

        # Specific configurations for known models
        if "qwen3max" in model_name.lower():
            context_window = 262144
            max_output = 32768
            supports_thinking = True
        elif "qwen2" in model_name.lower():
            context_window = 128000
            max_output = 32768
        elif "qwen3-0.6b" in model_name.lower():
            context_window = 32768
            max_output = 8192

        return ModelCapabilities(
            model_name=model_name,
            friendly_name="Qwen",
            provider=ProviderType.QWEN,
            context_window=context_window,
            max_output_tokens=max_output,
            supports_extended_thinking=supports_thinking,
        )
