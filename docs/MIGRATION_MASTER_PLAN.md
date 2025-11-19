# Zen MCP Server - LangGraph Migration Master Plan

## Executive Summary

This document serves as the **Single Source of Truth** for the "Big-Bang" migration of the Zen MCP Server. We are moving from a traditional tool-based architecture to a **LangGraph-based multi-agent system** powered by a unified model gateway.

**Core Objectives:**
1.  **Architecture**: Replace linear tool execution with **LangGraph StateGraph**.
2.  **Model Gateway**: Integrate **Bifrost** (preferred) or LiteLLM to remove provider secrets from the MCP server.
3.  **State Persistence**: Implement **Redis-based checkpointing** for robust conversation memory.
4.  **Tool Consolidation**: Reduce 16 tools to ~9 core tools to eliminate redundancy.
5.  **CLI Execution**: Implement SSH-based remote command execution.

---

## Phase 1: Foundation & Dependencies

**Goal**: Set up the runtime environment and dependencies without breaking existing functionality immediately.

- [ ] **Dependency Management**:
    - Add `langgraph`, `langgraph-checkpoint-redis`, `redis` to `requirements.txt`.
    - Remove direct provider SDKs (`google-generativeai`, `anthropic`, etc.) *after* gateway integration is complete.
- [ ] **Gateway Configuration**:
    - Define `UNIFIED_LLM_GATEWAY` and `UNIFIED_LLM_API_KEY` in `.env.example`.
    - Create `providers/gateway.py` to handle all LLM requests via the gateway.
- [ ] **Redis Setup**:
    - Add Redis service to `docker-compose.yml`.
    - Configure `REDIS_URL` in `.env.example`.

## Phase 2: LangGraph Core Implementation

**Goal**: Replace the internal dispatch logic with a LangGraph StateGraph.

- [ ] **State Definition**:
    - Define `AgentState` (TypedDict) to hold conversation history, current step, and tool outputs.
- [ ] **Graph Construction**:
    - Create the `Supervisor` node (router).
    - Create worker nodes for each consolidated tool category.
- [ ] **Checkpointing**:
    - Initialize `RedisSaver` and attach it to the graph compilation.

## Phase 3: Tool Consolidation

**Goal**: Refactor existing tools into LangGraph nodes/tools.

| New Tool/Node | Replaces | Description |
| :--- | :--- | :--- |
| **Architect** | `analyze`, `refactor` | High-level system design and refactoring strategies. |
| **Debugger** | `debug`, `tracer` | Root cause analysis and execution tracing. |
| **Reviewer** | `codereview`, `secaudit`, `precommit` | Code quality, security, and pre-commit checks. |
| **Coder** | *New* | specialized code generation (from `planner` + `chat`). |
| **Researcher** | `consensus` | Multi-model consensus and deep research. |
| **Terminal** | *New* | SSH-based CLI execution. |
| **Utilities** | `listmodels`, `version` | Kept as simple tools. |

## Phase 4: Cutover & Cleanup

**Goal**: Switch the entry point to the new system and remove legacy code.

- [ ] **Entry Point**: Update `server.py` to initialize the LangGraph app instead of the old tool list.
- [ ] **Legacy Removal**: Delete `providers/openai_provider.py`, `providers/gemini.py`, etc.
- [ ] **Documentation**: Update `README.md` and `docs/` to reflect the new architecture.

---

## Decision Log

| Decision | Selected Option | Rationale |
| :--- | :--- | :--- |
| **Model Gateway** | **Bifrost** | Higher performance (Go-based), lower latency than LiteLLM. |
| **Persistence** | **Redis** | Native JSON support in Redis 8.0+, official LangGraph checkpointer. |
| **Migration Style** | **Big-Bang** | Interdependencies between StateGraph and Tools make incremental migration too complex. |
