# Documentation Review Framework

_Last updated: 2025-11-12_

## Overview

This framework keeps the augmented Zen MCP Server fork’s documentation accurate as architecture, tooling, and experiments evolve. Reviews focus on two things: (1) the **documentation register** as the inventory of truth, and (2) **scored audits** that confirm each file is still correct, actionable, and aligned with current goals.

## Registry Usage

1. Treat `docs/documentation-register.md` as the authoritative index. Every new document must add an entry (path, status, owner, last-reviewed date, purpose, notes).
2. When a review is completed, update the “Last Reviewed” column and summarize any changes or risks in the Notes field.
3. If a document is retired or superseded, move it to the Archive section of the register and cross-reference its replacement.

## Validation Criteria

Each document receives a score from 1 (critical gap) to 3 (meets expectations) on the following axes:

| Criterion | Description | Score 1 (Action Required) | Score 2 (Needs Follow-Up) | Score 3 (Healthy) |
|-----------|-------------|---------------------------|---------------------------|-------------------|
| Freshness | How recently the content was confirmed | Last update > 90 days or unknown | 60–90 days old, pending minor updates | ≤ 60 days or explicitly revalidated |
| Alignment | Consistency with the fork’s current goals | References deprecated architecture or upstream defaults | Minor mismatches (e.g., outdated env var) | Fully aligned with LangGraph + custom providers |
| Actionability | Can a contributor follow it end-to-end? | Missing steps, broken commands, unclear context | Steps exist but need clarification/examples | Step-by-step, includes commands and expected outcomes |
| Dependency Accuracy | External links, versions, and configs | Links broken or versions known to be wrong | Minor version drift without breaking changes | Verified versions and working links |

> Any criterion scored **1** triggers an issue or TODO entry before the review is closed.

## Review Cadence

- **Monthly Theme:** Rotate focus areas (Architecture, Tooling, Operations, Onboarding). Pick a theme during the first week of each month.
- **Assignment:** Use the registry’s Owner column to assign reviewers. If vacant, default to Coldaine.
- **Kickoff Checklist:**
  1. Export current registry (`cp docs/documentation-register.md /tmp/register-YYYYMM.md`).
  2. Identify documents matching the month’s theme and add them to the sprint board.
  3. Confirm applicable research sources (e.g., `docs/langgraph_refactor_plan.md` citations) are still valid.

## Execution Workflow

1. **Prepare Context**
   - Read the document top-to-bottom.
   - Run supporting commands (e.g., `rg -n "LangGraph" docs/langgraph_architecture.md`) to ensure references exist.
2. **Score Against Criteria**
   - Capture scores inline in the registry Notes field as `Freshness=3, Alignment=2, ...`.
   - Attach proof where helpful (commit hashes, command output snippets).
3. **Remediate**
   - For each score of 1, create an issue or TODO entry referencing the file path and deficiency.
   - For score 2 items, leave a concise action item in the Notes column (e.g., “Verify chrishayuk/mcp-cli version before next release”).
4. **Publish Summary**
   - Update `docs/documentation-register.md` with the new review date.
   - Add a short summary to the sprint notes or PR description indicating which docs were audited and any follow-up tickets filed.

## Tooling Tips

- `find docs -type f \( -name '*.md' -o -name '*.txt' \)` – regenerate the inventory when new files appear.
- `rg -n "TODO" docs -g '*.md'` – locate unfinished sections quickly.
- `gh issue create ...` – log remediation tasks (if GitHub CLI is available; otherwise track in your preferred system).

By following this framework, every contributor can trust that documentation mirrors the current state of the forked project, and updates happen on a predictable cadence.
