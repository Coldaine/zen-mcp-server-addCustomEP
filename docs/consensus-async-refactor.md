# Consensus Tool – Minimal Async Refactor Design

Status: draft  
Last Updated: 2025-09-09  
Owner: consensus-refactor

## 1. Purpose / Scope
Introduce lightweight concurrency to the existing `consensus` tool so multiple model calls execute in parallel and a single aggregated response is returned once all (or all that can) complete.

Keep changes narrowly focused: no new persistence layer, no caching tier, no ACL system, no expanded retry taxonomy. Preserve existing external behavior (single MCP tool response, continuation support) while improving latency when multiple models are consulted.

## 2. Current Behavior (Summary)

- Sequential per‑model invocation inside consensus workflow.
- Each model’s stance prompt constructed, model called, response appended.
- Final synthesis produced after the last model finishes.
- Ordering implicitly equals the input order (because of sequential execution).
- Partial failures currently handled (failed model noted, rest proceed). (Based on existing provider & tool error handling patterns.)

## 3. Target Behavior

- Launch all model requests concurrently.
- Preserve deterministic ordering in final aggregated structure (original input order), regardless of completion order.
- Aggregate per‑model results (success or error) into a normalized list, then run the same synthesis logic (unchanged as much as possible) over collected successful responses.
- Return a single MCP response only after aggregation and synthesis complete.

## 4. Non‑Goals

- No new configuration flags.
- No persistence or recovery layer.
- No rate limiting rework.
- No cross‑request caching.
- No schema changes visible to MCP client (additive internal fields only if needed).
- No speculative abstraction of unrelated tools.

## 5. Data Contract (Internal Normalized Result)

Per‑model result (kept internal; exposed only if current tool already surfaces similar detail):

```json
{
  "model": "<string>",
  "stance": "for|against|neutral",
  "status": "success" | "error",
  "content": "<string>" | null,
  "error_message": "<string>" | null,
  "latency_ms": <int>
}
```

Aggregate logic:

- Overall status = `success` if at least one model succeeded; else `error`.
- Synthesis only uses `status == success` entries.
- Error entries may still be summarized in a short “skipped/failed models” note (existing style preserved).

## 6. Execution Flow (High Level)

```text
User → MCP tools/call(consensus)
  → Validate / normalize model list & stances
  → Build per-model prompt inputs
  → Create async tasks (one per model)
  → await asyncio.gather(..., return_exceptions=True)
  → Normalize results (ordered by original list)
  → Run existing synthesis over successful contents
  → Package single response (unchanged outer shape)
  → Return to MCP client
```

## 7. Minimal Helper Utility

Add a small internal helper (e.g., `utils/async_models.py` if not existing) or inline inside consensus tool:

```python
async def run_models_concurrently(model_specs, invoke_fn):
  # model_specs: list[ModelSpec] preserving order
  # invoke_fn: async (spec) -> ModelResult
  tasks = [asyncio.create_task(invoke_fn(spec)) for spec in model_specs]
  raw_results = await asyncio.gather(*tasks, return_exceptions=True)
  normalized = []
  for spec, result in zip(model_specs, raw_results):
    normalized.append(normalize_result(spec, result))
  return normalized
```

Keep this intentionally small—no class wrapper unless already consistent with repo style.

## 8. Error & Timeout Handling

- Reuse existing provider timeout mechanisms (do not add new knobs).
- If a task raises an exception: capture as `status=error`, record `error_message`, proceed.
- Do not retry beyond what provider already does.
- If all models fail: synthesis phase skipped; return an error-style consensus output consistent with current failure formatting (include per-model errors list if already done today; otherwise add a concise summary string).

## 9. Ordering & Determinism

- Maintain a `model_specs` list in the original user order; use its index for deterministic final ordering.
- Do not rely on dict iteration order from intermediate structures.
- When synthesizing, iterate through the ordered list of successful results only.

## 10. Logging (Additive & Minimal)

Use existing loggers (no new handlers):

- On dispatch: `DEBUG: consensus dispatch models=[m1,m2,...]`
- Per completion: `DEBUG: consensus model=<name> status=<success|error> latency=<ms>`
- Final aggregation: `DEBUG: consensus aggregation success=<n_success> error=<n_error>`

Avoid INFO level unless current implementation uses it for similar milestones.

## 11. Testing Adjustments

Add / modify tests (reuse simulator framework):

1. Parallel speed heuristic (optional): simulate two artificial slow models; ensure wall clock ~ max(single) not sum (allow generous threshold to avoid flakiness).
2. Mixed success/failure: one failing model should not abort synthesis.
3. All failure path returns aggregate error.
4. Deterministic ordering: feed models in a given order, ensure output ordering matches even if artificial delays invert completion order.

No load / stress harness needed for initial merge.

## 12. Migration Steps

1. Identify consensus tool implementation file and isolate sequential loop.
2. Extract loop body into `async def invoke_model(spec)`.
3. Replace loop with call to helper (`run_models_concurrently`).
4. Adapt synthesis to accept list of successful contents (unchanged signature if already list-based).
5. Add logging lines (DEBUG level).
6. Update / add simulator tests.
7. Verify no schema/output regressions via existing tests.

## 13. Rollback Plan

Change is localized; to rollback, replace concurrent block with previous sequential loop (keep old code in initial PR diff context for easy revert). No data migrations required.

## 14. Future (Explicitly Optional / Out of Scope Now)

- Per-model adaptive timeouts.
- Batch provider requests where provider supports multi-prompt endpoints.
- Cancellation of slow laggards after quorum (if ever needed).
- Structured weighting / voting scheme.
- Exposing per-model raw metadata in MCP response (only if future client consumes it).

## 15. Acceptance Criteria

- Parallel execution implemented; decreasing latency for >=2 models (observable in debug logs).
- All existing consensus tests pass unchanged (unless they assert sequencing side-effects).
- New tests for mixed success and ordering added and passing.
- No new required environment variables or configuration.
- Log noise unchanged at INFO level.

---
This document intentionally limits scope to reduce implementation risk while enabling meaningful latency improvement.
