# Refactor Continuation Plan

## Completed Work
- **Registry Refactor**: Implemented `append=True` support and index-based retrieval in `ModelProviderRegistry`.
- **Kilo/OpenRouter Integration**: Added Kilo API support, proxy handling, and prefix resolution.
- **Consensus Async**: Implemented concurrent model execution in `ConsensusTool`.
- **Testing**: Fixed `tests/test_providers.py` and added `tests/test_registry_behavior.py`.

## Remaining Tasks

### 1. CLI Bridge Provider (Pillar 3)
- **Objective**: Enable CLI tools to route to MCP models safely.
- **Tasks**:
  - Create `providers/cli_bridge.py`.
  - Implement argument validation and registration logic.
  - Add hybrid routing to `providers/registry.py` (if not fully covered by `append=True`).
  - Add tests for CLI provider.

### 2. Testing & Model Updates (Pillar 4)
- **Objective**: Standardize on efficient models for CI/dev.
- **Tasks**:
  - Update `tests/conftest.py` to use `qwen3:0.6b` or similar lightweight models where appropriate.
  - Ensure all tests use `clean_registry` or similar fixtures to avoid pollution.
  - Mark vision tests as xfail if they are flaky locally.

### 3. Documentation & Chores (Pillar 5)
- **Objective**: Clean up docs and scripts.
- **Tasks**:
  - Update `README.md` with Kilo usage instructions.
  - Create `docs/CLI_INTEGRATION.md` (if not exists or needs update).
  - Run `ruff` and `isort` to ensure code quality.

## Next Immediate Step
- Implement the CLI Bridge Provider.
