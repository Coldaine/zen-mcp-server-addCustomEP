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
    """Provider for local CLI tools that expose model inference via command line."""

    # Model specifications - extensible for multiple CLI tools
    CLI_MODEL_SPECS = {
        "codex": {
            "friendly_name": "Codex (GPT-5)",
            # Align with GPT-5 capabilities for consistency
            "context_window": 400_000,
            "max_output_tokens": 128_000,
            "binary": "codex",
            # Use non-interactive execution path; read prompt from stdin
            # --color=never avoids ANSI codes in output; --skip-git-repo-check for portability
            "args": ["exec", "--color", "never", "--skip-git-repo-check"],
        },
    }

    def __init__(self, api_key: str = "", **kwargs):
        """Initialize CLI bridge provider."""
        super().__init__(api_key, **kwargs)
        self.timeout = int(os.getenv("CODEX_CLI_TIMEOUT", "30"))  # Default 30 seconds

        # Build SUPPORTED_MODELS from specs
        self.SUPPORTED_MODELS = {}
        for model_name, spec in self.CLI_MODEL_SPECS.items():
            self.SUPPORTED_MODELS[model_name] = ModelCapabilities(
                provider=ProviderType.CLI,
                model_name=model_name,
                friendly_name=spec["friendly_name"],
                context_window=spec["context_window"],
                max_output_tokens=spec["max_output_tokens"],
                supports_extended_thinking=False,
                supports_system_prompts=True,  # We concatenate internally
                supports_streaming=False,
                supports_function_calling=False,
                supports_images=False,
                max_image_size_mb=0.0,
                supports_temperature=False,  # CLI may not support temperature
                description=f"Local CLI model via {spec['binary']}",
                aliases=[],  # Can add short aliases later if needed
                supports_json_mode=False,
                max_thinking_tokens=0,
                is_custom=False,
            )

    def get_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get capabilities for a specific model."""
        if model_name not in self.SUPPORTED_MODELS:
            raise ValueError(f"Model {model_name} not supported by CLI bridge")
        return self.SUPPORTED_MODELS[model_name]

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
        if model_name not in self.CLI_MODEL_SPECS:
            raise ValueError(f"Unknown model: {model_name}")

        spec = self.CLI_MODEL_SPECS[model_name]
        binary = os.getenv("CODEX_CLI_BINARY", spec["binary"])

        # Verify binary exists
        if not shutil.which(binary):
            raise RuntimeError(f"CLI binary '{binary}' not found in PATH")

        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Build command
        cmd = [binary] + spec["args"]

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
                friendly_name=spec["friendly_name"],
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
                friendly_name=spec["friendly_name"],
                provider=ProviderType.CLI,
                metadata={"error": "command_failed", "stderr": error_msg, "exit_code": result.returncode},
            )

        # Success - return the stdout as content
        content = result.stdout.strip()
        return ModelResponse(
            content=content,
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},  # Stub for now
            model_name=model_name,
            friendly_name=spec["friendly_name"],
            provider=ProviderType.CLI,
            metadata={"execution_time": elapsed},
        )

    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens - stub implementation."""
        # For MVP, return 0 and log that this is approximate
        logger.debug(f"Token counting not implemented for CLI model {model_name}, returning 0")
        return 0

    def get_provider_type(self) -> ProviderType:
        """Get provider type."""
        return ProviderType.CLI

    def validate_model_name(self, model_name: str) -> bool:
        """Validate model name."""
        return model_name in self.CLI_MODEL_SPECS

    def supports_thinking_mode(self, model_name: str) -> bool:
        """CLI models don't support thinking mode."""
        return False
