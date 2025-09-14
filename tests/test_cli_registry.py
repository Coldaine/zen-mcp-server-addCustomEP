from providers.base import ProviderType
from providers.cli_bridge import CLIBridgeProvider
from providers.registry import ModelProviderRegistry


def setup_function(function):
    # Ensure registry is reset for each test
    ModelProviderRegistry.reset_for_testing()


def test_cli_provider_registration_and_listing():
    # Register CLI provider and ensure its models are listed
    ModelProviderRegistry.register_provider(ProviderType.CLI, CLIBridgeProvider)

    available = ModelProviderRegistry.get_available_model_names()
    assert isinstance(available, list)
    # CLIBridgeProvider exposes single 'codex-cli' logical model
    assert any(name.lower() == "codex-cli" for name in available)


def test_get_provider_for_cli_model():
    ModelProviderRegistry.register_provider(ProviderType.CLI, CLIBridgeProvider)

    provider = ModelProviderRegistry.get_provider_for_model("codex-cli")
    assert provider is not None
    assert provider.get_provider_type() == ProviderType.CLI


def test_registry_returns_none_for_unknown_model():
    ModelProviderRegistry.register_provider(ProviderType.CLI, CLIBridgeProvider)
    provider = ModelProviderRegistry.get_provider_for_model("this-model-does-not-exist")
    assert provider is None
