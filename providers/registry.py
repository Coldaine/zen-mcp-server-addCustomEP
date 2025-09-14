"""Model provider registry for managing available providers."""

import logging
import os
from typing import TYPE_CHECKING, Dict, List, Optional, Type

from .base import ModelProvider, ProviderType

if TYPE_CHECKING:
    from tools.models import ToolModelCategory


class ModelProviderRegistry:
    """Registry for managing model providers."""

    _instance = None

    # Provider priority order for model selection
    # Native APIs first, then local CLI tools, then custom endpoints, then catch-all providers
    PROVIDER_PRIORITY_ORDER = [
        ProviderType.GOOGLE,  # Direct Gemini access
        ProviderType.OPENAI,  # Direct OpenAI access
        ProviderType.XAI,  # Direct X.AI GROK access
        ProviderType.DIAL,  # DIAL unified API access
        ProviderType.CLI,  # Local CLI tools (Codex, etc.)
        ProviderType.CUSTOM,  # Local/self-hosted models
        ProviderType.OPENROUTER,  # Catch-all for cloud models
    ]

    def __new__(cls):
        """Singleton pattern for registry."""
        if cls._instance is None:
            logging.debug("REGISTRY: Creating new registry instance")
            cls._instance = super().__new__(cls)
            # Initialize instance dictionaries on first creation
            # Map ProviderType -> list of provider classes (or factories)
            cls._instance._providers: Dict[ProviderType, List[type[ModelProvider]]] = {}
            # Map ProviderType -> list of initialized provider instances (aligned by index)
            cls._instance._initialized_providers: Dict[ProviderType, List[Optional[ModelProvider]]] = {}
            logging.debug(f"REGISTRY: Created instance {cls._instance}")
        return cls._instance

    @classmethod
    def register_provider(
        cls,
        provider_type: ProviderType,
        provider_class: type[ModelProvider],
        *,
        append: bool = False,
    ) -> None:
        """Register a new provider class.

        Args:
            provider_type: Type of the provider (e.g., ProviderType.GOOGLE)
            provider_class: Class that implements ModelProvider interface
            append: If True, appends the provider to the list for this type.
                If False (default), overwrites any existing providers for the type.
                This preserves backward compatibility for single-provider types.
        """
        instance = cls()
        if provider_type not in instance._providers or not append:
            instance._providers[provider_type] = [provider_class]
            instance._initialized_providers[provider_type] = [None]
        else:
            instance._providers[provider_type].append(provider_class)
            instance._initialized_providers[provider_type].append(None)

    @classmethod
    def get_provider(cls, provider_type: ProviderType, force_new: bool = False) -> Optional[ModelProvider]:
        """Get an initialized provider instance.

        Args:
            provider_type: Type of provider to get
            force_new: Force creation of new instance instead of using cached

        Returns:
            Initialized ModelProvider instance or None if not available
        """
        # Compatibility: return the first provider instance (or initialize it) for this type
        providers = cls.get_providers(provider_type, force_new=force_new)
        if not providers:
            return None
        return providers[0]

    @classmethod
    def get_providers(cls, provider_type: ProviderType, force_new: bool = False) -> list[ModelProvider]:
        """Get all initialized providers for a given type.

        Initializes providers lazily and returns a list aligned with registered classes.
        """
        instance = cls()
        classes = instance._providers.get(provider_type)
        if not classes:
            return []

        init_list = instance._initialized_providers.setdefault(provider_type, [None] * len(classes))

        providers: list[ModelProvider] = []
        for idx, provider_class in enumerate(classes):
            if not force_new and idx < len(init_list) and init_list[idx] is not None:
                providers.append(init_list[idx])
                continue

            # Initialize provider instance according to type-specific needs
            api_key = cls._get_api_key_for_provider(provider_type)

            try:
                if provider_type == ProviderType.CUSTOM:
                    # Factory function or class requiring base_url
                    if callable(provider_class) and not isinstance(provider_class, type):
                        provider = provider_class(api_key=api_key)
                    else:
                        custom_url = os.getenv("CUSTOM_API_URL", "")
                        if not custom_url:
                            if api_key:
                                logging.warning(
                                    "CUSTOM_API_KEY set but CUSTOM_API_URL missing – skipping Custom provider"
                                )
                            # Skip this provider
                            providers.append(None)  # placeholder to keep alignment
                            continue
                        api_key = api_key or ""
                        provider = provider_class(api_key=api_key, base_url=custom_url)
                elif provider_type == ProviderType.CLI:
                    # CLI providers don't use API keys
                    provider = provider_class(api_key="")
                else:
                    if not api_key:
                        # Skip provider if required key missing
                        providers.append(None)
                        continue
                    provider = provider_class(api_key=api_key)
            except Exception as e:
                logging.debug(f"Failed to initialize provider {provider_class} for {provider_type}: {e}")
                providers.append(None)
                continue

            # Cache and collect
            if idx >= len(init_list):
                init_list.extend([None] * (idx - len(init_list) + 1))
            init_list[idx] = provider
            providers.append(provider)

        # Filter out Nones for consumers; keep internal alignment in cache
        return [p for p in providers if p is not None]

    @classmethod
    def get_provider_for_model(cls, model_name: str) -> Optional[ModelProvider]:
        """Get provider instance for a specific model name.

        Provider priority order:
        1. Native APIs (GOOGLE, OPENAI) - Most direct and efficient
        2. CUSTOM - For local/private models with specific endpoints
        3. OPENROUTER - Catch-all for cloud models via unified API

        Args:
            model_name: Name of the model (e.g., "gemini-2.5-flash", "gpt5")

        Returns:
            ModelProvider instance that supports this model
        """
        logging.debug(f"get_provider_for_model called with model_name='{model_name}'")

        # Check providers in priority order
        instance = cls()
        logging.debug(f"Registry instance: {instance}")
        logging.debug(f"Available providers in registry: {list(instance._providers.keys())}")

        for provider_type in cls.PROVIDER_PRIORITY_ORDER:
            if provider_type in instance._providers:
                logging.debug(f"Found {provider_type} in registry")
                # Iterate through all providers of this type
                for provider in cls.get_providers(provider_type):
                    if provider and provider.validate_model_name(model_name):
                        logging.debug(f"{provider_type} validates model {model_name}")
                        return provider
                logging.debug(f"{provider_type} does not validate model {model_name}")
            else:
                logging.debug(f"{provider_type} not found in registry")

        logging.debug(f"No provider found for model {model_name}")
        return None

    @classmethod
    def get_available_providers(cls) -> list[ProviderType]:
        """Get list of registered provider types."""
        instance = cls()
        return list(instance._providers.keys())

    @classmethod
    def get_available_models(cls, respect_restrictions: bool = True) -> dict[str, ProviderType]:
        """Get mapping of all available models to their providers.

        Args:
            respect_restrictions: If True, filter out models not allowed by restrictions

        Returns:
            Dict mapping model names to provider types
        """
        # Import here to avoid circular imports
        from utils.model_restrictions import get_restriction_service

        restriction_service = get_restriction_service() if respect_restrictions else None
        models: dict[str, ProviderType] = {}
        instance = cls()

        for provider_type in instance._providers:
            for provider in cls.get_providers(provider_type):
                if not provider:
                    continue

                try:
                    available = provider.list_models(respect_restrictions=respect_restrictions)
                except NotImplementedError:
                    logging.warning("Provider %s does not implement list_models", provider_type)
                    continue

                for model_name in available:
                    # Prevent double restriction filtering (Fixed Issue #98)
                    if (
                        restriction_service
                        and not respect_restrictions
                        and not restriction_service.is_allowed(provider_type, model_name)
                    ):
                        logging.debug("Model %s filtered by restrictions", model_name)
                        continue
                    models[model_name] = provider_type

        return models

    @classmethod
    def get_available_model_names(cls, provider_type: Optional[ProviderType] = None) -> list[str]:
        """Get list of available model names, optionally filtered by provider.

        This respects model restrictions automatically.

        Args:
            provider_type: Optional provider to filter by

        Returns:
            List of available model names
        """
        available_models = cls.get_available_models(respect_restrictions=True)

        if provider_type:
            return [name for name, ptype in available_models.items() if ptype == provider_type]
        else:
            return list(available_models.keys())

    @classmethod
    def _get_api_key_for_provider(cls, provider_type: ProviderType) -> Optional[str]:
        """Get API key for a provider from environment variables.

        Args:
            provider_type: Provider type to get API key for

        Returns:
            API key string or None if not found
        """
        key_mapping = {
            ProviderType.GOOGLE: "GEMINI_API_KEY",
            ProviderType.OPENAI: "OPENAI_API_KEY",
            ProviderType.XAI: "XAI_API_KEY",
            ProviderType.OPENROUTER: "OPENROUTER_API_KEY",
            ProviderType.CUSTOM: "CUSTOM_API_KEY",  # Can be empty for providers that don't need auth
            ProviderType.DIAL: "DIAL_API_KEY",
            ProviderType.CLI: None,  # CLI providers don't use API keys
        }

        env_var = key_mapping.get(provider_type)
        if not env_var:
            return None

        return os.getenv(env_var)

    @classmethod
    def _get_allowed_models_for_provider(cls, provider: ModelProvider, provider_type: ProviderType) -> list[str]:
        """Get a list of allowed canonical model names for a given provider.

        Args:
            provider: The provider instance to get models for
            provider_type: The provider type for restriction checking

        Returns:
            List of model names that are both supported and allowed
        """
        from utils.model_restrictions import get_restriction_service

        restriction_service = get_restriction_service()

        allowed_models = []

        # Get the provider's supported models
        try:
            # Use list_models to get all supported models (handles both regular and custom providers)
            supported_models = provider.list_models(respect_restrictions=False)
        except (NotImplementedError, AttributeError):
            # Fallback to SUPPORTED_MODELS if list_models not implemented
            try:
                supported_models = list(provider.SUPPORTED_MODELS.keys())
            except AttributeError:
                supported_models = []

        # Filter by restrictions
        for model_name in supported_models:
            if restriction_service.is_allowed(provider_type, model_name):
                allowed_models.append(model_name)

        return allowed_models

    @classmethod
    def get_preferred_fallback_model(cls, tool_category: Optional["ToolModelCategory"] = None) -> str:
        """Get the preferred fallback model based on provider priority and tool category.

        This method orchestrates model selection by:
        1. Getting allowed models for each provider (respecting restrictions)
        2. Asking providers for their preference from the allowed list
        3. Falling back to first available model if no preference given

        Args:
            tool_category: Optional category to influence model selection

        Returns:
            Model name string for fallback use
        """
        from tools.models import ToolModelCategory

        effective_category = tool_category or ToolModelCategory.BALANCED
        first_available_model = None

        # Ask each provider for their preference in priority order
        for provider_type in cls.PROVIDER_PRIORITY_ORDER:
            for provider in cls.get_providers(provider_type):
                if provider:
                    allowed_models = cls._get_allowed_models_for_provider(provider, provider_type)

                    if not allowed_models:
                        continue

                    if not first_available_model:
                        first_available_model = sorted(allowed_models)[0]

                    preferred_model = provider.get_preferred_model(effective_category, allowed_models)

                    if preferred_model:
                        logging.debug(
                            f"Provider {provider_type.value} selected '{preferred_model}' for category '{effective_category.value}'"
                        )
                        return preferred_model

        # If no provider returned a preference, use first available model
        if first_available_model:
            logging.debug(f"No provider preference, using first available: {first_available_model}")
            return first_available_model

        # Ultimate fallback if no providers have models
        logging.warning("No models available from any provider, using default fallback")
        return "gemini-2.5-flash"

    @classmethod
    def get_available_providers_with_keys(cls) -> list[ProviderType]:
        """Get list of provider types that have valid API keys.

        Returns:
            List of ProviderType values for providers with valid API keys
        """
        available = []
        instance = cls()
        for provider_type in instance._providers:
            if any(cls.get_providers(provider_type)):
                available.append(provider_type)
        return available

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached provider instances."""
        instance = cls()
        # Reset all initialized providers
        instance._initialized_providers = {
            ptype: [None] * len(classes) for ptype, classes in instance._providers.items()
        }

    @classmethod
    def reset_for_testing(cls) -> None:
        """Clear all registrations and initialized instances for a clean test slate."""
        instance = cls()
        instance._providers.clear()
        instance._initialized_providers.clear()

    @classmethod
    def unregister_provider(
        cls, provider_type: ProviderType, provider_class: Optional[type[ModelProvider]] = None
    ) -> None:
        """Unregister a provider or specific class (mainly for testing)."""
        instance = cls()
        if provider_class is None:
            instance._providers.pop(provider_type, None)
            instance._initialized_providers.pop(provider_type, None)
            return

        classes = instance._providers.get(provider_type, [])
        if not classes:
            return
        try:
            idx = classes.index(provider_class)
        except ValueError:
            return
        # Remove class and its initialized instance at same index
        classes.pop(idx)
        init_list = instance._initialized_providers.get(provider_type, [])
        if idx < len(init_list):
            init_list.pop(idx)


def register_additional_provider(
    provider_type: ProviderType, provider_class: type[ModelProvider]
) -> None:
    """Semantic helper to explicitly append a provider to a type."""
    ModelProviderRegistry.register_provider(provider_type, provider_class, append=True)


def get_primary_provider_class(
    provider_type: ProviderType,
) -> Optional[type[ModelProvider]]:
    """Compatibility accessor for tests/code expecting a single provider class per type."""
    instance = ModelProviderRegistry()
    provider_list = instance._providers.get(provider_type)
    return provider_list[0] if provider_list else None
