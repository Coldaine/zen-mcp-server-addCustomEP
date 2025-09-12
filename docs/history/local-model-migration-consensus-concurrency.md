# Merge Notes: Local Model Migration & Consensus Concurrency Refactor

Date: 2025-09-12
Merged Commit: 4b5cbab (main)
Scope: Model configuration overhaul, consensus tool concurrency redesign, environment hardening, expanded documentation & tests.

## Why This Was Merged Without a PR
This change set began as an internal cleanup (removing external model dependencies and sanitizing environment keys) and grew into a broader refactor of the consensus workflow. The branch was merged directly once stability was confirmed locally, but a formal PR record is desirable for auditability. This document serves as the authoritative post-merge rationale.

## Objectives
- Eliminate reliance on paid / external API models for default test and simulator flows.
- Introduce parallel (single-step) consensus model consultation to reduce latency.
- Improve environment security posture (no committed secrets, explicit verification script).
- Enrich observability (timing logs + markdown export of consensus results).
- Expand/align simulator test coverage with new behaviors.

## Key Changes
### Model & Capability Layer
- Replaced external aliases (`flash`, `pro`, `gemini-*`, `haiku`, `o3`) with local Ollama models: `qwen3:0.6b`, `qwen2.5vl:7b`, `llava:latest`, `llama3.2-vision:11b`, `moondream:latest`.
- Updated `conf/custom_models.json` to mark vision-capable models (`supports_images: true`).
- Added model library snapshot (`docs/_ModelLibrary.json`).

### Consensus Tool Refactor
- Single-step concurrent fan-out of all model consultations (replaces multi-step iterator pattern).
- Added aggregate timing log (`consensus concurrent_total_time_ms=...`).
- Normalized output structure with `consensus_workflow_complete` status.
- Introduced `utils/consensus_output.py` for markdown export of full and per-model responses.

### Environment & Security
- Sanitized `.env` (removed hard-coded API keys; rely on exported shell vars).
- Added `scripts/verify_env.py` to introspect provider configuration safely (masked output).

### Documentation
- Added async refactor rationale (`docs/consensus-async-refactor.md`).
- Added planning notes (`docs/plans/thinking-mode-implementation.md`).
- Added GLM usage tips and extended help overview.

### Testing
- Updated simulator tests to align with local-only models.
- Added comprehensive consensus workflow & conversation variants.
- Vision tests currently retained but failing under local models (see Open Issues).

### Tooling & Infra
- Added `uv.lock` for deterministic dependency resolution.
- Ensured formatting/lint compliance (Black, Ruff, isort).

## Breaking / Behavioral Changes
- External model aliases no longer resolvable by default.
- Consensus workflow condensed to a single step; previous multi-step expectations no longer valid.
- Response payload shape adjusted (immediate inclusion of all model responses in step 1).

## Known Issues / Follow-Up Items
| Area | Issue | Planned Action |
|------|-------|----------------|
| Vision models | Local Ollama vision models return generic / no-image responses | Investigate image encoding & provider request payload formatting |
| Legacy consensus | Some code paths assume multi-step progression | Add feature flag or compatibility wrapper if downstream tools require it |
| Model registry size | Large `docs/_ModelLibrary.json` may slow clones | Evaluate pruning or generating on demand |
| Test robustness | Vision tests produce false negatives locally | Mark xfail or param-skip until pipeline fixed |

## Migration Guidance
- Update any automation referencing removed model names to new local identifiers.
- Ensure Ollama (or compatible endpoint) is running with required models pulled.
- Export environment variables instead of populating `.env` with secrets.

## Verification Snapshot
- Lint/format checks: Passed.
- Consensus tests: Passing after refactor.
- Vision tests: Failing (expected, pending pipeline fix).
- Manual consensus run produced markdown outputs in `consensus_outputs/`.

## Suggested Next Steps
1. Open an issue: "Fix local vision image ingestion pipeline" (attach failing test output & sample payloads).
2. Add optional CLI flag to dump raw provider request for debugging vision.
3. Consider streaming partial consensus synthesis while models return.
4. Tag release after vision fix (e.g., `v0.5.0`).

## Retroactive PR Body (For GitHub Issue or Release Notes)
> This consolidation migrates the server to a fully local model strategy, introduces parallel consensus evaluation, hardens environment handling, and expands both documentation and test coverage. It prepares the codebase for offline-friendly, lower-latency operation while surfacing areas (notably vision) needing focused follow-up.

---
Maintainer Note: This file serves as the durable audit artifact for the direct merge commit. If a formal PR is later created (e.g., against a stabilization branch), reuse this content verbatim.
