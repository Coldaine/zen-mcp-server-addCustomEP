# Documentation Registry & Review Framework Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Catalog every document in the repository, publish its status, and document the governance workflow so future reviews stay consistent.

**Architecture:** Introduce a single Markdown registry that lists all docs with status/owner metadata, update `docs/index.md` to route readers to the registry plus current active files, and add a governance guide describing cadence and validation criteria.

**Tech Stack:** Markdown, `rg`, `find`, standard POSIX shell.

---

### Task 1: Capture Documentation Registry

**Files:**
- Create: `docs/documentation-register.md`

**Step 1: Inventory docs**

Run: `find docs -type f | sort > /tmp/doc_inventory.txt`

Expected: `/tmp/doc_inventory.txt` lists every doc path for reference.

**Step 2: Draft registry table**

Use this starter template:

```markdown
| Path | Status | Owner | Last Reviewed | Purpose | Notes |
|------|--------|-------|---------------|---------|-------|
| README.md | Active | Coldaine | 2025-11-12 | Fork overview | Replace upstream positioning |
```

Include root docs (README.md, AGENTS.md, PR_SUMMARY.md) plus everything under `docs/` (group archive entries as “Archive” status). Set Owner to the maintainer responsible (default “Coldaine”), and mark Last Reviewed as the current date for entries you verified.

**Step 3: Save file**

Populate the table and save as `docs/documentation-register.md`.

**Step 4: Spot-check references**

Verify a random sample (at least 3 entries) by opening the referenced files to confirm they exist. Example command: `sed -n '1,40p' docs/langgraph_architecture.md`.

---

### Task 2: Update Documentation Index

**Files:**
- Modify: `docs/index.md`

**Step 1: Replace stale entries**

Remove references to non-existent files (`getting-started.md`, `configuration.md`, etc.). Replace with links that actually exist (e.g., `README.md`, `docs/custom_models.md`, `docs/langgraph_architecture.md`).

**Step 2: Add registry link**

At the top of the Active Documentation section, add a bullet pointing to `docs/documentation-register.md` so contributors know where to find status metadata.

**Step 3: Call out archive policy**

In the Archive section, add a sentence that all files under `docs/Archive/` are historical and should not be used without re-validation.

**Step 4: Proofread**

Ensure Markdown renders cleanly (no duplicate bullet headings) and that every listed file actually exists.

---

### Task 3: Publish Review Framework

**Files:**
- Create: `docs/documentation-review-framework.md`

**Step 1: Outline sections**

Structure the document with headings for Overview, Registry Usage, Validation Criteria (Freshness, Alignment, Actionability, Dependency Accuracy), Review Cadence, and Execution Workflow.

**Step 2: Describe cadence**

Document a monthly review cycle with theme-based assignments, referencing the registry for owner mapping. Include instructions to log outcomes in the registry.

**Step 3: Detail checklist**

Add a bullet list or table with the four scoring criteria (1–3 scale) and remediation rule (“Any 1 requires an issue”). Provide sample commands (e.g., `rg -n "LangGraph"`).

**Step 4: Save and cross-link**

Finalize the Markdown file and link it back from both `docs/index.md` and the new registry (Notes column) so it’s discoverable.

---

### Task 4: Verification & Commit Prep

**Files:**
- Modify: `docs/documentation-register.md`
- Modify: `docs/index.md`
- Create: `docs/documentation-review-framework.md`

**Step 1: Lint Markdown (optional)**

If `markdownlint` is available: `markdownlint docs/documentation-register.md docs/documentation-review-framework.md`.

**Step 2: Git status**

Run: `git status -sb` to confirm only the expected files changed.

**Step 3: Review diff**

Run: `git diff docs/documentation-register.md docs/index.md docs/documentation-review-framework.md`.

**Step 4: Tests (not applicable)**

Document in summary that no automated tests were run because changes are documentation-only.

**Step 5: Commit**

```bash
git add docs/documentation-register.md docs/index.md docs/documentation-review-framework.md
git commit -m "docs: add registry and review framework"
```
