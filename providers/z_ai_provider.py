"""Z.AI provider for GLM-4.5 models."""

import os

from .base import ModelCapabilities, ProviderType, RangeTemperatureConstraint
from .openai_compatible import OpenAICompatibleProvider


class ZAIProvider(OpenAICompatibleProvider):
    """Provider for Z.AI GLM-4.5 models."""

    def __init__(self, api_key=None, **kwargs):
        super().__init__(
            api_key=api_key or os.getenv("Z_AI_API_KEY"),
            base_url="https://api.z.ai/api/paas/v4/chat/completions",
            **kwargs,
        )

    def get_provider_type(self) -> ProviderType:
        return ProviderType.Z_AI

    def validate_model_name(self, model_name: str) -> bool:
        # Z.AI supports glm-4.5 series
        return model_name.startswith("glm-") or model_name == "glm-4.5"

    def get_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get model capabilities for Z.AI models."""
        return ModelCapabilities(
            model_name=model_name,
            friendly_name="Z.AI",
            provider=ProviderType.Z_AI,
            context_window=262144,
            max_output_tokens=32768,
            supports_extended_thinking=True,
            temperature_constraint=RangeTemperatureConstraint(0.0, 2.0, 1.0),
        )
