### Resuming Task: Finalized Re-Implementation Plan

Resuming the task. The documentation is now reorganized with the new `docs/index.md` and `docs/research/CLI_Substitution.md` files, and the `README.md` is updated to reflect the project's new direction. All changes are committed and pushed to the main branch.

Here is the finalized, reordered implementation plan, incorporating all your feedback. It's streamlined for a personal tool, with a logical build order (foundation first), and ready for execution.

#### Final Reordered Implementation Plan

**Phase 1: Foundational Setup (Registry, Models, Defaults)**
- **Objective**: Establish the core routing logic and model availability. This phase implements **Goal 1 (Kilo substitution for OpenRouter only)**, **Goal 5 (additional native model endpoints)**, and the **GLM-4.5 default model** requirement.
- **Tasks**:
    1.  **Update `config.py`**: Set `DEFAULT_MODEL = "glm-4.5"`.
    2.  **Update `providers/registry.py`**:
        -   Add new `ProviderType` enums for `KILO`, `MOONSHOT`, `Z_AI`, etc.
        -   Update `PROVIDER_PRIORITY_ORDER` to `[...native providers..., KILO, ...other native..., OPENROUTER]`.
        -   Modify `get_provider_for_model` to check a model's `upstream_provider` from the JSON. If it's `openrouter`, attempt to route through the `KiloProvider`. Otherwise, route to the specific native provider.
    3.  **Update `providers/openrouter.py`**: This provider will now primarily handle fallbacks from Kilo.
    4.  **Create New Provider Files**: Create `providers/kilo_provider.py`, `providers/moonshot_provider.py`, `providers/z_ai_provider.py`, etc. These will be simple classes inheriting from `OpenAICompatibleProvider`, configured with the specific `base_url` from `_ModelLibrary.json`.
    5.  **Update `conf/custom_models.json`**: Merge entries from `docs/_ModelLibrary.json`, ensuring native endpoints are correctly configured and OpenRouter models are flagged for Kilo routing.
    6.  **Update `.env.example`**: Add `KILO_PREFERRED=true` and placeholders for new native API keys (`Z_AI_API_KEY`, `MOONSHOT_API_KEY`).
- **Tests**:
    -   Unit test `get_provider_for_model` to ensure correct routing (e.g., `claude-4.1-sonnet` -> `KiloProvider`, `kimi-k2-instruct` -> `MoonshotProvider`).
    -   Integration test a `listmodels` call to verify all new models are loaded correctly.

**Phase 2: Core Tool Refactor (Consensus)**
- **Objective**: Implement the parallel, randomized consensus workflow. This addresses **Goal 2**.
- **Tasks**:
    1.  **Update `tools/consensus.py`**:
        -   Hardcode the `models_to_consult` to `["qwen3max", "glm4.5", "kimi-k2-instruct"]`.
        -   Implement `random.shuffle` on a list of stances (`["for", "against", "neutral"]`) and assign one to each model before the concurrent calls.
        -   Ensure the existing `asyncio.gather` logic is used for parallel execution.
- **Tests**:
    -   Unit test to confirm stances are randomized on each run.
    -   Live integration test for the `consensus` tool, asserting that three responses are returned from the correct native providers.

**Phase 3: Testing Overhaul (Live Qwen)**
- **Objective**: Switch all tests to use live `qwen3-0.6b` calls, removing mocks and fallbacks. This addresses **Goal 4**.
- **Tasks**:
    1.  **Update `tests/conftest.py`**: Modify fixtures to default to and require the `qwen3-0.6b` model for any test needing an LLM.
    2.  **Refactor Tests**: Remove any mock objects or fallback logic in `simulator_tests/` and `tests/` that would prevent live calls.
    3.  **CI Configuration**: Update `.github/workflows/test.yml` to require a `QWEN_API_KEY` secret and use it in the test environment.
- **Tests**: The entire test suite now runs against a live model, providing higher-fidelity validation.

**Phase 4: Advanced Integration (Headless CLI)**
- **Objective**: Integrate headless CLI tools as a new provider type. This addresses **Goal 3**.
- **Tasks**:
    1.  **Update `providers/base.py`**: Add `ProviderType.HEADLESS`.
    2.  **Create `providers/headless_provider.py`**:
        -   Implement `validate_model_name` to check if a CLI binary (e.g., `gemini`, `qwen`) exists on the system `PATH`.
        -   Implement `generate_content` to use `subprocess.run` to execute the CLI tool with appropriate headless flags (e.g., `gemini "prompt" --model ...`).
        -   Add logic to parse `stdout` (preferring JSON, falling back to regex for code blocks) and normalize it into a `ModelResponse`.
    3.  **Update `providers/registry.py`**: Register the `HeadlessProvider` and add it to the priority list (e.g., after `CUSTOM`).
- **Tests**:
    -   Unit tests with mocked `subprocess.run` to validate output parsing.
    -   An integration test using a live CLI tool (e.g., `qwen`) to ensure the end-to-end flow works.

This reordered plan ensures a stable foundation before building more complex features. We are ready to begin with Phase 1.
