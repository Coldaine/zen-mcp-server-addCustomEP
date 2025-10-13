"""Provider for Z.AI (Zhipu AI) models."""

from .openai_compatible import OpenAICompatibleProvider
from .shared.provider_type import ProviderType


class ZAIProvider(OpenAICompatibleProvider):
    """Provider for Z.AI models."""

    FRIENDLY_NAME = "Z.AI"
    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    def __init__(self, api_key: str, **kwargs):
        """Initialize the Z.AI provider."""
        super().__init__(
            api_key=api_key,
            **kwargs,
        )

    def get_provider_type(self) -> ProviderType:
        """Get the provider type."""
        return ProviderType.ZAI
