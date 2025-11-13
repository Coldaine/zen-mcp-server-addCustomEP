# Documentation Register

_Last updated: 2025-11-12_

This register tracks every maintained document in the repository, its status, and who owns future updates. Use it alongside `docs/documentation-review-framework.md` to schedule audits and record the latest review date. Anything marked **Archive** should be treated as historical context only—refresh or rewrite before using it for implementation.

## Active & Draft Documents

| Path | Status | Owner | Last Reviewed | Purpose | Notes |
|------|--------|-------|---------------|---------|-------|
| README.md | Active | Coldaine | 2025-11-12 | Top-level overview of the augmented fork, goals, and quick start | Updated to clarify fork scope and custom defaults |
| AGENTS.md | Active | Coldaine | 2025-11-12 | Contributor guidelines covering structure, commands, style, and PR expectations | Reference in onboarding or contributor docs |
| PR_SUMMARY.md | Active | Coldaine | 2025-10-01 | Template plus example content for long-form PR descriptions | Sync with actual PR workflow when tooling changes |
| CHANGELOG.md | Active | Release Maintainer | 2025-09-01 | Semantic-release friendly history | Update only via release workflow |
| CLAUDE.md | Active | Toolsmiths | 2025-11-01 | Claude-specific usage instructions | Verify when Claude CLI behavior changes |
| docker/README.md | Active | Ops | 2025-11-12 | Docker build/run instructions tailored to the fork | Mirrors helper scripts under `docker/scripts/` |
| patch/README.md | Active | Ops | 2025-11-12 | Explains cross-platform patch scripts | Ensure fixes stay scoped to the fork |
| docs/index.md | Active | Docs | 2025-11-12 | Landing page for documentation tree | Must reference files that actually exist |
| docs/documentation-register.md | Active | Docs | 2025-11-12 | This register | Update whenever docs change and cross-check with `docs/documentation-review-framework.md` |
| docs/documentation-review-framework.md | Draft | Docs | 2025-11-12 | Governance process for audits and scoring | Linked from index/register; finalize after first review cycle |
| docs/implementation-plan.md | Active | Delivery | 2025-11-12 | Phase-by-phase execution plan for current goals | Align with LangGraph refactor planning |
| docs/langgraph_architecture.md | Active | Delivery | 2025-11-12 | High-level architecture for LangGraph agents | Cross-link with implementation plan |
| docs/langgraph_refactor_plan.md | Active | Delivery | 2025-11-12 | Big-bang migration plan + research findings | Requires validation before execution |
| docs/CLI_INTEGRATION.md | Active | Delivery | 2025-11-12 | MCP CLI integration research (chrishayuk/mcp-cli, etc.) | Verify referenced versions before install |
| docs/ASYNC_ARCHITECTURE.md | Active | Delivery | 2025-11-12 | Async execution patterns and examples | Keep in sync with actual async implementation |
| docs/OBSERVABILITY.md | Active | Delivery | 2025-11-12 | Observability + tracing guidance | Update when telemetry tooling changes |
| docs/MEMORY_ARCHITECTURE.md | Active | Delivery | 2025-11-12 | Redis-based LangGraph memory decisions | Confirm Redis version requirements during implementation |
| docs/CONSOLIDATION_SUMMARY.txt | Active | Delivery | 2025-11-12 | Executive summary for tool consolidation | Pair with `docs/TOOL_CONSOLIDATION_ANALYSIS.md` |
| docs/TOOL_CONSOLIDATION_ANALYSIS.md | Active | Delivery | 2025-11-12 | Detailed per-tool consolidation findings | Update when tool inventory changes |
| docs/custom_models.md | Active | Delivery | 2025-11-12 | Notes on custom model registration | Keep aligned with `conf/custom_models.json` |
| docs/refactor/CLIInstructions.md | Active | Delivery | 2025-09-15 | CLI usage dumps for headless tools | Regenerate when CLI flags change |
| docs/research/CLI_Substitution.md | Draft | Research | 2025-09-15 | Research notes on CLI substitution strategy | Migrate findings into primary docs when stabilized |
| docs/tools/*.md | Legacy Active | Toolsmiths | 2025-08-01 | Per-tool prompts and usage guides | Mark obsolete files individually once LangGraph consolidation ships |
| docs/0914_refactor.md | Archive Reference | Delivery | 2024-09-14 | Earlier refactor notes | Keep for historical context only |
| docs/plans/2025-11-12-documentation-review-framework.md | Active | Docs | 2025-11-12 | Implementation plan for this effort | Update when scope changes or after execution |
| staged_refactor_prompt_and_plan.md | Archive Reference | Delivery | 2025-07-01 | Prior staged refactor prompt/plan | Superseded by current LangGraph plans |
| old_readme_backup.md | Archive Reference | Docs | 2025-05-01 | Snapshot of upstream README | Do not edit—used for historical comparison |

## Archive Collection

The following entries are historical and kept under `docs/Archive/`. They require validation before reuse.

| Path | Owner | Last Reviewed | Notes |
|------|-------|---------------|-------|
| docs/Archive/adding_providers.md | Docs | 2024-05-01 | Legacy guidance predating fork |
| docs/Archive/adding_tools.md | Docs | 2024-05-01 | Outdated tool authoring steps |
| docs/Archive/advanced-usage.md | Docs | 2024-05-01 | Advanced scenarios for upstream server |
| docs/Archive/ai-collaboration.md | Docs | 2024-05-01 | Collaboration workflows tied to upstream |
| docs/Archive/ai_banter.md | Docs | 2024-05-01 | Experimental content |
| docs/Archive/configuration.md | Docs | 2024-05-01 | Replaced by fork-specific env guidance |
| docs/Archive/context-revival.md | Docs | 2024-05-01 | Legacy memory guidance |
| docs/Archive/contributions.md | Docs | 2024-05-01 | Upstream contribution process |
| docs/Archive/docker-deployment.md | Ops | 2024-05-01 | Superseded by `docker/README.md` |
| docs/Archive/gemini-setup.md | Ops | 2024-05-01 | Outdated provider setup |
| docs/Archive/getting-started.md | Docs | 2024-05-01 | Replaced by README quick start |
| docs/Archive/locale-configuration.md | Docs | 2024-05-01 | Locale info tied to upstream |
| docs/Archive/logging.md | Docs | 2024-05-01 | Logging guidance pre-refactor |
| docs/Archive/testing.md | Docs | 2024-05-01 | Obsolete testing instructions |
| docs/Archive/troubleshooting.md | Docs | 2024-05-01 | Upstream troubleshooting |
| docs/Archive/vcr-testing.md | Docs | 2024-05-01 | Old cassette workflow |
| docs/Archive/wsl-setup.md | Docs | 2024-05-01 | Windows Subsystem for Linux guidance |

## Generated Artifacts & Logs

| Path | Status | Notes |
|------|--------|-------|
| consensus_outputs/*.md | Reference | Auto-generated consensus transcripts; keep for auditing but exclude from manual reviews |
| requirements*.txt | Reference | Dependency manifests—update via tooling, not manual edits |

Use this table as the single source of truth for documentation ownership. When adding a new document, immediately create an entry with Owner + Status, and update the “Last Reviewed” date after each audit cycle.
