from typing import Optional

import pytest

from providers.base import ModelCapabilities, ModelProvider, ProviderType
from providers.registry import (
    ModelProviderRegistry,
    get_primary_provider_class,
    register_additional_provider,
)
from tools.models import ToolOutput


class StubProviderA(ModelProvider):
    def __init__(self, **kwargs):
        pass  # Dummy init

    def get_capabilities(self, model_name: str) -> Optional[ModelCapabilities]:
        return None

    def generate_content(
        self, prompt: str, model_name: str, previous_messages: list = None, system_prompt: Optional[str] = None, **kwargs
    ) -> ToolOutput:
        return ToolOutput(status="success", content="")

    def count_tokens(self, text: str, model_name: str) -> int:
        return 0

    def get_provider_type(self) -> ProviderType:
        return ProviderType.CUSTOM

    def validate_model_name(self, model_name: str) -> bool:
        return True

    def supports_thinking_mode(self, model_name: str) -> bool:
        return False


class StubProviderB(ModelProvider):
    def __init__(self, **kwargs):
        pass  # Dummy init

    def get_capabilities(self, model_name: str) -> Optional[ModelCapabilities]:
        return None

    def generate_content(
        self, prompt: str, model_name: str, previous_messages: list = None, system_prompt: Optional[str] = None, **kwargs
    ) -> ToolOutput:
        return ToolOutput(status="success", content="")

    def count_tokens(self, text: str, model_name: str) -> int:
        return 0

    def get_provider_type(self) -> ProviderType:
        return ProviderType.CUSTOM

    def validate_model_name(self, model_name: str) -> bool:
        return True

    def supports_thinking_mode(self, model_name: str) -> bool:
        return False


@pytest.fixture(autouse=True)
def reset_registry():
    ModelProviderRegistry.reset_for_testing()
    yield
    ModelProviderRegistry.reset_for_testing()


def test_register_provider_overwrites_by_default(monkeypatch):
    """Verify that the default behavior is to overwrite, preserving the old contract."""
    monkeypatch.setenv("CUSTOM_API_URL", "http://localhost:1234")
    ModelProviderRegistry.register_provider(ProviderType.CUSTOM, StubProviderA)
    assert get_primary_provider_class(ProviderType.CUSTOM) is StubProviderA

    # This second call should OVERWRITE the first one
    ModelProviderRegistry.register_provider(ProviderType.CUSTOM, StubProviderB)
    providers = ModelProviderRegistry.get_providers(ProviderType.CUSTOM)
    assert len(providers) == 1
    assert isinstance(providers[0], StubProviderB)
    assert get_primary_provider_class(ProviderType.CUSTOM) is StubProviderB


def test_register_provider_appends_when_flag_is_true():
    """Verify that append=True correctly adds a second provider."""
    ModelProviderRegistry.register_provider(ProviderType.CLI, StubProviderA)
    ModelProviderRegistry.register_provider(ProviderType.CLI, StubProviderB, append=True)

    providers = ModelProviderRegistry.get_providers(ProviderType.CLI)
    assert len(providers) == 2
    assert isinstance(providers[0], StubProviderA)
    assert isinstance(providers[1], StubProviderB)


def test_register_additional_provider_helper_works():
    """Verify the semantic helper for appending."""
    ModelProviderRegistry.register_provider(ProviderType.CLI, StubProviderA)
    register_additional_provider(ProviderType.CLI, StubProviderB)

    providers = ModelProviderRegistry.get_providers(ProviderType.CLI)
    assert len(providers) == 2
    assert isinstance(providers[0], StubProviderA)
    assert isinstance(providers[1], StubProviderB)
