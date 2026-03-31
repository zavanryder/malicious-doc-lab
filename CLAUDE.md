# CLAUDE.md

## Project

`malicious-doc-lab` is a local-first offensive security framework for generating adversarial documents and evaluating them against AI document-processing pipelines. It includes a deliberately vulnerable demo app for end-to-end testing.

This is a security research tool. Generated documents are adversarial by design. Do not add safety guards, input sanitization, or defensive hardening to the demo app — it is intentionally vulnerable.

## Architecture

- `src/maldoc/` — Python package, CLI tool named `maldoc`
- `demo/` — Demo-API: FastAPI REST app (Dockerized, intentionally vulnerable, port 8000)
- `demo-chatbot/` — Demo-Chatbot: FastAPI chatbot with browser UI (Dockerized, intentionally vulnerable, port 8001)
- `documents/` — detailed documentation (attacks, formats, walkthroughs)
- `reports/` — evaluation report output (gitignored except `.gitkeep`)
- `output/` — generated adversarial documents (gitignored)
- `planning/` — design docs (PLAN.md, ARCHITECTURE.md, TASKS.md)
- `tests/` — pytest test suite (166 tests)
- See `planning/ARCHITECTURE.md` for full layout and data flow

## Commands

```bash
# Install dependencies
uv sync

# Run CLI
uv run maldoc --help
uv run maldoc run --attack retrieval_poison --format pdf                  # full pipeline against Demo-API
uv run maldoc run --attack retrieval_poison --format pdf --target chatbot # full pipeline against Demo-Chatbot
uv run maldoc generate --attack metadata --format docx                    # generate adversarial documents only
uv run maldoc evaluate --file output/doc.pdf --attack ...                 # evaluate against a target
uv run maldoc report --input reports/eval.json                            # generate report from results
uv run maldoc demo start                                                  # start both demo services via Docker

# Run tests
uv run pytest                  # unit tests (no Docker/Ollama needed)
uv run pytest -m integration   # integration tests (requires Docker + Ollama)

# Demo services (user provides Ollama externally)
OLLAMA_BASE_URL=http://192.168.68.61:11434 docker compose up --build -d demo-app demo-chatbot

# Demo-Chatbot in black-box mode (hides evidence endpoints)
BLACK_BOX=true OLLAMA_BASE_URL=http://192.168.68.61:11434 docker compose up --build -d demo-chatbot
```

## Code style

- Package manager: `uv`. Always `uv run`, never `python3` directly. Always `uv add`, never `pip install`.
- CLI framework: Typer
- Data models: Pydantic
- HTTP client: httpx
- Keep modules short and focused. Small functions, clear names.
- No emojis in code, print statements, or logging.
- Docstrings on public functions. Minimal inline comments.
- No defensive programming. No unnecessary error handling.
- Do not add abstractions for one-time operations.

## Key conventions

- 14 attack classes, all inherit from `BaseAttack` ABC in `attacks/base.py`
- 4 adapters (base ABC, DemoAdapter, ChatbotAdapter, HttpAdapter) in `adapters/`
- 10 document format generators (pdf, docx, html, md, txt, csv, image, xlsx, pptx, eml) in `generate/`
- Generated documents write to `output/` by default
- Reports write to `reports/` by default with descriptive filenames (e.g., `20260329_143000_demo_retrieval_poison_report.md`)
- Report filenames follow the pattern `{YYYYMMDD}_{HHMMSS}_{target}_{attack|multiple}_report.{json,md}` (`multiple` only when results include more than one attack)
- Markdown reports include an "Attack Summary" table (per-attack averages) when multiple attack types are present, above the "All Results" per-test table
- CLI `run` command accepts comma-separated `--attack` and `--format` values; unsupported pairs are skipped automatically
- `src/maldoc/coverage.py` defines the attack/format compatibility matrix (supported, degraded, unsupported)
- CLI uses `--output-dir` for generated documents, `--reports-dir` for reports
- Demo-API defaults: `--target demo` (auto-resolves to `http://localhost:8000`)
- Demo-Chatbot defaults: `--target chatbot` (auto-resolves to `http://localhost:8001`)
- Both demo apps read Ollama config from env vars: `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_EMBED_MODEL`
- Demo-Chatbot supports `BLACK_BOX` env var: when true, hides `/extracted`, `/chunks`, `/reset` endpoints
- In black-box mode, extraction and chunk scores are `None` ("N/A" in reports)
- `docker-compose.yml` defines two services (`demo-app`, `demo-chatbot`); user provides Ollama externally
- `docker-compose.yml` includes `extra_hosts` for Linux `host.docker.internal` support

## Attacks

`hidden_text`, `white_on_white`, `metadata`, `retrieval_poison`, `ocr_bait`, `off_page`, `chunk_split`, `summary_steer`, `delayed_trigger`, `tool_routing`, `encoding_obfuscation`, `typoglycemia`, `markdown_exfil`, `visual_scaling_injection`

## Testing

- pytest for all tests (166 tests, 0 warnings)
- Unit tests must run without Docker or Ollama
- Integration tests are marked with `@pytest.mark.integration`
- Test files mirror source layout: `tests/test_attacks.py`, `tests/test_generators.py`, etc.
- `pytest-httpx` is used for mocking HTTP calls in adapter tests

## Documentation

Detailed docs are in `documents/`:
- `attacks-and-techniques.md` — all 14 attacks with scoring guide and real-world examples
- `file-formats.md` — all 10 formats with attack surfaces and testing recommendations
- `walkthrough-demo.md` — end-to-end demo app walkthrough
- `walkthrough-real-targets.md` — real-world testing scenarios and custom adapter guide

## Important

- Both demo apps are intentionally vulnerable. Do not harden them.
- Attack payloads are adversarial by design. Do not sanitize them.
- This is a security research tool, not a production application.
- Use DejaVu TTF fonts in PDF generation for Unicode support (not Helvetica).
- Both demo apps require `python-multipart` for file upload support.
- Demo-Chatbot has a browser UI at `http://localhost:8001/` for manual interaction.
