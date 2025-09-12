# Follow-Up Issues: Local Model Migration & Consensus Concurrency

Tracking document for post-merge tasks. Create formal GitHub issues referencing these summaries.

## Issue 1: Vision Image Ingestion Fails
- Summary: Local vision models (llava, moondream, qwen2.5vl, llama3.2-vision) return generic text or ignore image inputs.
- Suspected Areas: Provider request payload (multipart vs base64), MIME type labeling, omission of `image_url` or `b64_json` field.
- Acceptance: Vision test passes with at least one model producing content referencing basic image features.
- Actions:
  1. Log raw outbound request body when `supports_images=True` and `ZEN_DEBUG_VISION=1`.
  2. Verify Ollama API expects `images: [<base64>]` vs nested objects.
  3. Add fallback conversion (resize, ensure RGB) before encode.
  4. Add sample manual reproduction script.

## Issue 2: Optional Legacy Multi-Step Consensus Mode
- Summary: Some downstream automation may assume iterative step progression.
- Acceptance: Flag `CONSENSUS_LEGACY_MODE=1` re-enables old multi-step path.
- Actions: Preserve previous loop structure guarded by env flag; add regression test.

## Issue 3: Streaming Partial Consensus Synthesis
- Summary: Provide incremental summaries while models still returning.
- Acceptance: Stream events `model_partial` and `aggregate_update` before final payload.
- Actions: Introduce async queue + SSE / callback integration point.

## Issue 4: Prune Large Model Library Snapshot
- Summary: `docs/_ModelLibrary.json` may bloat clone size.
- Acceptance: File either generated on demand or reduced < 100KB.
- Actions: Add script `scripts/generate_model_library.py`; exclude from git and add cache note.

## Issue 5: Mark Vision Tests xfail Until Fixed
- Summary: Prevent noisy CI failures.
- Acceptance: Vision test suite marked `xfail` with linked issue number.
- Actions: Apply `@pytest.mark.xfail(reason="See Issue 1", strict=False)`.

## Issue 6: Add README Local-Only Strategy Note
- Summary: Communicate removal of external defaults & how to re-enable.
- Acceptance: New section "Local Model Strategy" added with reactivation instructions.

## Issue 7: Release Tag After Vision Fix
- Summary: Prepare formal release once feature parity restored for vision.
- Acceptance: Tag `v5.12.1` (or `v5.13.0` if streaming added) and update CHANGELOG.

---
Create GitHub issues referencing these canonical fragments. Replace placeholder numbering with actual issue IDs once opened.
