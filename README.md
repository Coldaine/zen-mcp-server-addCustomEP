# Zen MCP Server – Coldaine Augmented Fork

This repository is Coldaine’s maintained and augmented fork of the original BeehiveInnovations/zen-mcp-server. It layers extensive planning for LangGraph-based multi-agent flows, custom provider endpoints, and tooling that reflects Coldaine’s local-first, CLI-centric workflows. Treat this repo as the authoritative source for the fork—documentation and scripts no longer mirror upstream defaults.

## Fork Scope
- Adds comprehensive research docs (LangGraph architecture, tool consolidation, CLI integration) that chart the upcoming multi-agent refactor.
- Maintains custom model registries (`conf/custom_models.json`) and consensus defaults tuned for Coldaine’s API keys and infrastructure.
- Ships extra helper scripts (`patch/`, `docker/scripts/`, PowerShell variants) to keep the fork cross-platform and reproducible without upstream dependencies.

## Key Goals
1. Default to Kilo Code API for OpenRouter models (interchangeable substitution with fallback).
2. Consensus tool calls 3 models in parallel: qwen3max, glm4.5 (Z.AI), kimi-k2 (Moonshot), with randomized stances.
3. Headless CLI integration for gemini, qwen, codex, claude code (subprocess execution, no API keys).
4. Live testing with qwen3-0.6b for all LLM calls (no fallbacks except headless CLI).
5. Additional model endpoints from _ModelLibrary.json (native where possible).

## Quick Start
1. Clone: `git clone https://github.com/Coldaine/zen-mcp-server.git && cd zen-mcp-server`
2. Env: Copy .env.example to .env; add API keys (KILO_API_KEY, Z_AI_API_KEY, MOONSHOT_API_KEY, QWEN_API_KEY).
3. Run: `./run-server.sh`
4. Use: In Claude Code or Gemini CLI, reference "zen" server for multi-model workflows.

## Setup
- Install: Python 3.10+, uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- Keys: See .env.example for required (e.g., KILO_PREFERRED=true for default Kilo).
- Tools: Consensus (3 models parallel), chat, planner enabled; others via DISABLED_TOOLS="" in .env.

For details, see docs/ (getting-started.md, configuration.md).

License: Apache 2.0

- **Phase 1: Foundational Setup (Registry, Models, Defaults)** – Complete (GLM default set).
## Current Project Status
- **Prep Phase: Documentation Reorganization** – Complete (README refactored, CLI instructions organized in docs/refactor/, _ModelLibrary.json recovered, index.md added).
- **Phase 1: Foundational Setup (Registry, Models, Defaults)** – Pending (Kilo substitution, model merge, GLM default).
- **Phase 2: Core Tool Refactor (Consensus)** – Pending (parallel calls, randomized stances).
- **Phase 3: Testing Overhaul (Live Qwen)** – Pending.
- **Phase 4: Advanced Integration (Headless CLI)** – Pending.

**Milestone Updates:**
- README refactored and pushed.
- CLI instructions organized in docs/refactor/.
- _ModelLibrary.json recovered and committed.
- Agent prompts updated to include status reporting.


- **Phase 1: Foundational Setup (Registry, Models, Defaults)** – Complete (GLM default set).
## Current Project Status
- **Prep Phase: Documentation Reorganization** – Complete (README refactored, CLI instructions organized in docs/refactor/, _ModelLibrary.json recovered, index.md added).
- **Phase 1: Foundational Setup (Registry, Models, Defaults)** – Complete (GLM default set, registry updated, models merged, Kilo routing configured).
- **Phase 2: Core Tool Refactor (Consensus)** – Pending (parallel calls, randomized stances).
- **Phase 3: Testing Overhaul (Live Qwen)** – Pending.
- **Phase 4: Advanced Integration (Headless CLI)** – Pending.

**Milestone Updates:**
- README refactored and pushed.
- CLI instructions organized in docs/refactor/.
- _ModelLibrary.json recovered and committed.
- Agent prompts updated to include status reporting.


- **Phase 1: Foundational Setup (Registry, Models, Defaults)** – Complete (GLM default set).
## Current Project Status
- **Prep Phase: Documentation Reorganization** – Complete (README refactored, CLI instructions organized in docs/refactor/, _ModelLibrary.json recovered, index.md added).
- **Phase 1: Foundational Setup (Registry, Models, Defaults)** – Pending (Kilo substitution, model merge, GLM default).
- **Phase 2: Core Tool Refactor (Consensus)** – Pending (parallel calls, randomized stances).
- **Phase 3: Testing Overhaul (Live Qwen)** – Pending.
- **Phase 4: Advanced Integration (Headless CLI)** – Pending.

**Milestone Updates:**
- README refactored and pushed.
- CLI instructions organized in docs/refactor/.
- _ModelLibrary.json recovered and committed.
- Agent prompts updated to include status reporting.


- **Phase 1: Foundational Setup (Registry, Models, Defaults)** – Complete (GLM default set).
## Current Project Status
- **Prep Phase: Documentation Reorganization** – Complete (README refactored, CLI instructions organized in docs/refactor/, _ModelLibrary.json recovered, index.md added).
- **Phase 1: Foundational Setup (Registry, Models, Defaults)** – Pending (Kilo substitution, model merge, GLM default).
- **Phase 2: Core Tool Refactor (Consensus)** – Pending (parallel calls, randomized stances).
- **Phase 3: Testing Overhaul (Live Qwen)** – Pending.
- **Phase 4: Advanced Integration (Headless CLI)** – Pending.

**Milestone Updates:**
- README refactored and pushed.
- CLI instructions organized in docs/refactor/.
- _ModelLibrary.json recovered and committed.
- Agent prompts updated to include status reporting.


- **Phase 1: Foundational Setup (Registry, Models, Defaults)** – Complete (GLM default set).
## Current Project Status
- **Prep Phase: Documentation Reorganization** – Complete (README refactored, CLI instructions organized in docs/refactor/, _ModelLibrary.json recovered, index.md added).
- **Phase 1: Foundational Setup (Registry, Models, Defaults)** – Pending (Kilo substitution, model merge, GLM default).
- **Phase 2: Core Tool Refactor (Consensus)** – Pending (parallel calls, randomized stances).
- **Phase 3: Testing Overhaul (Live Qwen)** – Pending.
- **Phase 4: Advanced Integration (Headless CLI)** – Pending.

**Milestone Updates:**
- README refactored and pushed.
- CLI instructions organized in docs/refactor/.
- _ModelLibrary.json recovered and committed.
- Agent prompts updated to include status reporting.


## Current Project Status

- **Phase 1: Foundational Setup** – Complete (GLM default set, registry updated, models merged, Kilo routing configured).
- **Phase 2: Core Tool Refactor (Consensus)** – Pending.
- **Phase 3: Testing Overhaul (Live Qwen)** – Pending.
- **Phase 4: Advanced Integration (Headless CLI)** – Pending.

## Current Project Status

- **Phase 1: Foundational Setup** – Complete (GLM default set).
- **Phase 2: Core Tool Refactor (Consensus)** – Pending.
- **Phase 3: Testing Overhaul (Live Qwen)** – Pending.
- **Phase 4: Advanced Integration (Headless CLI)** – Pending.
