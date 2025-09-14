
---
doc_type: design
subsystem: providers
version: 1.0.0
status: draft
owners: [kilo-code]
last_reviewed: 2025-09-14
description: Detailed design and implementation plan for refactoring the ModelProviderRegistry to support multiple CLI providers (Codex and Gemini) simultaneously, with auto-detection, unified routing, and full testing/documentation.
---

# Multi-CLI Provider Refactor: Enabling Simultaneous Codex and Gemini CLI Support

## Introduction

### Background
The current ModelProviderRegistry supports only one provider instance per `ProviderType` (e.g., CLI), leading to overwriting when registering both Codex CLI (`CLIBridgeProvider`) and Gemini CLI (`GeminiCLIBridgeProvider`). This prevents simultaneous use. CLI providers are already simplified to single logical models ("codex-cli", "gemini-cli"), with binary auto-detection (shutil.which) and no ENABLE flags, aligning with Codex CLI's minimalist design (no per-command model selection, default via env/API).

### Requirements
- **Functional**: Register multiple providers per type (CLI); auto-detect binaries (codex, gemini); aggregate models/restrictions; route requests to correct provider (e.g., "codex-cli" → CLIBridge).
- **Non-Functional**: Backward compatible (single-provider behavior unchanged); no regressions (full test suite passes); >95% coverage; lint-compliant.
- **Constraints**: Preserve priority (CLI after native APIs); handle missing binaries gracefully; no new deps unless needed (e.g., tiktoken for tokens).
- **Interfaces**: Update `get_provider_for_model`, `get_available_models`, `get_preferred_fallback_model` for multi-iter; new `get_providers(type)`.
- **Non-Goals**: Dynamic CLI discovery beyond binaries; per-provider restrictions (CLI_ALLOWED_MODELS applies globally); streaming/JSON for CLI (unsupported).

### Assumptions
- Binaries on PATH or via env (CODEX_CLI_BINARY, GEMINI_CLI_BINARY).
- CLI models don't overlap (unique names: "codex-cli", "gemini-cli").
- Codex/Gemini CLIs remain sync, single-model defaults (per web search).

### Risks & Mitigations
- **Risk**: Breaking single-provider code. **Mitigation**: get_provider returns first; deprecation logs.
- **Risk**: Double-filtering restrictions. **Mitigation**: Aggregate with respect_restrictions=False per provider.
- **Risk**: Init failures (missing binary). **Mitigation**: Lazy init with None slots; skip in iteration.
- **Risk**: Test complexity. **Mitigation**: Parametrized matrix; mock subprocess/which.

## High-Level Architecture

### Current State
- Registry: Singleton dict[ProviderType, class]; get_provider initializes one.
- CLI: Two classes, both ProviderType.CLI; register second overwrites first.
- Resolution: Iterates types, but assumes one per type.

### Proposed Changes
- Registry: dict[ProviderType, list[class]] for _providers; list[instance|None] for _initialized_providers.
- Registration: Append classes; get_providers initializes list on-demand.
- Resolution: For each type, iterate providers until match.
- Aggregation: list_models across all CLI providers; merge for available models.
- Fallback: Collect from all, prefer first with preference.

**Registry Flow** (Mermaid):
```mermaid
graph TD
  A[register_provider(CLI, CLIBridge)] --> B[_providers[CLI] = [CLIBridge]]
  C[register_provider(CLI, GeminiCLIBridge)] --> D[_providers[CLI] = [CLIBridge, GeminiCLIBridge]]
  E[get_provider_for_model('codex-cli')] --> F[For CLI type: get_providers(CLI)]
  F --> G[Init list: [CLIBridge, None] → [CLIBridge, GeminiCLIBridge]]
  G --> H[Iterate: CLIBridge.validate('codex-cli') = True → Return CLIBridge]
  I[get_available_models] --> J[Aggregate: CLIBridge.list_models() + GeminiCLIBridge.list_models()]
  J --> K[Apply restrictions once; return {'codex-cli': CLI, 'gemini-cli': CLI}]
```

### Tradeoffs
- **Pros**: Extensible (add more CLIs); isolated (no crosstalk); simple (lazy lists).
- **Cons**: Slight perf overhead (iter lists; negligible, <5 providers); more complex init (handle None).
- **Alternatives**: Separate types (CLI_Codex, CLI_Gemini)—violates enum; rejected for unification.

## Incorporated Decisions from CLI ImplementationPlan 0914.md

This plan builds on the earlier CLI integration analysis (version 1.1.0, dated 2025-09-12), adopting its lean philosophy while extending for multi-provider support.

### Key Decisions Integrated
- **Lean Provider Bridge Approach**: Chosen over heavy generic wrapper for simplicity. Our CLI bridges use minimal subprocess.run (stdin prompt, stdout response), avoiding caching/streaming/retry. Rationale: CLI tools like Codex have simple I/O, system auth, and no API complexity—focus on core mapping.
- **Core Responsibilities**:
  1. Subprocess Execution: Blocking call with timeout (env: *_TIMEOUT=30s).
  2. I/O Mapping: Concat system + user to stdin; stdout.strip() to content; empty usage (no tokens from CLI).
  3. Error Normalization: Non-zero/timeout → RuntimeError with stderr snippet.
  4. Capability Stubbing: Static ModelCapabilities (no temp/streaming/images/JSON; conservative limits).
  5. Config/Discovery: Static per-CLI (e.g., Codex: ["exec", "--quiet"]); auto-register if binary found.
- **Codex Specifics**: No model selection (-m unsupported; defaults to GPT-5 via ChatGPT plan). Prompts via stdin; reinforces single-model design ("codex-cli").
- **Out of Scope (Adopted)**: No caching, streaming, API fallback, retries, generic protocol—CLI is sync/simple; add later if needed.

### Adjustments to Plan
- **Testing**: Add live integration (Phase 4): Create test_cli_bridge_live.py and test_gemini_cli_live.py with skips on binary missing/error for portability/CI (use pytest.mark.live; gate in CI).
- **CI**: Use markers to skip live tests in CI (Phase 6).
- **Rationale Alignment**: Multi-registration enables multiple lean bridges without added complexity.

This ensures the refactor remains lean while supporting coexistence.

## Implementation Phases

### Phase 1: Multi-Provider Registry Refactor
Goal: Enable list-based registration/init/resolution without breaking singles.
Success: Both CLI register; models aggregate; resolution routes correctly; existing tests pass.
Steps:
1. Update data structures: _providers = {}; _providers[ptype] = [] (list of classes).
2. register_provider(ptype, class): _providers[ptype].append(class).
3. get_providers(ptype): If not initialized, for each class in _providers[ptype], init (CLI: which binary; API: api_key check) and store in parallel _initialized[ptype] = list[instances].
4. get_provider_for_model(model): For ptype in priority: providers = get_providers(ptype); for p in providers: if p and p.validate_model_name(model): return p.
5. get_available_models: For ptype: providers = get_providers(ptype); aggregate = []; for p in providers if p: aggregate += p.list_models(False); then filter aggregate with restrictions.
6. get_preferred_fallback_model(category): For ptype: allowed = []; for p in get_providers(ptype) if p: allowed += _get_allowed_models_for_provider(p, ptype); for model in allowed: if p.get_preferred_model(category, allowed): return model; fallback to first.
7. get_available_providers_with_keys: [ptype for ptype in _providers if any(p for p in get_providers(ptype) if p)].
8. clear_cache: For each ptype: _initialized[ptype] = [None] * len(_providers[ptype]).
9. reset_for_testing: _instance = None; _providers.clear(); _initialized.clear().
10. unregister_provider(ptype, class): Remove class from _providers[ptype]; adjust _initialized.
11. Backward: get_provider(ptype): return get_providers(ptype)[0] if any else None; log "Deprecated: use get_providers".
12. Tests: tests/test_registry_multi.py - Mock two CLI classes; assert len(get_providers(CLI))==2; aggregate models; resolution picks first match.
13. Logs: DEBUG "Iterating {len(providers)} providers for {ptype}".
14. Hygiene: pre-commit run -a on registry.py.

### Phase 2: CLI Provider Normalization
[Unchanged from original]

[All other phases unchanged]

## Implementation Phases

### Phase 1: Multi-Provider Registry Refactor
Goal: Enable list-based registration/init/resolution without breaking singles.
Success: Both CLI register; models aggregate; resolution routes correctly; existing tests pass.
Steps:
1. Update data structures: _providers = {}; _providers[ptype] = [] (list of classes).
2. register_provider(ptype, class): _providers[ptype].append(class).
3. get_providers(ptype): If not initialized, for each class in _providers[ptype], init (CLI: which binary; API: api_key check) and store in parallel _initialized[ptype] = list[instances].
4. get_provider_for_model(model): For ptype in priority: providers = get_providers(ptype); for p in providers: if p and p.validate_model_name(model): return p.
5. get_available_models: For ptype: providers = get_providers(ptype); aggregate = []; for p in providers if p: aggregate += p.list_models(False); then filter aggregate with restrictions.
6. get_preferred_fallback_model(category): For ptype: allowed = []; for p in get_providers(ptype) if p: allowed += _get_allowed_models_for_provider(p, ptype); for model in allowed: if p.get_preferred_model(category, allowed): return model; fallback to first.
7. get_available_providers_with_keys: [ptype for ptype in _providers if any(p for p in get_providers(ptype) if p)].
8. clear_cache: For each ptype: _initialized[ptype] = [None] * len(_providers[ptype]).
9. reset_for_testing: _instance = None; _providers.clear(); _initialized.clear().
10. unregister_provider(ptype, class): Remove class from _providers[ptype]; adjust _initialized.
11. Backward: get_provider(ptype): return get_providers(ptype)[0] if any else None; log "Deprecated: use get_providers".
12. Tests: tests/test_registry_multi.py - Mock two CLI classes; assert len(get_providers(CLI))==2; aggregate models; resolution picks first match.
13. Logs: DEBUG "Iterating {len(providers)} providers for {ptype}".
14. Hygiene: pre-commit run -a on registry.py.

### Phase 2: CLI Provider Normalization
Goal: Auto-register both if binaries present; no flags.
Success: server.py registers both; missing binary skips.
Steps:
1. cli_bridge.py: Init raises if no which(binary); but in registry, catch in get_provider.
2. gemini_cli_bridge.py: Similar (already does).
3. server.py: if ProviderType.CLI in registry: register CLIBridgeProvider(CLI); register GeminiCLIBridgeProvider(CLI).
4. Env: Already CODEX_CLI_BINARY="codex", GEMINI_CLI_BINARY="gemini"; document.
5. Remove ENABLE from .env.example, comments.
6. Tests: test_cli_auto_detect.py - @patch('shutil.which') for scenarios; assert registration only if present.

### Phase 3: Routing & Simplification
Goal: Unified resolution; no CLI specials.
Success: Mixed models route correctly; fallback prefers CLI.
Steps:
1. Audit: No shorts in server/tools (confirmed).
2. get_provider_for_model: Uses multi (from Phase 1); test "codex-cli" → CLIBridge, "gemini-cli" → Gemini.
3. Restrictions: CLI_ALLOWED_MODELS filters all CLI models (no per-provider).
4. Fallback: Prefers CLI (priority); test with both.
5. Full pytest -q; cov >95%.
6. Edge: In generate_content, re-which before run; raise if gone.

### Phase 4: Dual CLI Test Matrix
Goal: Coverage for all scenarios.
Success: 90%+ cov; no crosstalk.
Steps:
1. test_dual_cli_matrix.py: @parametrize(["none", "codex", "gemini", "both"]).
2. Listing: assert models == expected (e.g., both → ["codex-cli", "gemini-cli"]).
3. Resolution: Mock validate; assert provider class for each model.
4. Isolation: "codex-cli".validate on Gemini → False.
5. Integration: @patch(subprocess.run); assert cmd binary for each.
6. Cov: --cov-report=term-missing; fix gaps.

### Phase 5: Documentation
Goal: Clear guidance.
Success: No broken links; pre-commit passes.
Steps:
1. README.md: Add "Local CLI Providers" section: Auto-detect, env vars, install (brew install openai/codex/codex; npm i -g @google/generative-ai-cli for gemini).
2. .env.example: Remove ENABLE; add BINARY notes, TIMEOUT.
3. docs/providers.md: Create; describe multi-registration, flow diagram.
4. CHANGELOG: feat entry under Unreleased.
5. Getting Started: Add binary install in docs/getting-started.md.
6. pre-commit run -a.

### Phase 6: Stabilize
Goal: Production-ready.
Success: 100% tests, committed.
Steps:
1. pre-commit -a.
2. pytest --cov-fail-under=95.
3. Commit: feat(providers): ... body with phases.
4. Push/verify.

### Phase 7: Hardening (Optional)
Goal: Polish.
Steps:
1. Re-which in generate_content.
2. tiktoken for count_tokens (add to requirements-dev.txt).
3. CLIBaseProvider in base.py: Common binary/timeout/subprocess.
4. Metadata: execution_time already; add verbose via env.

This plan is self-contained, executable, and grounded in code/search. Approve to switch to code mode?
</result>
</attempt_completion>
