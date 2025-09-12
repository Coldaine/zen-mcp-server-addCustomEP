import os
from unittest.mock import patch

from providers.base import ProviderType
from providers.registry import ModelProviderRegistry
from server import configure_providers


def setup_function(function):
    # Ensure registry is reset for each test
    ModelProviderRegistry.reset_for_testing()


def test_cli_provider_integration_routing():
    """Integration test for CLI provider registration and routing.

    Tests that when CODEX_CLI_ENABLED=1 and codex binary is available,
    the CLI provider is registered and can resolve "codex" model requests.
    """
    # Patch environment: enable CLI, clear other provider keys
    env_patches = {
        "CODEX_CLI_ENABLED": "1",
        "CODEX_CLI_BINARY": "codex",
        "GEMINI_API_KEY": "",
        "OPENAI_API_KEY": "",
        "XAI_API_KEY": "",
        "OPENROUTER_API_KEY": "",
        "DIAL_API_KEY": "",
        "CUSTOM_API_URL": "",
    }

    with patch.dict(os.environ, env_patches, clear=False):
        # Patch shutil.which to simulate codex binary being available
        with patch("shutil.which", return_value="/usr/local/bin/codex"):
            # Call configure_providers to register CLI provider
            configure_providers()

            # Assert: CLI provider can resolve "codex" model
            provider = ModelProviderRegistry.get_provider_for_model("codex")
            assert provider is not None
            assert provider.get_provider_type() == ProviderType.CLI

            # Assert: "codex" appears in CLI provider's available models
            cli_models = ModelProviderRegistry.get_available_model_names(ProviderType.CLI)
            assert "codex" in cli_models
