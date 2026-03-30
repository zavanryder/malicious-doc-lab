# Code Review - malicious-doc-lab

Date: 2026-03-29
Reviewer: Cursor AI agent
Scope: `src/maldoc/`, `demo/`, tests, project config/docs consistency

## Method

- Read all Python source files in `src/maldoc/`, `demo/`, and `tests/`
- Validated runtime behavior with:
  - `uv run pytest` (99 passed)
  - Targeted runtime checks for evaluation and CLI edge cases
- Focused review on correctness, reliability, regression risk, and test coverage

## Findings (ordered by severity)

### 1) High - Retrieval/chunk scoring can be forced to false-negative

**Where**
- `src/maldoc/evaluate/runner.py` (`evaluate`, `_find_payload_fragments`)

**Issue**
- Chunk and retrieval detection are both keyed off `payload_fragments` derived from extracted text.
- If extraction fails to produce fragments (or parser normalization changes text), chunk and retrieval checks always fail even when payload is actually present in chunks/retrieval context.

**Impact**
- Under-reports successful attacks with `chunk_survival=0` and `retrieval_influence=0`.
- Can mark a vulnerable pipeline as resistant.

**Evidence**
- Reproduced with a minimal adapter where payload appears in chunks/retrieval but extraction has no payload fragments:
  - Result scores: `{'extraction_survival': 0.0, 'chunk_survival': 0.0, 'retrieval_influence': 0.0, 'response_influence': 0.0}`
  - `payload_found_in_retrieval` was `False` even though retrieved chunk contained payload text.

**Recommended fix direction**
- Decouple chunk/retrieval detection from extraction-derived fragments.
- Match against:
  - full payload,
  - payload token subsets,
  - and extraction fragments (when available) as a supplemental signal.

**Missing tests**
- Add tests for `evaluate()` where extraction misses payload but retrieval contains payload.

---

### 2) High - `evaluate` CLI cannot correctly evaluate custom payload documents

**Where**
- `src/maldoc/cli.py` (`evaluate` command)

**Issue**
- `evaluate` reconstructs payload from `atk.default_payload()` and has no `--payload` option.
- If a document was generated with `--payload` custom text, evaluation compares evidence against the wrong payload.

**Impact**
- False negatives in extraction/chunk/retrieval/response influence scoring.
- Report conclusions can be incorrect for a primary documented workflow (custom payload generation).

**Recommended fix direction**
- Add `--payload` to `evaluate` (or accept payload from input metadata/report source).
- If omitted, default to attack default payload for backward compatibility.

**Missing tests**
- CLI test: generate with custom payload + evaluate with matching payload should detect fragments.

---

### 3) High - Core evaluation pipeline is effectively untested

**Where**
- `tests/` (coverage gap)

**Issue**
- No tests for:
  - `src/maldoc/evaluate/runner.py`
  - CLI `evaluate` and CLI `run` behavior paths

**Impact**
- Critical scoring and orchestration regressions can pass CI undetected.
- Existing issues above were not caught by current suite.

**Evidence**
- `rg` in `tests/` finds no references to `evaluate.runner`, `_find_payload_fragments`, or `_detect_influence`.
- `tests/test_cli.py` covers `help`, `generate`, and `report`, but not `evaluate`/`run`.

**Recommended fix direction**
- Add unit tests for `evaluate()` with fake adapter fixtures.
- Add CLI tests for `evaluate`/`run` via dependency injection or mocked adapters.

---

### 4) Medium - `report --format` silently accepts invalid values

**Where**
- `src/maldoc/cli.py` (`report` command)

**Issue**
- Any format except literal `"json"` falls through to markdown generation.
- Invalid values (for example `yaml`) return exit code 0 and produce markdown.

**Impact**
- User intent is ignored without warning.
- Automation scripts can silently produce wrong output format.

**Evidence**
- Reproduced via `CliRunner` with `--format yaml`: command succeeded and wrote `.md`.

**Recommended fix direction**
- Restrict to explicit choices (`json`, `markdown`) and fail fast on invalid input.

**Missing tests**
- Add negative CLI test for invalid `--format`.

---

### 5) Medium - CLI report filename behavior conflicts with project docs

**Where**
- Code: `src/maldoc/report/json_report.py` (`report_filename`)
- Docs: `README.md`, `AGENT.md`, `CLAUDE.md`, `documents/walkthrough-demo.md`

**Issue**
- Code currently generates: `{timestamp}_{target}_{label}_report`.
- Docs repeatedly describe/report examples as: `{attack}_{format}_report`.

**Impact**
- Users following docs cannot find expected filenames.
- Tooling/scripts built from docs may break.

**Recommended fix direction**
- Either:
  - align code to documented naming, or
  - update docs/examples consistently to timestamped naming.

**Missing tests**
- Add assertions for documented naming contract (whichever contract is chosen).

---

### 6) Medium - `demo` CLI action handling has UX/reliability edge cases

**Where**
- `src/maldoc/cli.py` (`demo` command)

**Issue**
- `demo start/stop` shells out to `docker compose` in current working directory.
- Running `maldoc demo start` outside repo root likely fails to locate compose file.
- Unknown `action` only prints a message and exits success (no nonzero exit).

**Impact**
- Non-repo-root invocation is brittle.
- Invalid usage can pass CI/automation unexpectedly.

**Recommended fix direction**
- Run compose using explicit `-f` repo-root compose file.
- Convert `action` to typed choices (or raise `typer.BadParameter`).

**Missing tests**
- Add CLI tests for invalid `demo` action and path-independent compose invocation.

---

### 7) Medium - Adapter clients are never explicitly closed

**Where**
- `src/maldoc/adapters/demo.py`
- `src/maldoc/adapters/http.py`

**Issue**
- Both adapters create persistent `httpx.Client` instances without close lifecycle.

**Impact**
- Repeated long-running usage can accumulate open connections/resources.

**Recommended fix direction**
- Add `close()` / context-managed usage or one-shot request style.

**Missing tests**
- Add lifecycle tests ensuring client close path exists and can be called safely.

---

### 8) Low/Medium - `hidden_text` PDF path does not apply `font_size_zero_text` hint

**Where**
- `src/maldoc/generate/pdf.py`

**Issue**
- The code only applies `font_size_zero_text` when technique is not `hidden_text`.
- `HiddenTextAttack` declares `font_size_zero_text` hint but PDF generator suppresses it for that attack.

**Impact**
- Behavior is inconsistent across formats and with attack description wording.
- May reduce survival rate for `hidden_text` in PDF if zero-width extraction is weak.

**Recommended fix direction**
- Clarify intent and either:
  - apply tiny-font hidden text for `hidden_text` too, or
  - remove/rename hint to match intended behavior.

**Missing tests**
- Add PDF generator test asserting intended hidden-text embedding strategy for `hidden_text`.

---

### 9) Low - Documentation metadata is stale in multiple locations

**Where**
- `README.md`, `AGENT.md`, `CLAUDE.md`

**Issue**
- Multiple files state "95 tests", but current run is 99 tests.
- Report naming docs are also stale relative to implementation (covered above).

**Impact**
- Minor confusion and reduced trust in docs.

**Recommended fix direction**
- Update counts/examples as part of docs sync pass.

## Positive notes

- Project layout is clear and coherent across attacks/generators/adapters/evaluation/reporting.
- Unit tests are fast and deterministic (99 passing in ~2.5s).
- Attack registry and generator dispatch patterns are simple and maintainable.
- Report output includes strong evidence artifacts and stage justifications.

## Suggested implementation order (when approved)

1. Fix evaluation detection coupling (Finding 1)
2. Fix `evaluate` custom payload support (Finding 2)
3. Add runner + CLI evaluate/run tests (Finding 3)
4. Tighten CLI input validation for report/demo (Findings 4, 6)
5. Resolve naming/docs contract and doc drift (Findings 5, 9)
6. Address adapter lifecycle and hidden-text consistency (Findings 7, 8)
