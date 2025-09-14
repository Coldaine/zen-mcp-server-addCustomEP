"""Integration-style test for CLI provider registration and routing.

This test ensures that when CODEX_CLI_ENABLED=1 and the binary exists, the
CLI provider (CLIBridgeProvider) is registered and resolves the 'codex-cli' model.
"""

import os
from unittest.mock import patch

from providers.base import ProviderType
from providers.registry import ModelProviderRegistry


@patch.dict(os.environ, {"CODEX_CLI_ENABLED": "1", "CODEX_CLI_BINARY": "codex"}, clear=True)
def test_cli_provider_registers_and_resolves_codex_cli():
    # Ensure a clean registry
    ModelProviderRegistry.reset_for_testing()

    # Pretend the codex binary exists
    with patch("shutil.which", return_value="/usr/bin/codex"):
        # Import and run provider configuration
        import server

        # Configure providers (should register CLI)
        server.configure_providers()

    # Verify provider resolves for 'codex-cli'
    provider = ModelProviderRegistry.get_provider_for_model("codex-cli")
    assert provider is not None
    assert provider.get_provider_type() == ProviderType.CLI

    # Verify 'codex-cli' appears in available model names for CLI
    models = ModelProviderRegistry.get_available_model_names(ProviderType.CLI)
    assert "codex-cli" in models
