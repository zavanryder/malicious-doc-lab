# Code Review — 2026-03-30

Comprehensive review of the malicious-doc-lab codebase across all modules:
attacks (14), generators (10), evaluate, report, CLI, adapters, demo app,
coverage, and tests (144).

## Issues Found and Fixed

### 1. xlsx generator: IndexError on empty obfuscated_variants list

**File:** `src/maldoc/generate/xlsx.py:44-45`

`hints.get("obfuscated_variants")` could return a truthy empty list, then
`hints["obfuscated_variants"][0]` would raise IndexError. The code-simplifier
subsequently simplified the guard to rely on truthy check (non-empty list).

**Fix:** Simplified to `hints.get("obfuscated_variants")` which is falsy for
both None and empty list.

---

### 2. Markdown report: _avg_score division by zero

**File:** `src/maldoc/report/markdown_report.py:242-247`

If any EvaluationResult had an empty `scores` dict, `sum(r.scores.values()) / len(r.scores)`
would divide by zero, crashing report generation.

**Fix:** Skip results with empty scores in the average calculation.

---

### 3. Markdown report: pipe characters break table formatting

**File:** `src/maldoc/report/markdown_report.py:268`

Score justification text containing pipe characters (`|`) corrupts the
markdown table. No escaping was applied.

**Fix:** Escape `|` as `\|` in justification text before embedding in table rows.

---

### 4. Documentation: stale attack/format/test counts

**Files:** `CLAUDE.md`, `AGENT.md`, `README.md`

After codex added 4 new attacks and 4 new formats, documentation across
multiple files still referenced old counts (10 attacks, 6 formats, 117 tests).

**Fix:** Updated all files:
- CLAUDE.md: 14 attacks, 10 format generators, 144 tests, expanded attack list
- AGENT.md: 14 attacks, 10 formats, 144 tests, expanded attack list, updated overview
- README.md: 144 tests in project structure

---

### 5. Code simplification: runner.py scoring loop

**File:** `src/maldoc/evaluate/runner.py:321-333`

Four repetitive scorer calls and two parallel dict constructions replaced
with a single loop over a `stage_scorers` mapping.

---

### 6. Code simplification: CLI _get_adapter and demo command

**File:** `src/maldoc/cli.py`

Removed unnecessary `elif`/`else` after early returns in `_get_adapter`.
Restructured `demo` command with early return for reset case.

---

### 7. CLI run command: unsupported pairs crash batch

**File:** `src/maldoc/cli.py:193-194`

When running all attacks x all formats, unsupported pairs raised
`typer.BadParameter` which aborted the entire batch run. Users running
`--attack "attack1,attack2" --format "fmt1,fmt2"` expected unsupported
combos to be skipped, not crash the process.

**Fix:** Changed to `continue` with a "Skipped:" message instead of raising.

---

### 8. Code simplification: report helper functions

**File:** `src/maldoc/report/markdown_report.py:225-239`

Removed unnecessary `elif` after `return` in `_score_label` and `_overall_verdict`.

---

## Issues Reviewed and Kept As-Is

### Coverage matrix: text-only attacks listing IMAGE_FORMATS as degraded

Attacks like chunk_split, retrieval_poison, summary_steer, etc. list
IMAGE_FORMATS as "degraded". This is intentional: the image generator can
render any visible_content as text-on-image, providing a degraded simulation.
The coverage matrix correctly flags this as degraded, not supported.

### Generator technique completeness for new formats

New generators (txt, xlsx, pptx, eml) don't handle every attack technique
with special rendering. This is acceptable: attacks that aren't specially
handled still render their visible_content through the default path. The
coverage matrix's "degraded" classification covers these cases.

### Scoring formula: min(1.0, n/total) in score_chunking

The `min()` wrapper is technically unnecessary since `n/total <= 1.0` by
definition. Keeping it is harmless and provides defensive capping.

### _build_match_terms deduplication stores lowercase

The dedup logic stores lowercased terms, which is correct since all
matching is case-insensitive throughout runner.py.

### Demo pipeline: intentionally vulnerable parsing

The demo app's XLSX, PPTX, and EML parsers iterate all cells/shapes/headers
including hidden content. This is intentional — the demo app is deliberately
vulnerable to test whether attacks survive the full pipeline.

### New attacks: metadata field omitted

The 4 new attacks (encoding_obfuscation, typoglycemia, markdown_exfil,
visual_scaling_injection) don't set the `metadata` field in AttackResult.
This is correct: `metadata` is optional (`dict | None = None` in base.py)
and these attacks don't use the metadata injection vector.

## Previous Reviews

Issues from CODE_REVIEW_1_FIXED.md (9 findings) and CODE_REVIEW_2_FIXED.md
(6 findings) were previously addressed and remain fixed. Key fixes include:
- Decoupled chunk/retrieval detection from extraction fragments
- Added --payload to evaluate command
- Added runner + CLI tests (test_evaluate_runner.py)
- Restricted report --format to Literal["json", "markdown"]
- Added adapter close() lifecycle
- Removed generic keyword false positives
- Excluded refusal from payload influence scoring
- Updated all documentation for consolidated reporting
