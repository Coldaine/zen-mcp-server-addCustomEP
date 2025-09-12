---
title: Agent Prompt for OpenRouter to Kilo Code Endpoint Conversion
doc_type: research
subsystem: providers
version: 1.0.0
status: draft
owners: ["architect"]
last_reviewed: 2025-01-12
---

# Agent Prompt: Convert OpenRouter Endpoints to Kilo Code Endpoints

## Task Overview
Convert all OpenRouter-based endpoints, configurations, and references in the Zen MCP Server codebase to use Kilo Code endpoints instead. This includes updating provider configurations, model definitions, API calls, and documentation while maintaining identical functionality.

## Important Context
**Kilo Code is currently a proxy service to OpenRouter with different billing.** The API structure, endpoints, headers, and request/response formats are identical to OpenRouter. The only differences are:
- Base URL: `https://kilocode.ai/api/openrouter/` instead of `https://openrouter.ai/api/v1/`
- Billing/pricing model (handled by Kilo Code)
- Authentication token (KILO_API_KEY instead of OPENROUTER_API_KEY)

## Files to Modify

### 1. Provider Implementation
**File:** `providers/openrouter.py`
- **Action:** Rename class from `OpenRouterProvider` to `KiloCodeProvider`
- **Action:** Update base URL from `https://api.kilocode.ai/api/openrouter/` to `https://kilocode.ai/api/openrouter/`
- **Action:** Change API key environment variable from `OPENROUTER_API_KEY` to `KILO_API_KEY`
- **Action:** Update all class references, method names, and variable names
- **Action:** Update FRIENDLY_NAME from "OpenRouter" to "Kilo Code"
- **Action:** Add comprehensive comments explaining Kilo Code is a proxy to OpenRouter
- **Action:** Update docstrings and comments referencing openrouter.ai

### 2. Provider Registry File
**File:** `providers/openrouter_registry.py`
- **Action:** Rename file to `providers/kilocode_registry.py`
- **Action:** Rename class `OpenRouterModelRegistry` to `KiloCodeModelRegistry`
- **Action:** Update all log messages and comments from "OpenRouter" to "Kilo Code"
- **Action:** Update docstrings and class descriptions

### 3. Model Configuration
**File:** `conf/custom_models.json`
- **Action:** Update all model entries that reference OpenRouter providers
- **Action:** Update the `_README` section to replace "OpenRouter" with "Kilo Code"
- **Action:** Change model descriptions from "via OpenRouter" to "via Kilo Code"
- **Action:** Update documentation URL if needed
- **Action:** Add comments explaining proxy relationship

### 4. Server Configuration
**File:** `server.py`
- **Action:** Update import statement from `providers.openrouter` to `providers.kilocode`
- **Action:** Change class reference from `OpenRouterProvider` to `KiloCodeProvider`
- **Action:** Update environment variable check from `OPENROUTER_API_KEY` to `KILO_API_KEY`
- **Action:** Change ProviderType.OPENROUTER to ProviderType.KILOCODE in registration
- **Action:** Update all log messages and validation messages
- **Action:** Update help text and configuration messages

### 5. Provider Types and Constants
**File:** `providers/base.py`
- **Action:** Change `OPENROUTER = "openrouter"` to `KILOCODE = "kilocode"`
- **Action:** Update any related constants or enums

### 6. Configuration Files
**File:** `.env.example`
- **Action:** Replace `OPENROUTER_API_KEY=your_openrouter_api_key_here` with `KILO_API_KEY=your_kilo_code_api_key_here`
- **Action:** Update comments from "OpenRouter" to "Kilo Code"
- **Action:** Update URLs from openrouter.ai to kilocode.ai
- **Action:** Change restriction environment variables from `OPENROUTER_ALLOWED_MODELS` to `KILOCODE_ALLOWED_MODELS`
- **Action:** Update header customization variables (KILO_REFERER instead of OPENROUTER_REFERER, etc.)

### 7. Utilities and Helpers
**File:** `tools/shared/base_tool.py`
- **Action:** Update `_get_openrouter_registry` to `_get_kilocode_registry`
- **Action:** Change class references from `OpenRouterModelRegistry` to `KiloCodeModelRegistry`
- **Action:** Update environment variable checks from `OPENROUTER_API_KEY` to `KILO_API_KEY`
- **Action:** Update log messages and comments

**File:** `tools/listmodels.py`
- **Action:** Update import statements for new registry class
- **Action:** Change environment variable references
- **Action:** Update display names from "OpenRouter" to "Kilo Code"
- **Action:** Update help text and descriptions

**File:** `utils/model_restrictions.py`
- **Action:** Change `OPENROUTER_ALLOWED_MODELS` to `KILOCODE_ALLOWED_MODELS`
- **Action:** Update ProviderType references from OPENROUTER to KILOCODE

### 8. Test Files
**Files:** All test files in `tests/` and `simulator_tests/`
- **Action:** Update test file names (e.g., `test_openrouter_*.py` → `test_kilocode_*.py`)
- **Action:** Update test class names and method names
- **Action:** Change API endpoint references in test configurations
- **Action:** Update mock URLs and test data
- **Action:** Update environment variable names in test setup
- **Action:** Change import statements for provider classes
- **Action:** Update assertion messages and error strings

**Key test files to update:**
- `tests/test_openrouter_provider.py` → `tests/test_kilocode_provider.py`
- `tests/test_openrouter_registry.py` → `tests/test_kilocode_registry.py`
- `simulator_tests/test_openrouter_models.py` → `simulator_tests/test_kilocode_models.py`
- `simulator_tests/test_openrouter_fallback.py` → `simulator_tests/test_kilocode_fallback.py`

### 9. Documentation
**File:** `README.md`
- **Action:** Replace all "OpenRouter" references with "Kilo Code"
- **Action:** Update API key setup instructions
- **Action:** Change URLs from openrouter.ai to kilocode.ai
- **Action:** Update model listing examples
- **Action:** Add section explaining Kilo Code's relationship to OpenRouter

**File:** `CLAUDE.md`
- **Action:** Update development guide references
- **Action:** Change environment variable names in examples
- **Action:** Update troubleshooting sections

### 10. System Prompts (if needed)
**Files:** All files in `systemprompts/`
- **Action:** Review for any hardcoded OpenRouter references
- **Action:** Update provider names in prompts if needed

## Naming Conventions

### Class and Variable Naming
- `OpenRouterProvider` → `KiloCodeProvider`
- `openrouter_provider` → `kilocode_provider`
- `OpenRouterModelRegistry` → `KiloCodeModelRegistry`
- `openrouter_models` → `kilocode_models`
- `OPENROUTER_API_KEY` → `KILO_API_KEY`
- `OPENROUTER_ALLOWED_MODELS` → `KILOCODE_ALLOWED_MODELS`
- `ProviderType.OPENROUTER` → `ProviderType.KILOCODE`

### URL and Endpoint Updates
- `https://openrouter.ai/api/v1/` → `https://kilocode.ai/api/openrouter/`
- Keep all sub-paths identical (e.g., `/chat/completions`, `/models`)

### Model ID Format
Keep existing model IDs unchanged since they reference the underlying providers (Google, OpenAI, etc.):
- `google/gemini-2.5-flash` (no change - this is the actual model ID)
- `openai/o3` (no change - this references OpenAI's model)
- `meta-llama/llama-3-70b` (no change - this references Meta's model)

### Environment Variable Names
- `OPENROUTER_API_KEY` → `KILO_API_KEY`
- `OPENROUTER_ALLOWED_MODELS` → `KILOCODE_ALLOWED_MODELS`
- `OPENROUTER_REFERER` → `KILO_REFERER`
- `OPENROUTER_TITLE` → `KILO_TITLE`
- `OPENROUTER_USER_AGENT` → `KILO_USER_AGENT`

## Required Comments
Add these types of comments throughout the codebase:

```python
# NOTE: Kilo Code is currently a proxy service to OpenRouter with identical API structure
# The only differences are the base URL and billing model - all functionality remains the same

# IMPORTANT: Kilo Code uses the same OpenRouter infrastructure and model availability
# API requests, headers, and responses are identical to OpenRouter

# TODO: If Kilo Code API diverges from OpenRouter in the future, this will need updates
```

## Testing Requirements
1. **Unit Tests:** All existing OpenRouter unit tests must pass with new naming
2. **Integration Tests:** Verify API calls work with new endpoints (may require API key)
3. **Simulator Tests:** Ensure model selection and conversation flows work correctly
4. **Configuration Tests:** Validate that new environment variables and configs load properly

## Validation Checklist
- [ ] All OpenRouter class names changed to KiloCode equivalents
- [ ] Base URL updated to `https://kilocode.ai/api/openrouter/`
- [ ] Environment variable changed from OPENROUTER_API_KEY to KILO_API_KEY
- [ ] All model restriction variables updated
- [ ] Provider type enum updated
- [ ] Documentation updated with new provider name
- [ ] Test files renamed and updated
- [ ] Comments added explaining proxy relationship
- [ ] No remaining "openrouter" references in codebase (case-insensitive search)

## Implementation Order
1. **Provider Layer:** Update `providers/base.py` for ProviderType enum
2. **Registry:** Rename and update `providers/openrouter_registry.py`
3. **Main Provider:** Update `providers/openrouter.py`
4. **Server Configuration:** Update `server.py` imports and registrations
5. **Configuration:** Update `.env.example` and environment variables
6. **Utilities:** Update helper classes and tools
7. **Tests:** Update all test files to use new naming
8. **Documentation:** Update README and other docs
9. **Validation:** Run full test suite and verify functionality

## Risk Mitigation
- **Backup:** Ensure all changes are in version control before starting
- **Gradual Testing:** Test each component after updates
- **Rollback Plan:** Keep track of all changed files for potential rollback
- **API Compatibility:** Verify Kilo Code API is accessible and functional

## Final Notes
This conversion is primarily a **renaming and rebranding exercise**. The underlying API functionality, request formats, model capabilities, and response handling should remain identical. The goal is to switch from OpenRouter billing to Kilo Code billing while maintaining all existing features.

**Remember:** Kilo Code currently uses OpenRouter's infrastructure, so any OpenRouter model availability, rate limits, or API behaviors will remain the same through the Kilo Code proxy.

## Search and Replace Patterns
Use these patterns for comprehensive replacement:

### Case-sensitive replacements:
- `OpenRouter` → `KiloCode` (class names, documentation)
- `openrouter` → `kilocode` (file names, variable names)
- `OPENROUTER` → `KILO` (environment variables)

### URL replacements:
- `https://openrouter.ai/api/v1/` → `https://kilocode.ai/api/openrouter/`
- `openrouter.ai` → `kilocode.ai`

### Environment variable patterns:
- `OPENROUTER_API_KEY` → `KILO_API_KEY`
- `OPENROUTER_ALLOWED_MODELS` → `KILOCODE_ALLOWED_MODELS`
- `OPENROUTER_*` → `KILO_*` (for header customization variables)