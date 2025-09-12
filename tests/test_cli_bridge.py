"""Tests for CLI Bridge Provider."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from providers.cli_bridge import CLIBridgeProvider


class TestCLIBridgeProvider:
    """Test cases for CLI Bridge Provider."""

    def test_init_builds_supported_models(self):
        """Test that init builds SUPPORTED_MODELS correctly."""
        provider = CLIBridgeProvider()
        assert "codex" in provider.SUPPORTED_MODELS

        capabilities = provider.SUPPORTED_MODELS["codex"]
        assert capabilities.provider.name == "CLI"
        assert capabilities.friendly_name == "Codex (GPT-5)"
        assert capabilities.context_window == 400_000
        assert capabilities.max_output_tokens == 128_000
        assert capabilities.supports_system_prompts is True

    def test_get_capabilities_known_model(self):
        """Test getting capabilities for known model."""
        provider = CLIBridgeProvider()
        caps = provider.get_capabilities("codex")
        assert caps.model_name == "codex"

    def test_get_capabilities_unknown_model(self):
        """Test getting capabilities for unknown model raises error."""
        provider = CLIBridgeProvider()
        with pytest.raises(ValueError, match="Model unknown not supported"):
            provider.get_capabilities("unknown")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_generate_content_success(self, mock_run, mock_which):
        """Test successful content generation."""
        mock_which.return_value = "/usr/bin/codex"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Generated response",
            stderr="",
        )

        provider = CLIBridgeProvider()
        response = provider.generate_content("test prompt", "codex")

        assert response.content == "Generated response"
        assert response.model_name == "codex"
        assert response.provider.name == "CLI"
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert kwargs["input"] == "test prompt"
        assert kwargs["timeout"] == 30

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_generate_content_with_system_prompt(self, mock_run, mock_which):
        """Test content generation with system prompt concatenation."""
        mock_which.return_value = "/usr/bin/codex"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Response",
            stderr="",
        )

        provider = CLIBridgeProvider()
        provider.generate_content("user prompt", "codex", system_prompt="system prompt")

        expected_input = "system prompt\n\nuser prompt"
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert kwargs["input"] == expected_input

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_generate_content_binary_not_found(self, mock_run, mock_which):
        """Test error when binary is not found."""
        mock_which.return_value = None

        provider = CLIBridgeProvider()
        with pytest.raises(RuntimeError, match="CLI binary 'codex' not found"):
            provider.generate_content("test", "codex")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_generate_content_timeout(self, mock_run, mock_which):
        """Test timeout handling."""
        mock_which.return_value = "/usr/bin/codex"
        mock_run.side_effect = subprocess.TimeoutExpired("codex", 30)

        provider = CLIBridgeProvider()
        response = provider.generate_content("test", "codex")

        assert response.content == ""
        assert response.metadata["error"] == "timeout"
        assert response.metadata["timeout_seconds"] == 30

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_generate_content_command_failure(self, mock_run, mock_which):
        """Test handling of non-zero exit code."""
        mock_which.return_value = "/usr/bin/codex"
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error message",
        )

        provider = CLIBridgeProvider()
        response = provider.generate_content("test", "codex")

        assert response.content == ""
        assert response.metadata["error"] == "command_failed"
        assert response.metadata["stderr"] == "Error message"
        assert response.metadata["exit_code"] == 1

    def test_count_tokens_stub(self):
        """Test token counting returns 0 (stub implementation)."""
        provider = CLIBridgeProvider()
        assert provider.count_tokens("test text", "codex") == 0

    def test_get_provider_type(self):
        """Test provider type."""
        provider = CLIBridgeProvider()
        assert provider.get_provider_type().name == "CLI"

    def test_validate_model_name(self):
        """Test model name validation."""
        provider = CLIBridgeProvider()
        assert provider.validate_model_name("codex") is True
        assert provider.validate_model_name("unknown") is False

    def test_supports_thinking_mode(self):
        """Test thinking mode support."""
        provider = CLIBridgeProvider()
        assert provider.supports_thinking_mode("codex") is False

    @patch("os.getenv")
    def test_custom_timeout(self, mock_getenv):
        """Test custom timeout from environment."""
        mock_getenv.return_value = "60"
        provider = CLIBridgeProvider()
        assert provider.timeout == 60

    @patch("os.getenv")
    def test_custom_binary(self, mock_getenv):
        """Test custom binary from environment."""

        def getenv_side_effect(key, default=None):
            if key == "CODEX_CLI_BINARY":
                return "custom-codex"
            return default

        mock_getenv.side_effect = getenv_side_effect

        with patch("shutil.which") as mock_which, patch("subprocess.run") as mock_run:
            mock_which.return_value = "/usr/bin/custom-codex"
            mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

            provider = CLIBridgeProvider()
            provider.generate_content("test", "codex")

            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            cmd = args[0]
            assert cmd[0] == "custom-codex"
