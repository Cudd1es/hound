# Resume/JD Semantic + Cache + Focus Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve resume parsing semantic quality, persist resume parse results to avoid repeat parsing, and focus JD extraction on responsibilities/requirements instead of whole-page noise.

**Architecture:** Keep existing extension->API flow. Add persistent resume cache in backend keyed by file hash. Expand LLM resume schema to include semantic summary fields in profile. Harden JD extraction in extension with section-focused text extraction and update helper tests. Preserve rule/LLM fallback behavior.

**Tech Stack:** FastAPI, Python stdlib hashing/json, Chrome MV3 extension JS, node:test, pytest.

---

### Task 1: Add failing tests for resume semantic fields and cache behavior

**Files:**
- Modify: `backend/tests/test_resume_parser_llm.py`
- Modify: `backend/tests/test_api_resume_parse.py`

**Step 1: Write failing semantic test**
- Extend fake resume provider payload to include semantic summary fields.
- Assert profile includes these new normalized fields.

**Step 2: Write failing cache test for `/resume/parse`**
- Use monkeypatch to wrap parse function and count calls.
- Call endpoint twice with same bytes and assert second call returns `cache_hit=true` and parse function called once.

**Step 3: Run tests (expect fail)**
- `PYTHONPATH=backend/src conda run -n hound pytest backend/tests/test_resume_parser_llm.py backend/tests/test_api_resume_parse.py -q`

### Task 2: Add failing tests for JD focused extraction helper

**Files:**
- Modify: `extension/tests/endpoint-builder.test.mjs`

**Step 1: Add helper tests**
- Add tests for text cleaner that drops `About the company/More jobs` sections.
- Add tests ensuring key sections (`Responsibilities`, `Qualifications`) are preserved.

**Step 2: Run JS tests (expect fail)**
- `cd extension && node --test tests/endpoint-builder.test.mjs`

### Task 3: Implement backend semantic resume profile and persistent cache

**Files:**
- Modify: `backend/src/hound_core/resume_parser.py`
- Modify: `backend/src/hound_core/llm_ollama.py`
- Modify: `backend/src/hound_core/api.py`

**Step 1: Resume semantic fields**
- Normalize/add fields: `semantic_summary`, `strengths`, `experience_signals`.
- Keep compatibility with `skills/experiences/source`.

**Step 2: Persistent resume cache**
- Implement file-hash based cache in API layer.
- Store/lookup cache path under logs (JSON file), include `cache_hit` in response.

**Step 3: Run targeted python tests**
- Re-run tests from Task 1.

### Task 4: Implement focused JD extraction in extension

**Files:**
- Modify: `extension/sidepanel_helpers.js`
- Modify: `extension/sidepanel.js`
- Modify: `extension/content.js`

**Step 1: Add reusable text focus helper in helpers**
- Build function to clean and focus on job sections.

**Step 2: Use helper in sidepanel fallback path**
- Keep existing selector flow; clean extracted text before filling textarea.

**Step 3: Update content script extraction**
- Apply same focused cleanup in content script response.

**Step 4: Run JS tests**
- `cd extension && node --test tests/endpoint-builder.test.mjs`

### Task 5: Verify all tests and update docs

**Files:**
- Modify: `docs/usage/backend-api.md`
- Modify: `docs/usage/extension.md`

**Step 1: Add notes**
- Explain resume cache behavior and semantic fields.
- Explain JD focus extraction behavior.

**Step 2: Full verification**
- `PYTHONPATH=backend/src conda run -n hound pytest backend/tests -q`
- `cd extension && node --test tests/endpoint-builder.test.mjs`
