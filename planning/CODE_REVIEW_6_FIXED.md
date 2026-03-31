# Code Review - malicious-doc-lab

Date: 2026-03-30
Reviewer: Codex (GPT-5)
Scope: Current working tree review across `src/maldoc`, `demo`, `demo-chatbot`, and `tests`

## Review Process

- Read the main execution paths in `src/maldoc` (`cli`, adapters, evaluation, reporting, generators, attacks, coverage).
- Read both demo applications and their ingestion pipelines.
- Read current tests to separate covered behavior from uncovered risk.
- Ran the current test suite: `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q` -> **174 passed**.
- Excluded intentionally vulnerable prompt-injection behavior from findings unless it breaks evaluation fidelity or benchmark correctness.

## Findings (Ordered by Severity)

### 1) High - Several fallback generators inject the raw payload and invalidate attack fidelity

**Where**
- `src/maldoc/generate/csv_gen.py:23-24`
- `src/maldoc/generate/xlsx.py:45-48`
- `src/maldoc/generate/pptx_gen.py:37-57`
- `src/maldoc/generate/html.py:64-76` (`generate_markdown`)

**Issue**
- These generators fall back to embedding `attack_result.hidden_content` directly even when the attack is supposed to survive only via an obfuscated, split, or format-specific variant.
- That means attacks such as `encoding_obfuscation`, `typoglycemia`, and `chunk_split` can end up containing the literal payload in the output document even when the attack logic intentionally transformed it.

**Impact**
- Extraction and retrieval scores can be inflated by the fallback carrier rather than the intended attack.
- Cross-attack comparisons become misleading because some formats silently collapse into "raw hidden text".

**Suggestions**
- Only inject the literal payload for techniques whose semantics explicitly require it.
- For transformed attacks, emit only the transformed representation or mark the format as degraded/unsupported in `coverage.py`.
- Add regression tests that generated `csv`, `xlsx`, `pptx`, and `md` artifacts do not contain the literal payload for attacks that should remain transformed.

---

### 2) High - Demo-Chatbot black-box mode disables reset, so sequential evaluations contaminate each other

**Where**
- `demo-chatbot/app.py:110-132`
- `src/maldoc/adapters/chatbot.py:69-76`

**Issue**
- `demo-chatbot` only registers `/reset` inside the `if not BLACK_BOX:` block.
- `ChatbotAdapter.reset()` treats a 404 as benign and returns.
- In black-box mode, every evaluation therefore runs without clearing conversation history or the Chroma collection.

**Impact**
- Later payloads can be retrieved from earlier uploads.
- Batch results in black-box mode are not isolated, so reported retrieval/response influence can reflect state leakage rather than the current document.

**Suggestions**
- Keep `/reset` available in both modes and hide only evidence endpoints.
- If the route must stay hidden, perform an equivalent state reset at upload time for adapter-driven evaluations.
- Add a test covering two back-to-back black-box evaluations to ensure the second run does not see the first document's state.

---

### 3) Medium - The generic HTTP target cannot be used against true black-box applications

**Where**
- `src/maldoc/adapters/http.py:74-86`
- `src/maldoc/evaluate/runner.py:290-305`

**Issue**
- The evaluator always calls `reset()`, `get_extracted_text()`, and `get_chunks()`.
- `HttpAdapter` treats missing `/reset`, `/extracted`, and `/chunks` endpoints as fatal instead of degrading into black-box scoring the way `ChatbotAdapter` does.

**Impact**
- `--target http` only works for white-box targets that expose the full demo-style evidence surface.
- A custom target with only upload/query endpoints cannot be evaluated even though the reporting model already supports `N/A` extraction/chunk scores.

**Suggestions**
- Add explicit black-box handling to `HttpAdapter`, or make evidence/reset endpoints optional in `BaseAdapter`.
- Move black-box detection into evaluator logic instead of relying on adapter-specific private state.
- Add CLI and adapter tests for an HTTP target that lacks evidence endpoints.

---

### 4) Medium - Both FastAPI apps use `async` endpoints for blocking parsing, embedding, and model calls

**Where**
- `demo/app.py:17-48`
- `demo-chatbot/app.py:35-95`
- `demo/pipeline.py:225-257`
- `demo-chatbot/pipeline.py:222-254`

**Issue**
- The request handlers are declared `async`, but they call synchronous file parsing, OCR, Chroma work, `ollama_client.embed(...)`, and `ollama_client.chat(...)` directly on the event loop thread.

**Impact**
- A single slow upload or model call can block unrelated requests.
- Under concurrent use, the demos can exhibit head-of-line blocking, timeouts, and misleading performance behavior unrelated to the attack itself.

**Suggestions**
- Make these endpoints plain `def` handlers, or offload blocking work with FastAPI/Starlette threadpool helpers.
- Keep the sync/async boundary consistent so request concurrency matches actual execution behavior.
- Add a small concurrency regression test or load probe for overlapping uploads and queries.

---

### 5) Low - Consolidated reports do not record skipped combinations or execution mode

**Where**
- `src/maldoc/cli.py:236-239`
- `src/maldoc/evaluate/evidence.py:56-62`
- `src/maldoc/report/markdown_report.py:368-376`

**Issue**
- Unsupported combinations are printed as "Skipped" during `maldoc run`, but they are not retained in the report model.
- Reports also do not explicitly record whether the run was white-box or black-box; that has to be inferred from `N/A` scores.

**Impact**
- A report does not fully describe the requested matrix, only the executed subset.
- Comparing runs becomes harder because readers cannot tell from report metadata alone whether omissions came from unsupported pairs or from a black-box configuration.

**Suggestions**
- Extend `ConsolidatedReport` with requested attacks/formats, skipped combinations, and execution mode metadata.
- Surface those fields in both JSON and Markdown reports.
- Add report tests for mixed supported/unsupported matrices and black-box runs.

## Test Coverage Gaps Worth Adding

- Generator fidelity tests that assert transformed attacks do not leak the literal payload through fallback generators.
- A black-box demo-chatbot isolation test covering multiple uploads in one process lifetime.
- HTTP adapter tests for missing `/reset`, `/extracted`, and `/chunks` endpoints.
- Concurrency or threadpool regression coverage for the demo services.
- Report tests that verify skipped combinations and run mode are preserved once modeled.

## Overall

The project is in better shape than the previous pass and the current suite is still fast and healthy. The biggest remaining risks are benchmark-fidelity issues: some generators flatten attack semantics, black-box chatbot runs are not isolated, and the generic HTTP path still assumes a white-box target surface.
