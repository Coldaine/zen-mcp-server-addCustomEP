"""CLI Bridge Provider for local CLI tools like Codex."""

import logging
import os
import shutil
import subprocess
import time
from typing import Optional

from providers.base import ModelCapabilities, ModelProvider, ModelResponse, ProviderType

logger = logging.getLogger(__name__)


class CLIBridgeProvider(ModelProvider):
    """Provider for a single local CLI tool (codex). Speculative multi-model support removed."""

    CLI_MODEL_NAME = "codex-cli"  # single logical model name exposed to the server
    DEFAULT_BINARY = "codex"  # actual binary expected on PATH (override via CODEX_CLI_BINARY)
    DEFAULT_ARGS = [
        "exec",
        "--color",
        "never",
        "--skip-git-repo-check",
    ]

    def __init__(self, api_key: str = "", **kwargs):
        """Initialize CLI bridge provider."""
        super().__init__(api_key, **kwargs)
        self.timeout = int(os.getenv("CODEX_CLI_TIMEOUT", "30"))  # Default 30 seconds

        # Single capabilities object (minimal, no speculative features)
        self.capabilities = ModelCapabilities(
            provider=ProviderType.CLI,
            model_name=self.CLI_MODEL_NAME,
            friendly_name="Codex CLI",
            context_window=400_000,  # generous upper bound; real limit enforced by underlying API/binary
            max_output_tokens=128_000,
            supports_extended_thinking=False,
            supports_system_prompts=True,
            supports_streaming=False,
            supports_function_calling=False,
            supports_images=False,
            max_image_size_mb=0.0,
            supports_temperature=False,
            description="Local codex CLI wrapper",
            aliases=[],
            supports_json_mode=False,
            max_thinking_tokens=0,
            is_custom=False,
        )

    def get_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get capabilities for a specific model."""
        if model_name != self.CLI_MODEL_NAME:
            raise ValueError(f"Model {model_name} not supported by CLI bridge")
        return self.capabilities

    def generate_content(
        self,
        prompt: str,
        model_name: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_output_tokens: Optional[int] = None,
        **kwargs,
    ) -> ModelResponse:
        """Generate content using CLI tool."""
        if model_name != self.CLI_MODEL_NAME:
            raise ValueError(f"Unknown model: {model_name}")

        binary = os.getenv("CODEX_CLI_BINARY", self.DEFAULT_BINARY)

        # Verify binary exists
        if not shutil.which(binary):
            raise RuntimeError(f"CLI binary '{binary}' not found in PATH")

        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Build command
        cmd = [binary] + self.DEFAULT_ARGS

        logger.debug(f"Running CLI command: {' '.join(cmd)} with timeout {self.timeout}s")

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                input=full_prompt,  # pass str when text=True
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            logger.warning(f"CLI command timed out after {elapsed:.1f}s")
            return ModelResponse(
                content="",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                model_name=model_name,
                friendly_name=self.capabilities.friendly_name,
                provider=ProviderType.CLI,
                metadata={"error": "timeout", "timeout_seconds": self.timeout},
            )

        elapsed = time.time() - start_time
        logger.debug(f"CLI command completed in {elapsed:.2f}s, exit code: {result.returncode}")

        if result.returncode != 0:
            error_msg = result.stderr.strip() or "Unknown error"
            logger.error(f"CLI command failed: {error_msg}")
            return ModelResponse(
                content="",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                model_name=model_name,
                friendly_name=self.capabilities.friendly_name,
                provider=ProviderType.CLI,
                metadata={"error": "command_failed", "stderr": error_msg, "exit_code": result.returncode},
            )

        # Success - return the stdout as content
        content = result.stdout.strip()
        return ModelResponse(
            content=content,
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},  # Stub for now
            model_name=model_name,
            friendly_name=self.capabilities.friendly_name,
            provider=ProviderType.CLI,
            metadata={"execution_time": elapsed},
        )

    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens - stub implementation."""
        # For MVP, return 0 and log that this is approximate
        if model_name != self.CLI_MODEL_NAME:
            raise ValueError("Unsupported model for token counting")
        logger.debug("Token counting not implemented for CLI CLI model; returning -1 sentinel")
        return -1

    def list_models(self, respect_restrictions: bool = True) -> list[str]:  # noqa: ARG002 parity
        """Return the single logical CLI model name.

        restrictions are applied at registry layer; nothing to filter here.
        """
        return [self.CLI_MODEL_NAME]

    def get_provider_type(self) -> ProviderType:
        """Get provider type."""
        return ProviderType.CLI

    def validate_model_name(self, model_name: str) -> bool:
        """Validate model name."""
        return model_name == self.CLI_MODEL_NAME

    def supports_thinking_mode(self, model_name: str) -> bool:
        """CLI models don't support thinking mode."""
        return False
