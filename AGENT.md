# AGENT.md

Instructions for AI coding agents working on this project. If you are Claude Code, see CLAUDE.md (which extends this file).

## Project overview

`malicious-doc-lab` is a local-first offensive security framework that:
- Generates adversarial documents (PDF, DOCX, HTML, Markdown, CSV, images)
- Evaluates them against AI document-processing and RAG pipelines
- Reports whether malicious payloads survived parsing, influenced retrieval, and affected responses
- Includes a Dockerized intentionally vulnerable demo app for end-to-end testing

This is a security research tool. All adversarial content is by design. Do not add safety guards or hardening to the demo app.

## Repository layout

```
src/maldoc/          # Python package — the CLI tool
  cli.py             # Typer CLI entrypoint
  generate/          # Document generators (6 formats: pdf, docx, html, md, csv, image)
  attacks/           # 10 attack class implementations
  adapters/          # Target adapters (demo app, generic HTTP, base ABC)
  evaluate/          # Evaluation pipeline, evidence models, scoring
  report/            # JSON and Markdown report output
demo/                # FastAPI demo app (intentionally vulnerable)
  app.py             # FastAPI endpoints
  pipeline.py        # Parse -> OCR -> chunk -> embed -> store pipeline
  config.py          # Ollama env var configuration
  Dockerfile
documents/           # Detailed documentation
  attacks-and-techniques.md
  file-formats.md
  walkthrough-demo.md
  walkthrough-real-targets.md
tests/               # pytest suite (117 tests)
reports/             # Evaluation reports (gitignored except .gitkeep)
output/              # Generated adversarial documents (gitignored)
planning/            # Design docs (PLAN.md, ARCHITECTURE.md, TASKS.md)
```

## Setup and commands

```bash
uv sync                                          # install dependencies
uv run maldoc --help                             # CLI help
uv run maldoc run --attack summary_steer --format pdf  # full pipeline
uv run maldoc generate --attack metadata --format docx # generate only
uv run pytest                                    # unit tests
uv run pytest -m integration                     # integration tests (needs Docker + Ollama)

# Demo app (user provides Ollama externally)
OLLAMA_BASE_URL=http://your-ollama-host:11434 docker compose up --build -d demo-app
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
9. **PDF Unicode**: Use DejaVu TTF fonts (not Helvetica) for Unicode support in PDF generation.

## Key interfaces

**Attack classes** implement `BaseAttack` (see `src/maldoc/attacks/base.py`):
- `name`, `description` properties
- `apply(payload, template) -> AttackResult` method
- `default_payload() -> str` for default adversarial text

All 10 attacks: `hidden_text`, `white_on_white`, `metadata`, `retrieval_poison`, `ocr_bait`, `off_page`, `chunk_split`, `summary_steer`, `delayed_trigger`, `tool_routing`

**Adapters** implement `BaseAdapter` (see `src/maldoc/adapters/base.py`):
- `upload(file_path) -> UploadResult`
- `query(question) -> QueryResult`
- `get_extracted_text() -> str`
- `get_chunks() -> list[str]`
- `reset() -> None`

**Document generators** are standalone functions in `generate/`, one per format module. The `generate_document()` function in `generate/__init__.py` dispatches to the correct generator.

**Reports** use `report_filename(result)` to generate descriptive names. Both JSON and Markdown reports are produced by default in the `run` command.

## Architecture details

See `planning/ARCHITECTURE.md` for full component design, data flow, dependency list, and demo app endpoints.

See `planning/TASKS.md` for implementation phases and checklist.

See `documents/` for detailed documentation on attacks, formats, and walkthroughs.
