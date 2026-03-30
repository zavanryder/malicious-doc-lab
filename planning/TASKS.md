# Tasks — v0.1.0

Work is organized into phases. Each phase produces a working increment.

---

## Phase 1: Project scaffolding

- [ ] Initialize `pyproject.toml` with `uv`, package name `maldoc`
- [ ] Create `src/maldoc/__init__.py` with version
- [ ] Create CLI entrypoint with Typer (`src/maldoc/cli.py`)
- [ ] Verify `uv run maldoc --help` works
- [ ] Create empty subpackages: `generate`, `attacks`, `adapters`, `evaluate`, `report`

---

## Phase 2: Attack classes and document generation

### Attack classes (core four)
- [ ] `attacks/base.py` — BaseAttack ABC, AttackResult model
- [ ] `attacks/hidden_text.py` — zero-width chars, font-size-zero
- [ ] `attacks/white_on_white.py` — white text on white background
- [ ] `attacks/metadata.py` — metadata field injection
- [ ] `attacks/retrieval_poison.py` — high-relevance adversarial content

### Attack stubs
- [ ] Stub files for: `ocr_bait`, `off_page`, `chunk_split`, `summary_steer`, `delayed_trigger`, `tool_routing`

### Document generators
- [ ] `generate/payloads.py` — payload model (attack content + benign wrapper)
- [ ] `generate/templates.py` — benign document templates (memo, report, invoice)
- [ ] `generate/pdf.py` — PDF generation with fpdf2
- [ ] `generate/docx.py` — DOCX generation with python-docx
- [ ] `generate/html.py` — HTML and Markdown generation
- [ ] `generate/image.py` — image-based hidden text with Pillow
- [ ] `generate/csv_gen.py` — CSV payloads

### CLI: generate command
- [ ] `maldoc generate` — select attack + format, output to `output/`
- [ ] Verify: generate a PDF with hidden_text attack, inspect output manually

---

## Phase 3: Demo app

- [ ] `demo/config.py` — Ollama env var config
- [ ] `demo/pipeline.py` — parse → OCR → chunk → embed → store pipeline
- [ ] `demo/app.py` — FastAPI app with endpoints: upload, ask, extracted, chunks, reset, health
- [ ] `demo/Dockerfile`
- [ ] `demo/requirements.txt`
- [ ] `docker-compose.yml`
- [ ] Verify: `docker compose up --build demo-app`, upload a clean PDF, ask a question, get answer

---

## Phase 4: Adapters

- [ ] `adapters/base.py` — BaseAdapter ABC (upload, query, get_extracted_text, reset)
- [ ] `adapters/demo.py` — DemoAdapter targeting localhost:8000
- [ ] `adapters/http.py` — generic HttpAdapter with configurable URL mappings
- [ ] Verify: DemoAdapter can upload, query, and reset against running demo app

---

## Phase 5: Evaluation pipeline

- [ ] `evaluate/evidence.py` — evidence capture models (extracted text, chunks, responses)
- [ ] `evaluate/scoring.py` — survival and influence scoring functions
- [ ] `evaluate/runner.py` — orchestrator: upload → query → capture → score
- [ ] CLI: `maldoc evaluate` subcommand
- [ ] Verify: evaluate a generated malicious doc against demo app, get structured result

---

## Phase 6: Reporting

- [ ] `report/json_report.py` — JSON output from EvaluationResult
- [ ] `report/markdown_report.py` — Markdown output with per-stage summary
- [ ] CLI: `maldoc report` subcommand
- [ ] Verify: generate report from evaluation output, review markdown

---

## Phase 7: Full pipeline and polish

- [ ] CLI: `maldoc run` — full pipeline (generate → evaluate → report)
- [ ] CLI: `maldoc demo` — start/stop/reset helpers
- [ ] Default config so `maldoc run` works with zero flags against demo app
- [ ] README.md with quickstart
- [ ] End-to-end test: clone → uv sync → docker compose up → maldoc run → report

---

## Phase 8: Test suite

- [ ] Set up pytest with `uv`, add to dev dependencies
- [ ] `tests/test_attacks.py` — unit tests for each core attack class
- [ ] `tests/test_generators.py` — unit tests for each document generator (verify output files, payload presence)
- [ ] `tests/test_adapters.py` — unit tests for adapter interface, mock-based tests for DemoAdapter and HttpAdapter
- [ ] `tests/test_scoring.py` — unit tests for survival and influence scoring functions
- [ ] `tests/test_reports.py` — unit tests for JSON and Markdown report output
- [ ] `tests/test_cli.py` — CLI smoke tests via Typer test runner
- [ ] `tests/integration/test_end_to_end.py` — full pipeline against demo app (requires Docker, marked as integration)
- [ ] CI-ready: all unit tests pass without Docker or Ollama

---

## Phase 9: Remaining attack classes

- [ ] `attacks/ocr_bait.py` — full implementation
- [ ] `attacks/off_page.py` — full implementation
- [ ] `attacks/chunk_split.py` — full implementation
- [ ] `attacks/summary_steer.py` — full implementation
- [ ] `attacks/delayed_trigger.py` — full implementation
- [ ] `attacks/tool_routing.py` — full implementation
- [ ] Verify each against demo app, confirm scoring captures the technique
- [ ] Add unit tests for each new attack class
