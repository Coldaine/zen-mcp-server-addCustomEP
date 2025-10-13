"""Tests for Z.AI provider."""

import os
from unittest.mock import patch

import pytest

from providers.base import ProviderType
from providers.zai import ZAIProvider


class TestZAIProvider:
    """Test Z.AI provider functionality."""

    def setup_method(self):
        """Set up clean state before each test."""
        # Tests don't need registry cleanup since we test the provider directly
        pass

    def teardown_method(self):
        """Clean up after each test."""
        pass

    @patch.dict(os.environ, {"ZAI_API_KEY": "test-key"})
    def test_initialization(self):
        """Test provider initialization."""
        provider = ZAIProvider("test-key")
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.z.ai/api/paas/v4"

    def test_initialization_with_custom_url(self):
        """Test provider initialization with custom base URL."""
        provider = ZAIProvider("test-key", base_url="https://custom.z.ai/v4")
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://custom.z.ai/v4"

    def test_model_validation(self):
        """Test model name validation."""
        provider = ZAIProvider("test-key")

        # Valid models
        assert provider.validate_model_name("glm-4.6") is True
        assert provider.validate_model_name("glm4.6") is True
        assert provider.validate_model_name("flash") is True

        # Invalid models
        assert provider.validate_model_name("invalid-model") is False
        assert provider.validate_model_name("gpt-4") is False

    def test_resolve_model_name(self):
        """Test model name resolution."""
        provider = ZAIProvider("test-key")

        # Canonical name
        assert provider._resolve_model_name("glm-4.6") == "glm-4.6"

        # Aliases
        assert provider._resolve_model_name("glm4.6") == "glm-4.6"
        assert provider._resolve_model_name("glm46") == "glm-4.6"
        assert provider._resolve_model_name("flash") == "glm-4.6"

        # Unknown (returns as-is)
        assert provider._resolve_model_name("unknown") == "unknown"

    def test_get_capabilities_glm46(self):
        """Test getting model capabilities for GLM-4.6."""
        provider = ZAIProvider("test-key")
        capabilities = provider.get_capabilities("glm-4.6")

        assert capabilities.model_name == "glm-4.6"
        assert capabilities.provider == ProviderType.ZAI
        assert capabilities.context_window == 200_000
        assert capabilities.max_output_tokens == 128_000
        assert capabilities.supports_streaming is True
        assert capabilities.supports_function_calling is True
        assert capabilities.supports_json_mode is True
        assert capabilities.supports_system_prompts is True
        assert capabilities.supports_temperature is True
        assert capabilities.supports_images is False
        assert capabilities.supports_extended_thinking is False

    def test_get_capabilities_with_alias(self):
        """Test getting model capabilities with alias resolves correctly."""
        provider = ZAIProvider("test-key")

        # Use alias "flash"
        capabilities = provider.get_capabilities("flash")
        assert capabilities.model_name == "glm-4.6"
        assert capabilities.provider == ProviderType.ZAI

    def test_get_capabilities_unsupported_model(self):
        """Test getting capabilities for unsupported model raises error."""
        provider = ZAIProvider("test-key")

        with pytest.raises(ValueError, match="Unsupported Z.AI model"):
            provider.get_capabilities("invalid-model")

    def test_get_provider_type(self):
        """Test get_provider_type returns ZAI."""
        provider = ZAIProvider("test-key")
        assert provider.get_provider_type() == ProviderType.ZAI

    def test_supported_models_structure(self):
        """Test SUPPORTED_MODELS has correct structure."""
        provider = ZAIProvider("test-key")

        # Should have at least glm-4.6
        assert "glm-4.6" in provider.SUPPORTED_MODELS

        # Check glm-4.6 has all required aliases
        glm_capabilities = provider.SUPPORTED_MODELS["glm-4.6"]
        assert "flash" in glm_capabilities.aliases
        assert "glm4.6" in glm_capabilities.aliases
        assert "glm46" in glm_capabilities.aliases
        assert "glm-4.6" in glm_capabilities.aliases

    def test_temperature_constraint(self):
        """Test temperature constraint for ZAI models."""
        provider = ZAIProvider("test-key")
        capabilities = provider.get_capabilities("glm-4.6")

        # Z.AI supports temperature range 0.0-2.0
        assert capabilities.temperature_constraint.validate(0.0)
        assert capabilities.temperature_constraint.validate(1.0)
        assert capabilities.temperature_constraint.validate(2.0)
        assert not capabilities.temperature_constraint.validate(-0.1)
        assert not capabilities.temperature_constraint.validate(2.1)


@pytest.mark.skipif(
    not os.getenv("ZAI_API_KEY"),
    reason="ZAI_API_KEY not set - skipping integration tests",
)
class TestZAIProviderIntegration:
    """Integration tests for Z.AI provider (requires API key)."""

    def test_provider_initialization_with_env(self):
        """Test provider can initialize with environment variables."""
        api_key = os.getenv("ZAI_API_KEY")
        provider = ZAIProvider(api_key)

        assert provider.api_key == api_key
        assert provider.base_url == "https://api.z.ai/api/paas/v4"

    def test_model_validation_with_env(self):
        """Test model validation works with real provider."""
        api_key = os.getenv("ZAI_API_KEY")
        provider = ZAIProvider(api_key)

        assert provider.validate_model_name("glm-4.6") is True
        assert provider.validate_model_name("flash") is True
