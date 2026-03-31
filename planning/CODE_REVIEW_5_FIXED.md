# Code Review - malicious-doc-lab

Date: 2026-03-30
Reviewer: Codex (GPT-5)
Scope: Full repository review (`src/maldoc`, `demo`, `demo-chatbot`, `tests`, project config)

## Review Process

- Read all source modules in `src/maldoc` (attacks, generators, adapters, evaluate, report, CLI).
- Read both demo services and frontend UI code.
- Read full pytest suite to identify behavioral coverage and gaps.
- Ran test suite: `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q` -> **166 passed**.
- Ran targeted runtime probes for suspicious paths (including XLSX parsing behavior and target labeling behavior).

## Findings (Ordered by Severity)

### 1) High - `off_page` XLSX generation creates pathological parse time in both demo pipelines

**Where**
- `src/maldoc/generate/xlsx.py:43`
- `demo/pipeline.py:112-118`
- `demo-chatbot/pipeline.py:110-116`

**Issue**
- `off_page` stores hidden content in cell `(row=1048576, col=16384)` (last possible Excel cell).
- Both pipelines iterate rows with `sheet.iter_rows(values_only=True)` across worksheet bounds.
- This drives extremely slow iteration for sparse sheets with huge max bounds.

**Impact**
- Major performance degradation / potential DoS for `off_page+xlsx` and similarly crafted uploads.
- Evaluation runs can stall disproportionately on this format/technique pair.

**Evidence**
- Reproduced locally with current code: loading is fast, but row iteration crossed 10s almost immediately while finding only a few non-empty rows.

**Suggestions**
- Avoid writing to the absolute max row/column for off-page simulation.
- In parsers, iterate only meaningful ranges or stop after configurable sparse-run thresholds.
- Add runtime guardrails for worksheet traversal cost.

---

### 2) High - HTTP target defaults can silently hit the wrong backend and emit malformed target labels

**Where**
- `src/maldoc/cli.py:23-31` (`_resolve_target_url`)
- `src/maldoc/cli.py:63-67` (`_target_label`)
- `src/maldoc/cli.py:139`, `src/maldoc/cli.py:253` (report target assignment)

**Issue**
- For `--target http` with no `--target-url`, `_resolve_target_url()` silently defaults to `http://localhost:8000`.
- `_target_label()` is computed from raw `target_url` (empty string), producing `""`.
- Report filenames then contain a blank target segment (e.g., double underscore target slot).

**Impact**
- Users can accidentally evaluate against the demo API while believing they are using a custom HTTP target.
- Reports become harder to trace because target labeling is broken.

**Suggestions**
- Require explicit `--target-url` when `--target http`.
- Or at minimum compute target label from resolved URL, not raw argument.
- Add CLI validation and tests for this branch.

---

### 3) High - Typoglycemia phrase matching is order/proximity agnostic and produces false positives

**Where**
- `src/maldoc/evaluate/runner.py:88-102` (`_contains_typoglycemia_phrase`)
- Used by extraction and retrieval matching at `src/maldoc/evaluate/runner.py:131-133`, `src/maldoc/evaluate/runner.py:200`

**Issue**
- Phrase detection effectively behaves like bag-of-words presence with optional typoglycemia matching.
- It does not enforce phrase order or locality.
- Unrelated text containing the same words can be scored as payload survival/influence.

**Impact**
- Inflated extraction/retrieval success metrics (false positives).
- Can overstate vulnerability and bias attack comparisons.

**Evidence**
- Local probe with scattered words (`ignore`, `all`, `previous`, `instructions`) returned `True` for phrase match despite no contiguous payload phrase.

**Suggestions**
- Require ordered token matching within a sliding window.
- Keep typoglycemia support but constrain by adjacency/proximity.
- Add regression tests for scattered-word false positive cases.

---

### 4) Medium - `ChatbotAdapter` black-box flag is sticky across evaluations

**Where**
- `src/maldoc/adapters/chatbot.py:16`, `:52-53`, `:63-64`
- Consumed in scoring logic at `src/maldoc/evaluate/runner.py:322-335`

**Issue**
- `_evidence_unavailable` is set to `True` on 404 from `/extracted` or `/chunks`.
- It is never reset to `False` on subsequent successful evidence calls.

**Impact**
- Once tripped (including transient outages), extraction/chunk scores can remain `N/A` for later evaluations on the same adapter instance.
- Batch run correctness can degrade silently.

**Suggestions**
- Reset the flag to `False` when evidence endpoints succeed.
- Consider per-evaluation local black-box state rather than adapter-global sticky state.
- Add tests covering transition from 404 -> 200.

---

### 5) Medium - Demo-Chatbot conversation history is unbounded and globally shared

**Where**
- `demo-chatbot/app.py:16` (global list)
- `demo-chatbot/app.py:48`, `:78` (append each turn)
- `demo-chatbot/app.py:96` (`/history` exposes entire history)

**Issue**
- History grows without cap and is shared across all clients.
- Prompting uses only last 20 messages, but stored history retains everything indefinitely.

**Impact**
- Unbounded memory growth over long uptime.
- Cross-user data leakage in multi-client use.

**Notes**
- Shared-state vulnerability is partly intentional for demo realism, but unbounded growth is still an operational stability issue.

**Suggestions**
- Cap stored history length and/or TTL even if shared-session behavior is retained.
- Limit `/history` exposure or return bounded recent history only.

---

### 6) Low - Demo and Demo-Chatbot pipelines are duplicated, increasing regression risk

**Where**
- `demo/pipeline.py`
- `demo-chatbot/pipeline.py`

**Issue**
- Parsing/chunking/embedding logic is duplicated almost verbatim.
- Every fix requires synchronized edits in two modules.

**Impact**
- Higher chance of drift and inconsistent behavior between targets.
- Slower and riskier maintenance.

**Suggestions**
- Extract shared pipeline logic into a common module imported by both apps.
- Keep only app-specific endpoint behavior separate.

---

### 7) Low - Retry loop in `run` catches broad `Exception`

**Where**
- `src/maldoc/cli.py:232-242`

**Issue**
- Retries trigger for all exceptions, including deterministic programming/configuration errors.

**Impact**
- Adds delay and can obscure root causes in batch runs.

**Suggestions**
- Retry only transient classes (network/HTTP timeout/service unavailable).
- Fail fast on deterministic validation/logic errors.

## Test Coverage Gaps Worth Adding

- CLI test for `--target http` without `--target-url` (should fail fast or label correctly).
- Adapter lifecycle test for `_evidence_unavailable` reset behavior after successful calls.
- Evaluator regression tests for phrase-order/proximity false positive prevention.
- Performance-focused unit/integration guard for large sparse XLSX parsing.
- Demo-Chatbot history growth/capping behavior tests.

## Overall

Core architecture is clear and testable, and the existing suite is extensive and fast. The main risks now are correctness inflation in evaluator matching and operational/performance edge cases (notably XLSX off-page handling and target resolution semantics).
