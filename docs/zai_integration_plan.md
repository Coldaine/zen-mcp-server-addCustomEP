# Z.AI Provider Integration Plan

This document outlines the plan to correctly integrate the Z.AI provider and the GLM-4.6 model into the application.

## Background

Previous attempts to integrate the Z.AI provider were flawed. They involved duplicating the `glm-4.6` model definition across all provider-specific model configuration files and attempting to use the existing OpenAI provider with a custom base URL. This approach is incorrect and pollutes the model lists of other providers.

## Plan

The following steps will be taken to correctly integrate the Z.AI provider:

### 1. Create a new `zai` provider

- A new `ZAI` provider type will be added to the `ProviderType` enum in `providers/shared/provider_type.py`.
- A new provider file `providers/zai.py` will be created. This file will contain the `ZAIProvider` class, which will inherit from `OpenAICompatibleProvider`.
- The `ZAIProvider` will be configured with the following:
    - `FRIENDLY_NAME`: "Z.AI"
    - `base_url`: "https://api.z.ai/api/paas/v4/"
    - `api_key`: The provider will use the `ZAI_API_KEY` environment variable for authentication.

### 2. Update the provider registry

The `providers/registry.py` file will be updated as follows:

- The new `ZAI` provider will be added to the `PROVIDER_PRIORITY_ORDER`.
- The `ZAI` provider will be added to the `key_mapping` to map it to the `ZAI_API_KEY` environment variable.
- The `get_provider` method will be updated to handle the initialization of the `ZAIProvider`, including setting the base URL.

### 3. Correct the model configuration

- The duplicated `glm-4.6` model definition will be removed from all `conf/*_models.json` files.
- A new `conf/zai_models.json` file will be created to contain the `glm-4.6` model definition. This will be the single source of truth for Z.AI models.

### 4. Register the new provider

The main `server.py` file will be updated to import and register the new `ZAIProvider`.

## Z.AI API Endpoint Details

- **Provider:** Z.AI (formerly Zhipu AI)
- **Chat Completions Endpoint:** `https://api.z.ai/api/paas/v4/chat/completions`
- **Authentication:** API key
- **Model Name:** `glm-4.6`
