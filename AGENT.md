# AGENT.md

Instructions for AI coding agents working on this project. If you are Claude Code, see CLAUDE.md (which extends this file).

## Project overview

`malicious-doc-lab` is a local-first offensive security framework that:
- Generates adversarial documents (PDF, DOCX, HTML, Markdown, TXT, CSV, XLSX, PPTX, EML, images)
- Evaluates them against AI document-processing and RAG pipelines
- Reports whether malicious payloads survived parsing, influenced retrieval, and affected responses
- Includes two Dockerized intentionally vulnerable demo apps for end-to-end testing (Demo-API and Demo-Chatbot)

This is a security research tool. All adversarial content is by design. Do not add safety guards or hardening to the demo app.

## Repository layout

```
src/maldoc/          # Python package — the CLI tool
  cli.py             # Typer CLI entrypoint
  generate/          # Document generators (10 formats: pdf, docx, html, md, txt, csv, xlsx, pptx, eml, image)
  attacks/           # 14 attack class implementations
  adapters/          # Target adapters (demo, chatbot, generic HTTP, base ABC)
  evaluate/          # Evaluation pipeline, evidence models, scoring
  report/            # JSON and Markdown report output
demo/                # Demo-API: FastAPI REST app (intentionally vulnerable, port 8000)
  app.py             # FastAPI endpoints
  pipeline.py        # Parse -> OCR -> chunk -> embed -> store pipeline
  config.py          # Ollama env var configuration
  Dockerfile
demo-chatbot/        # Demo-Chatbot: FastAPI chatbot with browser UI (intentionally vulnerable, port 8001)
  app.py             # FastAPI chatbot endpoints (POST /chat with file upload)
  pipeline.py        # Thin wrapper around shared_pipeline.PipelineState
  config.py          # Ollama config + BLACK_BOX env var
  static/index.html  # Chat UI (HTML/CSS/JS)
  Dockerfile
shared_pipeline.py   # Shared parse -> chunk -> embed -> store implementation
documents/           # Detailed documentation
  attacks-and-techniques.md
  file-formats.md
  walkthrough-demo.md
  walkthrough-real-targets.md
tests/               # pytest suite (197 tests)
reports/             # Evaluation reports (gitignored except .gitkeep)
output/              # Generated adversarial documents (gitignored)
planning/            # Design docs (PLAN.md, ARCHITECTURE.md, TASKS.md)
```

## Setup and commands

```bash
uv sync                                          # install dependencies
uv run maldoc --help                             # CLI help
uv run maldoc run --attack summary_steer --format pdf                  # full pipeline against Demo-API
uv run maldoc run --attack summary_steer --format pdf --target chatbot # full pipeline against Demo-Chatbot
uv run maldoc run --attack-plus-format hidden_text:pdf,ocr_bait:image  # explicit attack:format pairs
uv run maldoc generate --attack metadata --format docx                 # generate only
uv run pytest                                    # unit tests
uv run pytest -m integration                     # integration tests (needs Docker + Ollama)

# Demo services (user provides Ollama externally)
OLLAMA_BASE_URL=http://your-ollama-host:11434 docker compose up --build -d demo-app demo-chatbot

# Demo-Chatbot in black-box mode (hides evidence endpoints)
BLACK_BOX=true docker compose up --build -d demo-chatbot
```

## Development rules

1. **Package manager**: Use `uv` exclusively. `uv run` to execute, `uv add` to add dependencies. Never use `pip` or raw `python3`.
2. **No defensive coding**: No unnecessary try/except, no input validation beyond system boundaries. Trust internal code.
3. **Keep it simple**: Short modules, short functions, clear names. No premature abstractions.
4. **Do not harden the demo app**: It is intentionally vulnerable. Do not add auth, sanitization, or rate limiting.
5. **Attack content is intentional**: Payloads are adversarial by design. Do not sanitize or filter them.
6. **Testing**: Unit tests must not require Docker or Ollama. Mark integration tests with `@pytest.mark.integration`.
7. **Output directories**: Generated documents go to `output/`. Reports go to `reports/`.
8. **Report naming**: Reports use descriptive filenames: `{YYYYMMDD}_{HHMMSS}_{target}_{attack|multiple}_report.{json,md}` (`multiple` only when more than one attack is included in a consolidated run).
9. **Report structure**: Markdown reports include an "Attack Summary" table (per-attack averages) when multiple attack types are present, above the per-test "All Results" table.
10. **Batch runs**: CLI `run` accepts comma-separated `--attack` and `--format` values (cross-product), or `--attack-plus-format` for explicit `attack:format` pairs. Unsupported pairs are automatically skipped and recorded in report metadata. The compatibility matrix is in `src/maldoc/coverage.py`.
11. **Artifact cleanup**: `run` keeps generated output files by default after evaluation. Use `--delete-artifacts` to remove them automatically. Other commands (`generate`, `evaluate`) do not delete output.
12. **Report metadata**: Consolidated reports carry execution mode (`white_box`, `black_box`, or `mixed`), requested attacks/formats, and skipped combinations.
13. **Black-box targets**: Missing `/extracted` and `/chunks` endpoints are valid. Adapters should degrade extraction/chunk scoring to `N/A` rather than fail outright. `/reset` is optional for generic HTTP targets and always available on the demo-chatbot.
14. **PDF Unicode**: Use DejaVu TTF fonts (not Helvetica) for Unicode support in PDF generation.

## Key interfaces

**Attack classes** implement `BaseAttack` (see `src/maldoc/attacks/base.py`):
- `name`, `description` properties
- `apply(payload, template) -> AttackResult` method
- `default_payload() -> str` for default adversarial text

All 14 attacks: `hidden_text`, `white_on_white`, `metadata`, `retrieval_poison`, `ocr_bait`, `off_page`, `chunk_split`, `summary_steer`, `delayed_trigger`, `tool_routing`, `encoding_obfuscation`, `typoglycemia`, `markdown_exfil`, `visual_scaling_injection`

**Adapters** implement `BaseAdapter` (see `src/maldoc/adapters/base.py`):
- `upload(file_path) -> UploadResult`
- `query(question) -> QueryResult`
- `get_extracted_text() -> str`
- `get_chunks() -> list[str]`
- `reset() -> None`

Built-in adapters: `DemoAdapter` (Demo-API), `ChatbotAdapter` (Demo-Chatbot), `HttpAdapter` (generic REST).
The `ChatbotAdapter` maps the BaseAdapter interface onto the chatbot's `POST /chat` endpoint. Both it and `HttpAdapter` treat missing evidence endpoints as black-box mode rather than hard failure.

**Document generators** are standalone functions in `generate/`, one per format module. The `generate_document()` function in `generate/__init__.py` dispatches to the correct generator.

**Reports** use `report_filename(result)` to generate descriptive names. Both JSON and Markdown reports are produced by default in the `run` command.

## Architecture details

See `planning/ARCHITECTURE.md` for full component design, data flow, dependency list, and demo app endpoints.

See `planning/TASKS.md` for implementation phases and checklist.

See `documents/` for detailed documentation on attacks, formats, and walkthroughs.
