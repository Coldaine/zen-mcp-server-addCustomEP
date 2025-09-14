"""Live (non-mocked) tests for the Codex CLI Bridge Provider.

These tests exercise the Codex CLI end-to-end via CLIBridgeProvider and use the
local qwen3:0.6b model (via CustomProvider) as a meta-validator to judge whether
the CLI's response plausibly satisfies the instruction, instead of comparing to
any hard-coded expected output.
"""

import pytest
pytest.skip("Requires codex CLI binary and a live local model endpoint", allow_module_level=True)

import os
import shutil

import pytest

from providers.cli_bridge import CLIBridgeProvider


def _codex_available() -> bool:
    binary = os.getenv("CODEX_CLI_BINARY", "codex")
    return shutil.which(binary) is not None


def test_cli_bridge_live_codex_responds_valid_by_qwen(monkeypatch):
    """Ensure Codex CLI returns a response that qwen3:0.6b validates as satisfying the instruction."""
    # Allow a bit more time for live CLI responses
    monkeypatch.setenv("CODEX_CLI_TIMEOUT", "60")

    if not _codex_available():
        pytest.fail("Codex CLI binary not found on PATH. Install 'codex' or set CODEX_CLI_BINARY.")

    provider = CLIBridgeProvider()

    system_prompt = "You are a helpful coding assistant."
    user_prompt = "In one concise sentence, explain what a Python function is."

    response = provider.generate_content(
        prompt=user_prompt,
        model_name="codex-cli",
        system_prompt=system_prompt,
    )

    if response.metadata.get("error"):
        pytest.fail(f"Codex CLI returned error: {response.metadata}")

    # Meta-validate using local qwen3:0.6b via CustomProvider
    from providers.custom import CustomProvider

    custom_api = os.getenv("CUSTOM_API_URL")
    if not custom_api:
        pytest.fail("CUSTOM_API_URL not set. Configure your local endpoint (e.g., http://localhost:11434/v1).")

    meta_system = (
        "You are a strict validator. Given the instruction and the CLI output, "
        "decide if the output plausibly satisfies the instruction. Respond with a single word: YES or NO."
    )
    meta_prompt = (
        f"Instruction (system + user combined):\n{system_prompt}\n\n{user_prompt}\n\n"
        f"CLI Output:\n{response.content}\n\n"
        "Judge YES if it is a plausible, short definition of a Python function, even if not perfectly one sentence. "
        "Answer only YES or NO."
    )

    qwen = CustomProvider(base_url=custom_api)
    verdict = qwen.generate_content(
        prompt=meta_prompt,
        model_name="qwen3:0.6b",
        system_prompt=meta_system,
        temperature=0.0,
        max_output_tokens=3,
    )

    raw = (verdict.content or "").strip().upper()
    text = raw.replace("<THINK>", "").replace("</THINK>", "").strip()
    first = text.split()[0] if text else ""
    if first in {"OK", "OKAY"}:
        first = "YES"
    if first not in {"YES", "NO"}:
        pytest.fail(f"Meta-validator did not produce a binary verdict: '{raw[:120]}'")
    assert first == "YES"


def test_cli_bridge_live_codex_response_meta_validated_by_qwen(monkeypatch):
    """Second meta-validation run to ensure stability across invocations."""
    # Require local custom API for Qwen
    custom_api = os.getenv("CUSTOM_API_URL")
    if not custom_api:
        pytest.fail("CUSTOM_API_URL not set. Configure your local endpoint (e.g., http://localhost:11434/v1).")

    # Allow a bit more time for live CLI responses
    monkeypatch.setenv("CODEX_CLI_TIMEOUT", "60")

    if not _codex_available():
        pytest.fail("Codex CLI binary not found on PATH. Install 'codex' or set CODEX_CLI_BINARY.")
    provider = CLIBridgeProvider()

    system_prompt = "You are a helpful coding assistant."
    user_prompt = "In one concise sentence, explain what a Python function is."

    response = provider.generate_content(
        prompt=user_prompt,
        model_name="codex-cli",
        system_prompt=system_prompt,
    )

    if response.metadata.get("error"):
        pytest.fail(f"Codex CLI returned error: {response.metadata}")

    # Meta-validate using local qwen3:0.6b via CustomProvider
    from providers.custom import CustomProvider

    meta_system = (
        "You are a strict validator. Given the original instruction and the CLI output, "
        "decide if the output appears to satisfy the instruction. Respond with a single word: YES or NO."
    )
    meta_prompt = (
        f"Instruction (system + user combined):\n{system_prompt}\n\n{user_prompt}\n\n"
        f"CLI Output:\n{response.content}\n\n"
        "Answer only YES or NO."
    )

    qwen = CustomProvider(base_url=custom_api)
    verdict = qwen.generate_content(
        prompt=meta_prompt,
        model_name="qwen3:0.6b",
        system_prompt=meta_system,
        temperature=0.0,
        max_output_tokens=3,
    )

    # Accept minor formatting by checking the presence of YES
    raw = (verdict.content or "").strip().upper()
    # Normalize common wrappers/tags and take the first token-ish
    text = raw.replace("<THINK>", "").replace("</THINK>", "").strip()
    first = text.split()[0] if text else ""
    # Map lenient affirmatives to YES
    if first in {"OK", "OKAY"}:
        first = "YES"
    if first not in {"YES", "NO"}:
        pytest.fail(f"Meta-validator did not produce a binary verdict: '{raw[:120]}'")
    assert first == "YES"
