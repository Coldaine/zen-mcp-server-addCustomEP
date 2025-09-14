"""Live (non-mocked) tests for the Gemini CLI Bridge Provider.

These tests exercise the Gemini CLI end-to-end via GeminiCLIBridgeProvider and
use the local qwen3:0.6b model (via CustomProvider) as a meta-validator to judge
whether the CLI's response plausibly satisfies the instruction, instead of
comparing to any hard-coded expected output.
"""

import os
import shutil

import pytest

from providers.gemini_cli_bridge import GeminiCLIBridgeProvider


def _gemini_available() -> bool:
    binary = os.getenv("GEMINI_CLI_BINARY", "gemini")
    return shutil.which(binary) is not None


def test_gemini_cli_bridge_live_responds_valid_by_qwen(monkeypatch):
    """Ensure Gemini CLI returns a response that qwen3:0.6b validates as satisfying the instruction."""
    # Slightly longer timeout for live CLI
    monkeypatch.setenv("GEMINI_CLI_TIMEOUT", "60")

    if not _gemini_available():
        pytest.fail("Gemini CLI binary not found on PATH. Install 'gemini' or set GEMINI_CLI_BINARY.")

    provider = GeminiCLIBridgeProvider()

    system_prompt = "You are a helpful coding assistant."
    user_prompt = "In one concise sentence, explain what a Python function is."

    response = provider.generate_content(
        prompt=user_prompt,
        model_name="gemini-cli",
        system_prompt=system_prompt,
    )

    if response.metadata.get("error"):
        pytest.fail(f"Gemini CLI returned error: {response.metadata}")

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


def test_gemini_cli_bridge_live_response_meta_validated_by_qwen(monkeypatch):
    """Meta-validate Gemini CLI response with local qwen3:0.6b when available.

    Skips if CUSTOM_API_URL is not configured; skips on CLI error metadata.
    """
    custom_api = os.getenv("CUSTOM_API_URL")
    if not custom_api:
        pytest.fail("CUSTOM_API_URL not set. Configure your local endpoint (e.g., http://localhost:11434/v1).")

    monkeypatch.setenv("GEMINI_CLI_TIMEOUT", "60")

    if not _gemini_available():
        pytest.fail("Gemini CLI binary not found on PATH. Install 'gemini' or set GEMINI_CLI_BINARY.")
    provider = GeminiCLIBridgeProvider()

    system_prompt = "You are a helpful coding assistant."
    user_prompt = "In one concise sentence, explain what a Python function is."

    response = provider.generate_content(
        prompt=user_prompt,
        model_name="gemini-cli",
        system_prompt=system_prompt,
    )

    if response.metadata.get("error"):
        pytest.fail(f"Gemini CLI returned error: {response.metadata}")

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

    raw = (verdict.content or "").strip().upper()
    text = raw.replace("<THINK>", "").replace("</THINK>", "").strip()
    first = text.split()[0] if text else ""
    if first in {"OK", "OKAY"}:
        first = "YES"
    if first not in {"YES", "NO"}:
        pytest.fail(f"Meta-validator did not produce a binary verdict: '{raw[:120]}'")
    assert first == "YES"
