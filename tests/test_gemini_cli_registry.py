import os
from unittest.mock import MagicMock, patch

from providers.gemini_cli_bridge import GeminiCLIBridgeProvider
from providers.registry import ModelProviderRegistry


def setup_function(function):
    ModelProviderRegistry.reset_for_testing()


@patch.dict(os.environ, {}, clear=True)
def test_gemini_cli_not_registered_when_binary_missing():
    ModelProviderRegistry.reset_for_testing()
    with patch("shutil.which", return_value=None):
        import server

        server.configure_providers()
    assert ModelProviderRegistry.get_provider_for_model("gemini-cli") is None


@patch.dict(os.environ, {"GEMINI_CLI_BINARY": "gemini"}, clear=True)
def test_gemini_cli_direct_instantiation_command_building():
    # Direct provider test (bypasses registry) to validate command construction
    provider = GeminiCLIBridgeProvider()
    with patch("shutil.which", return_value="/usr/bin/gemini"):
        # Mock subprocess.run to capture args
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "OK"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result) as run_mock:
            resp = provider.generate_content("Hello", model_name="gemini-cli")
        assert resp.content == "OK"
        called_cmd = run_mock.call_args[0][0]
        assert called_cmd[:2] == ["gemini", "--yolo"]
        assert "-p" in called_cmd
        # Model flag not present when GEMINI_CLI_MODEL unset
        assert "--model" not in called_cmd


@patch.dict(os.environ, {"GEMINI_CLI_BINARY": "gemini", "GEMINI_CLI_MODEL": "gemini-2.5-flash"}, clear=True)
def test_gemini_cli_model_override():
    provider = GeminiCLIBridgeProvider()
    with patch("shutil.which", return_value="/usr/bin/gemini"):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "OK"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result) as run_mock:
            provider.generate_content("Ping", model_name="gemini-cli")
        called_cmd = run_mock.call_args[0][0]
        # Ensure model override appears before -p
        model_index = called_cmd.index("--model")
        p_index = called_cmd.index("-p")
        assert model_index < p_index
        assert called_cmd[model_index + 1] == "gemini-2.5-flash"
