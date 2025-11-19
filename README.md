# Zen MCP Server – Coldaine Augmented Fork

This repository is Coldaine’s maintained and augmented fork of the original BeehiveInnovations/zen-mcp-server. It layers extensive planning for LangGraph-based multi-agent flows, custom provider endpoints, and tooling that reflects Coldaine’s local-first, CLI-centric workflows. Treat this repo as the authoritative source for the fork—documentation and scripts no longer mirror upstream defaults.

## Fork Scope
- Adds comprehensive research docs (LangGraph architecture, tool consolidation, CLI integration) that chart the upcoming multi-agent refactor.
- Maintains custom model registries (`conf/custom_models.json`) and consensus defaults tuned for Coldaine’s API keys and infrastructure.
- Ships extra helper scripts (`patch/`, `docker/scripts/`, PowerShell variants) to keep the fork cross-platform and reproducible without upstream dependencies.

## Key Goals
1. **LangGraph Migration**: Transition to a stateful, multi-agent architecture using LangGraph.
2. **Unified Model Gateway**: Integrate Bifrost/LiteLLM to centralize API key management and routing.
3. **Tool Consolidation**: Streamline 16 tools into ~9 core agents (Architect, Coder, Researcher, etc.).
4. **State Persistence**: Implement Redis-based checkpointing for robust conversation memory.
5. **CLI Execution**: Support SSH-based remote command execution.

## Quick Start
1. Clone: `git clone https://github.com/Coldaine/zen-mcp-server.git && cd zen-mcp-server`
2. Env: Copy .env.example to .env; configure `UNIFIED_LLM_GATEWAY` and `REDIS_URL`.
3. Run: `./run-server.sh`
4. Use: In Claude Code or Gemini CLI, reference "zen" server for multi-agent workflows.

## Setup
- Install: Python 3.10+, uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- Keys: See .env.example (API keys are now managed by the Gateway, not the MCP server).
- Tools: Agents are orchestrated by LangGraph; configuration via `conf/agents.json` (upcoming).

For details, see `docs/MIGRATION_MASTER_PLAN.md`.

License: Apache 2.0

## Current Project Status
- **Phase 0: Preparation** – Complete (Documentation aligned, Master Plan created).
- **Phase 1: Foundation & Dependencies** – Pending (Gateway integration, Redis setup).
- **Phase 2: LangGraph Core Implementation** – Pending (StateGraph, Supervisor).
- **Phase 3: Tool Consolidation** – Pending (Refactoring tools into agents).
- **Phase 4: Cutover & Cleanup** – Pending.
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
