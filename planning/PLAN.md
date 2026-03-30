# Malicious Doc Lab — Agent-Facing Implementation Plan

## Mission

Build `malicious-doc-lab` as a local-first offensive security framework that:

- generates adversarial documents,
- evaluates them against AI ingestion and retrieval pipelines,
- includes a Dockerized intentionally vulnerable demo environment for end-to-end demonstrations,
- produces evidence-rich reports showing whether malicious content survived and influenced system behavior.

The first release must be runnable end to end with minimal setup and no custom target integration.

---

## Build principles

- Prefer a working demo over elaborate abstractions.
- Keep modules small and composable.
- Optimize for local reproducibility.
- Make the demo target intentionally vulnerable by design.
- Capture evidence at each stage.
- Make it easy to add new payloads, formats, and adapters later.
- Do not accidentally harden the demo environment into uselessness.

---

## Release target

## v0.1.0

## Features

### Document generation
- PDF generation
- DOCX generation
- HTML and Markdown generation
- image-based hidden text payloads
- CSV / spreadsheet payloads
- themed benign-looking document templates

### Attack classes
- hidden text
- white-on-white text
- off-page / layered text
- metadata injection
- OCR bait
- chunk-boundary split payloads
- retrieval poisoning
- summary steering
- delayed trigger instructions
- tool-routing manipulation

### Evaluation
- parser survival scoring
- OCR survival scoring
- chunk survival tracking
- retrieval influence detection
- summarization influence scoring
- final response / action impact scoring
- evidence capture with extracted text and response artifacts

### Docker demo environment
- intentionally vulnerable AI document-processing app
- upload + ingest workflow
- parser / OCR / chunk / retrieval pipeline
- simple chat or ask endpoint backed by ingested content
- optional unsafe tool execution mode for demo purposes
- resettable state for repeatable testing
- demo application will point at Ollama instance with the default being localhost host llama3.2
- demo application will give user the ability to specify remote Ollama instance to either query available models and select, or just select one from the command line

### Must have
- [ ] Python package with CLI
- [ ] Attack Classes
- [ ] Document Generation
- [ ] Built-in vulnerable FastAPI demo app
- [ ] Docker Compose demo environment
- [ ] Upload / ingest / ask / reset workflow
- [ ] Evaluation pipeline
- [ ] JSON report output
- [ ] Markdown report output
- [ ] Base adapter interface
- [ ] README and docs sufficient for first-time use

### Explicitly not required for v0.1.0
- [ ] Production deployment
- [ ] Browser UI
- [ ] Cloud services
- [ ] Defensive hardening mode

---

## Success criteria

A new user must be able to:

- [ ] clone the repo
- [ ] run `uv sync`
- [ ] run `docker compose up --build demo-app`
- [ ] generate a malicious PDF or DOCX
- [ ] evaluate it against the demo app
- [ ] receive a report showing:
  - [ ] whether the payload survived extraction
  - [ ] whether it influenced retrieval
  - [ ] whether it influenced the final response

No code changes should be required for the default demo flow.

---

## Planning directory convention

All planning and design artifacts should live under the root `planning/` directory.

Examples:

```text
planning/
  PLAN.md
  TASKS.md
  ARCHITECTURE.md
  THREAT_MODEL.md
  NOTES.md
  ROADMAP.md
