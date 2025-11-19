# Documentation Index

This index summarizes the active documentation for Coldaine’s augmented fork of Zen MCP Server. Use it with the documentation register to keep track of ownership and review status.

## Active Documentation

- **Documentation Register (`docs/documentation-register.md`)** – Inventory of every doc, owner, and last-reviewed date. Update this first when adding or retiring docs.
- **Review Framework (`docs/documentation-review-framework.md`)** – Governance process for monthly audits, scoring criteria, and remediation rules.
- **Repository Overview (`README.md`)** – Fork goals, quick start, and setup; pair with `AGENTS.md` for contributor guidelines.
- **Implementation Planning**:
  - `docs/MIGRATION_MASTER_PLAN.md` – **Single Source of Truth** for the LangGraph migration.
  - `docs/langgraph_architecture.md` – Target architecture for LangGraph agents.
  - `docs/langgraph_refactor_plan.md` – Detailed research and milestones.
- **Execution Enablers**:
  - `docs/CLI_INTEGRATION.md` – MCP CLI integration research (chrishayuk/mcp-cli, cli-mcp, etc.).
  - `docs/ASYNC_ARCHITECTURE.md` – Async execution strategies.
  - `docs/MEMORY_ARCHITECTURE.md` – Redis-based state management decisions.
  - `docs/OBSERVABILITY.md` – Tracing and monitoring approaches.
  - `docs/CONSOLIDATION_SUMMARY.txt` / `docs/TOOL_CONSOLIDATION_ANALYSIS.md` – Tool reduction findings.
- **Custom Model Guidance (`docs/custom_models.md`)** – How to manage `conf/custom_models.json`.
- **CLI Reference (`docs/refactor/CLIInstructions.md`)** – Captured `--help` output for headless CLI providers.
- **Tool Guides (`docs/tools/*.md`)** – Legacy individual tool prompts and behaviors; keep until LangGraph consolidation lands.

## Archive (Historical References)

All legacy files live in `docs/Archive/` (adding_providers.md, configuration.md, docker-deployment.md, etc.). They originate from the upstream project and should not be followed without re-validation. When in doubt, prefer the active documents above and migrate any still-relevant material into the current structure.
