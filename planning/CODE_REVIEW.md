# Code Review — 2026-03-30

Comprehensive review of the malicious-doc-lab codebase across all modules:
attacks, generators, evaluate, report, CLI, adapters, demo app, and tests.

## Issues Found and Fixed

### 1. Dead code: unused space key in hidden_text.py

**File:** `src/maldoc/attacks/hidden_text.py:19`

The `chars` dict maps `" "` to `ZERO_WIDTH_JOINER`, but the binary encoding
(`format(ord(char), "08b")`) only produces `"0"` and `"1"` characters.
The space key is never used.

**Fix:** Removed the dead entry.

---

### 2. Markdown report: triple-backtick injection in code blocks

**File:** `src/maldoc/report/markdown_report.py:232-246`

If a prompt or LLM response contains triple backticks, it breaks the
enclosing markdown code block. This corrupts the report formatting.

**Fix:** Escape triple backticks inside prompt/response content before
embedding in code blocks.

---

### 3. Report filename: colons not sanitized

**File:** `src/maldoc/report/json_report.py:14`

Target URLs containing colons (e.g., `example.com:8080`) produce filenames
with colons, which are invalid on some filesystems.

**Fix:** Also replace `:` in the target label.

---

### 4. Evaluate command hardcodes template to "memo"

**File:** `src/maldoc/cli.py:95`

The `evaluate` command always reconstructs the attack with template "memo",
even though the document may have been generated with a different template.
Added `--template` option to `evaluate`.

**Fix:** Added `--template` parameter to the evaluate command.

---

### 5. Markdown hidden content: only 2 of 10 techniques supported

**File:** `src/maldoc/generate/html.py:65`

The markdown generator only embeds hidden content for `white_on_white` and
`metadata` techniques. Other attacks that have hidden_content (off_page,
ocr_bait, delayed_trigger, tool_routing) silently produce no hidden content
in markdown format.

**Fix:** Embed hidden content as HTML comment for all techniques that have it.

---

### 6. Scoring inconsistency: score_extraction redundant guard

**File:** `src/maldoc/evaluate/scoring.py:13`

`payload_found_in_text` is always derived from `len(payload_fragments) > 0`
in runner.py, making the double-check redundant. Simplified to check only
`payload_fragments`.

**Fix:** Simplified the condition.

---

### 7. Empty payload false positive in fragment detection

**File:** `src/maldoc/evaluate/runner.py:39`

`_find_payload_fragments()` with an empty payload returned `['']` because
`"" in text` is always True in Python. This would cause false positive
extraction scores.

**Fix:** Added early return for empty/whitespace-only payloads.

---

### 8. Dead code: unused Payload class in payloads.py

**File:** `src/maldoc/generate/payloads.py` (entire file)

The `Payload` Pydantic model was never imported or used anywhere in the
codebase. It duplicated fields from `AttackResult` and served no purpose.

**Fix:** Deleted the file.

---

## Issues Reviewed and Kept As-Is

### HTML "XSS" in generated documents

The review flagged unescaped HTML in the HTML generator. However, the HTML
documents ARE the attack artifacts. They are intentionally adversarial.
Escaping them would defeat their purpose. No fix needed.

### Demo app missing error handling / running as root / no healthcheck

The demo app is intentionally vulnerable and minimal by design (see CLAUDE.md).
Adding hardening, error handling, or security best practices would undermine
its purpose as a test target. No fix needed.

### Chunk split single-word payload handling

The fallback `filler + payload` for single-word payloads is correct behavior.
A single word cannot be meaningfully split across chunks. The function
gracefully degrades to appending the payload to the filler text. Not a bug.

### Scoring formula differences between stages

Extraction and response use `n/3.0` (absolute threshold) while chunking uses
`n/total` (relative proportion). This is intentional: extraction and response
measure distinct signal types with a fixed rubric, while chunk survival is
inherently proportional. Consistent within each metric's semantics.

### Global state in demo pipeline.py

Intentional for the demo. The demo app is single-threaded uvicorn. Global
state is reset between evaluations via the /reset endpoint. Adding dependency
injection would over-engineer a deliberately simple target.

### Dependency separation between pyproject.toml and demo/requirements.txt

Intentional. The CLI tool (pyproject.toml) and the demo app
(demo/requirements.txt) are separate deployments. The demo runs in Docker
with its own dependencies. They share only python-docx and Pillow by
coincidence, not coupling.
