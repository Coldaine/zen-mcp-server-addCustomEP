"""Provider for Z.AI (Zhipu AI) models."""

import logging
from typing import Optional

from .openai_compatible import OpenAICompatibleProvider
from .shared import (
    ModelCapabilities,
    ProviderType,
    RangeTemperatureConstraint,
)

logger = logging.getLogger(__name__)


class ZAIProvider(OpenAICompatibleProvider):
    """Provider for Z.AI (Zhipu AI) models.
    
    Native integration with Z.AI's GLM model API.
    Uses OpenAI-compatible endpoints for chat completions.
    """

    FRIENDLY_NAME = "Z.AI"
    
    # Model configurations using ModelCapabilities objects
    SUPPORTED_MODELS = {
        "glm-4.6": ModelCapabilities(
            provider=ProviderType.ZAI,
            model_name="glm-4.6",
            friendly_name="Z.AI (GLM-4.6)",
            context_window=200_000,
            max_output_tokens=128_000,
            supports_extended_thinking=False,  # GLM-4.6 has thinking but not via extended mode
            supports_system_prompts=True,
            supports_streaming=True,
            supports_function_calling=True,
            supports_json_mode=True,
            supports_images=False,
            max_image_size_mb=0.0,
            supports_temperature=True,
            temperature_constraint=RangeTemperatureConstraint(0.0, 2.0, 1.0),
            description="GLM-4.6 (200K context, 128K output) - Advanced Chinese AI model with strong coding and reasoning capabilities",
            aliases=["glm-4.6", "glm4.6", "glm46", "flash"],
        ),
    }

    def __init__(self, api_key: str, **kwargs):
        """Initialize the Z.AI provider.
        
        Args:
            api_key: Z.AI API key for authentication
            **kwargs: Additional configuration options including base_url override
        """
        # Set Z.AI base URL - matches Z.AI docs exactly
        kwargs.setdefault("base_url", "https://api.z.ai/api/paas/v4")
        super().__init__(
            api_key=api_key,
            **kwargs,
        )

    def get_provider_type(self) -> ProviderType:
        """Get the provider type."""
        return ProviderType.ZAI
    
    def get_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get capabilities for a specific Z.AI model."""
        resolved_name = self._resolve_model_name(model_name)
        if resolved_name not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported Z.AI model: {model_name}")
        return self.SUPPORTED_MODELS[resolved_name]
    
    def validate_model_name(self, model_name: str) -> bool:
        """Validate if the model name is supported."""
        try:
            resolved_name = self._resolve_model_name(model_name)
            return resolved_name in self.SUPPORTED_MODELS
        except Exception:
            return False
    
    def _resolve_model_name(self, model_name: str) -> str:
        """Resolve model aliases to canonical names."""
        # Check if it's already a canonical name
        if model_name in self.SUPPORTED_MODELS:
            return model_name
        
        # Check aliases
        for canonical_name, capabilities in self.SUPPORTED_MODELS.items():
            if model_name in capabilities.aliases:
                return canonical_name
        
        # Return as-is if no match (will fail validation)
        return model_name
