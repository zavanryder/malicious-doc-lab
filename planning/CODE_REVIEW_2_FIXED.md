# Code Review - Second Pass

Date: 2026-03-29
Scope: `src/maldoc`, `demo`, tests, and documentation consistency

## Review method

- Re-reviewed core evaluation/scoring logic and CLI behavior
- Reviewed docs against current implementation and report naming
- Ran full test suite after fixes

## Findings and actions

### 1) High - Extraction false positives from generic keywords

**File:** `src/maldoc/evaluate/runner.py`

**Issue:** `_find_payload_fragments()` used hardcoded keyword fallback (`IGNORE`, `ACCESS GRANTED`, etc.), which could report payload survival even when those keywords were unrelated to the current payload.

**Fix applied:**
- Removed generic keyword fallback
- Detection now uses payload-derived phrases only
- Added `_payload_phrases()` helper to keep phrase extraction consistent

**Tests added/updated:**
- `tests/test_evaluate_runner.py::test_find_payload_fragments_ignores_non_payload_keywords`

---

### 2) High - Refusal responses counted as payload influence

**Files:** `src/maldoc/evaluate/runner.py`, `src/maldoc/evaluate/scoring.py`

**Issue:** `refusal_detected` could still mark `payload_influenced_response=True` and contribute to influence score.

**Fix applied:**
- `payload_influenced_response` now excludes `refusal_detected`-only outcomes
- `score_response()` now explicitly returns 0 for refusal-only indicators
- Only non-refusal indicators contribute to response influence score

**Tests added/updated:**
- `tests/test_evaluate_runner.py::test_evaluate_refusal_does_not_count_as_payload_influence`
- `tests/test_scoring.py::test_refusal_indicator_not_scored_as_influence`

---

### 3) Medium - Inconsistent phrase threshold/matching behavior

**File:** `src/maldoc/evaluate/runner.py`

**Issue:** Phrase parsing and matching thresholds were inconsistent across extraction and retrieval checks.

**Fix applied:**
- Unified phrase extraction through `_payload_phrases()`
- Improved `_contains_match_term()` to enforce word boundaries on single-token matches
- Reduced noisy fallback token matching to long unique-like tokens (numeric/underscored)

**Tests added/updated:**
- `tests/test_evaluate_runner.py::test_contains_match_term_respects_word_boundaries`

---

### 4) High - Broken programmatic report example in docs

**File:** `documents/walkthrough-real-targets.md`

**Issue:** Example passed `EvaluationResult` directly to report generators; generators require `ConsolidatedReport`.

**Fix applied:**
- Updated example to wrap result in `ConsolidatedReport`
- Added needed imports and corrected snippet flow

---

### 5) Medium - Documentation/report naming drift

**Files:** `README.md`, `AGENT.md`, `CLAUDE.md`, `documents/walkthrough-real-targets.md`

**Issue:** Some docs implied legacy naming or unclear `multiple` semantics.

**Fix applied:**
- Clarified filename pattern behavior
- Clarified that `multiple` appears only for consolidated runs with >1 attack
- Updated examples to timestamped naming style used by code

---

### 6) Low - Demo app import cleanup

**File:** `demo/app.py`

**Issue:** Redundant top-level imports for `last_chunks` and `last_extracted_text`.

**Fix applied:**
- Removed unused top-level imports; handlers keep direct module reads

## Documentation sync status

Updated and aligned:
- `README.md`
- `AGENT.md`
- `CLAUDE.md`
- `documents/walkthrough-real-targets.md`

## Validation

- `uv run pytest`
- Result: **117 passed**
