"""Live (non-mocked) test for the CLI Bridge Provider.

This test exercises the Codex CLI end-to-end via CLIBridgeProvider.

It is intentionally simple and non-deterministic-friendly. It only asserts that
some content is returned and that the word 'OK' appears in the output for a very
constrained prompt.

The test is automatically skipped when the Codex binary is not found on PATH.
"""

import os
import shutil

import pytest

from providers.cli_bridge import CLIBridgeProvider


def _codex_available() -> bool:
    binary = os.getenv("CODEX_CLI_BINARY", "codex")
    return shutil.which(binary) is not None


@pytest.mark.skipif(not _codex_available(), reason="Codex CLI binary not found on PATH")
def test_cli_bridge_live_codex_responds_ok(monkeypatch):
    """Ensure the live Codex CLI returns content for a simple prompt.

    The prompt asks Codex to return exactly 'OK'. We only assert that 'OK' appears
    to avoid brittleness if Codex adds minor formatting.
    """
    # Allow a bit more time for live CLI responses
    monkeypatch.setenv("CODEX_CLI_TIMEOUT", "60")

    provider = CLIBridgeProvider()

    system_prompt = "You are a function that must output exactly OK and nothing else."
    user_prompt = "Return exactly OK"

    response = provider.generate_content(
        prompt=user_prompt,
        model_name="codex",
        system_prompt=system_prompt,
    )

    # Basic sanity: content returned and no error metadata
    assert isinstance(response.content, str)
    assert response.content.strip() != ""
    assert response.metadata.get("error") is None

    # Relaxed correctness check to avoid flakiness
    assert "OK" in response.content.upper()
