"""Gemini CLI Bridge Provider.

Minimal wrapper around the local `gemini` CLI binary.

Design goals (aligned with codex CLI simplification):
 - Single logical model name exposed: `gemini-cli`.
 - No enable flag; if the binary is discoverable we register it.
 - Minimal command invocation: `gemini --yolo -p <prompt>`.
 - Optional model override via `GEMINI_CLI_MODEL` -> adds `--model <value>` BEFORE `-p`.
 - System prompt (if provided) is prepended to user prompt separated by blank line.
 - Timeout controlled by `GEMINI_CLI_TIMEOUT` (default 30s).
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time

from providers.base import ModelCapabilities, ModelProvider, ModelResponse, ProviderType

logger = logging.getLogger(__name__)


class GeminiCLIBridgeProvider(ModelProvider):
    """Provider wrapping the local Gemini CLI binary."""

    CLI_MODEL_NAME = "gemini-cli"
    DEFAULT_BINARY = "gemini"

    def __init__(self, api_key: str = "", **kwargs):  # noqa: D401 - matches parent signature
        super().__init__(api_key, **kwargs)
        self.timeout = int(os.getenv("GEMINI_CLI_TIMEOUT", "30"))
        self.capabilities = ModelCapabilities(
            provider=ProviderType.CLI,
            model_name=self.CLI_MODEL_NAME,
            friendly_name="Gemini CLI",
            context_window=400_000,
            max_output_tokens=128_000,
            supports_extended_thinking=False,
            supports_system_prompts=True,
            supports_streaming=False,
            supports_function_calling=False,
            supports_images=False,
            max_image_size_mb=0.0,
            supports_temperature=False,
            description="Local Gemini CLI wrapper",
            aliases=[],
            supports_json_mode=False,
            max_thinking_tokens=0,
            is_custom=False,
        )

    def get_provider_type(self) -> ProviderType:  # noqa: D401
        return ProviderType.CLI

    def list_models(self, respect_restrictions: bool = True) -> list[str]:  # noqa: ARG002 parity
        return [self.CLI_MODEL_NAME]

    def validate_model_name(self, model_name: str) -> bool:
        return model_name == self.CLI_MODEL_NAME

    def get_capabilities(self, model_name: str) -> ModelCapabilities:
        if model_name != self.CLI_MODEL_NAME:
            raise ValueError(f"Model {model_name} not supported by Gemini CLI provider")
        return self.capabilities

    def supports_thinking_mode(self, model_name: str) -> bool:  # noqa: D401
        return False

    def count_tokens(self, text: str, model_name: str) -> int:  # noqa: D401
        if model_name != self.CLI_MODEL_NAME:
            raise ValueError("Unsupported model for token counting")
        logger.debug("Token counting not implemented for Gemini CLI model; returning -1 sentinel")
        return -1

    def generate_content(
        self,
        prompt: str,
        model_name: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,  # noqa: ARG002 maintained for interface compatibility
        max_output_tokens: int | None = None,  # noqa: ARG002
        **kwargs,
    ) -> ModelResponse:
        if model_name != self.CLI_MODEL_NAME:
            raise ValueError(f"Unknown model: {model_name}")

        binary = os.getenv("GEMINI_CLI_BINARY", self.DEFAULT_BINARY)
        if not shutil.which(binary):
            raise RuntimeError(f"Gemini CLI binary '{binary}' not found in PATH")

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        cmd = [binary, "--yolo"]
        model_override = os.getenv("GEMINI_CLI_MODEL")
        if model_override:
            cmd += ["--model", model_override]
        # -p <prompt>
        cmd += ["-p", full_prompt]

        logger.debug("Running Gemini CLI command: %s (timeout=%ss)", " ".join(cmd), self.timeout)
        start_time = time.time()
        try:
            # Prompt passed as argument; no stdin streaming needed.
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                input=None,
            )
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            logger.warning("Gemini CLI command timed out after %.1fs", elapsed)
            return ModelResponse(
                content="",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                model_name=model_name,
                friendly_name=self.capabilities.friendly_name,
                provider=ProviderType.CLI,
                metadata={"error": "timeout", "timeout_seconds": self.timeout},
            )

        elapsed = time.time() - start_time
        logger.debug("Gemini CLI completed in %.2fs (exit=%s)", elapsed, result.returncode)

        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            logger.error("Gemini CLI command failed: %s", stderr)
            return ModelResponse(
                content="",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                model_name=model_name,
                friendly_name=self.capabilities.friendly_name,
                provider=ProviderType.CLI,
                metadata={"error": "command_failed", "stderr": stderr, "exit_code": result.returncode},
            )

        content = (result.stdout or "").strip()
        return ModelResponse(
            content=content,
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            model_name=model_name,
            friendly_name=self.capabilities.friendly_name,
            provider=ProviderType.CLI,
            metadata={"execution_time": elapsed},
        )
