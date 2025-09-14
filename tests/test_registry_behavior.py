import pytest

from providers.base import ModelCapabilities, ModelProvider, ModelResponse, ProviderType
from providers.registry import (
    ModelProviderRegistry,
    get_primary_provider_class,
    register_additional_provider,
)


class _BaseStub(ModelProvider):
    def get_capabilities(self, model_name: str) -> ModelCapabilities:  # pragma: no cover - simple stub
        return ModelCapabilities(model_name=model_name, friendly_name=model_name, context_window=1, supports_images=False, max_output_tokens=1)

    def generate_content(self, prompt: str, model_name: str, system_prompt: str | None = None, temperature: float = 0.3, max_output_tokens: int | None = None, **kwargs) -> ModelResponse:  # pragma: no cover - simple stub
        return ModelResponse(content="", model_name=model_name, friendly_name=model_name, provider=ProviderType.CLI, usage={})

    def count_tokens(self, text: str, model_name: str) -> int:  # pragma: no cover - simple stub
        return len(text)

    def get_provider_type(self) -> ProviderType:  # pragma: no cover - simple stub
        return ProviderType.CLI

    def list_models(self, respect_restrictions: bool = True) -> list[str]:  # pragma: no cover - simple stub
        return ["stub"]

    def validate_model_name(self, model_name: str) -> bool:  # pragma: no cover - simple stub
        return True

    def supports_thinking_mode(self, model_name: str) -> bool:  # pragma: no cover - simple stub
        return False


class StubProviderA(_BaseStub):
    pass


class StubProviderB(_BaseStub):
    pass


@pytest.fixture(autouse=True)
def reset_registry():
    ModelProviderRegistry.reset_for_testing()
    yield
    ModelProviderRegistry.reset_for_testing()


def test_register_provider_overwrites_by_default():
    """Verify that the default behavior is to overwrite, preserving the old contract."""
    ModelProviderRegistry.register_provider(ProviderType.CLI, StubProviderA)
    assert get_primary_provider_class(ProviderType.CLI) is StubProviderA
    # This second call should OVERWRITE the first one
    ModelProviderRegistry.register_provider(ProviderType.CLI, StubProviderB)
    providers = ModelProviderRegistry.get_providers(ProviderType.CLI)
    assert len(providers) == 1
    assert isinstance(providers[0], StubProviderB)
    assert get_primary_provider_class(ProviderType.CLI) is StubProviderB


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
