# Architecture

## Overview

`malicious-doc-lab` is a Typer CLI (`maldoc`) that generates adversarial documents, evaluates them against AI document-processing pipelines, and produces JSON/Markdown reports. The current design supports both white-box and black-box targets and uses a shared ingestion pipeline for both built-in demo services.

```
┌─────────────────────────────────────────────────────┐
│                    maldoc CLI                       │
│                                                     │
│  generate ──▶ evaluate ──▶ report                   │
│       └── run (full pipeline) ──────┘               │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│              Target (via Adapter)                   │
│                                                     │
│  Demo-API / Demo-Chatbot / Custom HTTP target       │
│  - upload / query / optional reset                  │
│  - optional extraction and chunk evidence           │
└─────────────────────────────────────────────────────┘
```

## Repository Layout

```
malicious-doc-lab/
├── src/maldoc/
│   ├── cli.py
│   ├── coverage.py
│   ├── attacks/             # 14 attack implementations
│   ├── adapters/            # DemoAdapter, ChatbotAdapter, HttpAdapter, base ABC
│   ├── evaluate/            # Evidence models, runner, scoring
│   ├── generate/            # 10 generator modules, 13 CLI format labels
│   └── report/              # JSON and Markdown reporting
├── demo/
│   ├── app.py               # Demo-API FastAPI endpoints
│   ├── pipeline.py          # Thin wrapper around shared_pipeline.PipelineState
│   ├── config.py
│   └── Dockerfile
├── demo-chatbot/
│   ├── app.py               # Demo-Chatbot FastAPI endpoints
│   ├── pipeline.py          # Thin wrapper around shared_pipeline.PipelineState
│   ├── config.py
│   ├── static/index.html
│   └── Dockerfile
├── shared_pipeline.py       # Shared parse -> chunk -> embed -> store implementation
├── documents/
├── planning/
├── tests/
├── docker-compose.yml
└── README.md
```

## Core Components

### CLI

Commands:

| Command | Purpose |
|---------|---------|
| `maldoc generate` | Generate adversarial documents only |
| `maldoc evaluate` | Evaluate one existing document against a target |
| `maldoc report` | Render reports from saved evaluation JSON |
| `maldoc run` | Generate -> evaluate -> report in one step |
| `maldoc demo` | Start, stop, or reset the built-in demo services |

`run` accepts comma-separated `--attack` and `--format` values (cross-product), or `--attack-plus-format` for explicit `attack:format` pairs. Unsupported combinations are skipped, echoed to the console, and stored in report metadata. By default, `run` keeps generated artifacts after evaluation; pass `--delete-artifacts` to remove them automatically.

### Attack Layer

All attacks inherit from `BaseAttack` and return an `AttackResult`:

- `visible_content`
- `hidden_content`
- `metadata`
- `technique`
- `format_hints`

Coverage realism is controlled separately by `src/maldoc/coverage.py`, which marks attack/format pairs as supported, degraded, or unsupported.

### Generator Layer

Generators are standalone modules for:

- `pdf`
- `docx`
- `html`
- `md`
- `txt`
- `csv`
- `image`
- `xlsx`
- `pptx`
- `eml`

The CLI additionally exposes `png`, `jpg`, and `jpeg` as aliases for the image generator.

Recent fidelity rule:
- Fallback generators must preserve the intended transformed carrier for an attack rather than leak the literal payload as a generic hidden field.

### Adapter Layer

Built-in adapters:

- `DemoAdapter` for the demo REST API
- `ChatbotAdapter` for the demo chatbot
- `HttpAdapter` for custom HTTP targets

Adapter contract:

- `upload(file_path)`
- `query(question)`
- `get_extracted_text()`
- `get_chunks()`
- `reset()`

Black-box behavior:

- Missing `/extracted` or `/chunks` raise `EvidenceUnavailableError`
- The evaluator downgrades extraction/chunk scoring to `N/A`
- Missing `/reset` is tolerated by `HttpAdapter`
- `demo-chatbot` always exposes `/reset`, even in black-box mode, so batch runs remain isolated

### Evaluation Layer

The evaluator performs:

1. Reset target state when available
2. Upload the generated document
3. Capture extraction evidence when available
4. Capture chunk evidence when available
5. Query the target
6. Score extraction, chunking, retrieval, and response influence

Each `EvaluationResult` records `evidence_mode`:

- `white_box`
- `black_box`
- `mixed`

### Reporting Layer

`ConsolidatedReport` includes:

- `results`
- `execution_mode`
- `requested_attacks`
- `requested_formats`
- `skipped_combinations`
- `cli_commands`

Markdown reports surface:

- overall verdict
- execution mode
- requested attacks and formats
- skipped combinations
- attack summary table for multi-attack runs
- per-result evidence mode

## Demo Services

Both demo apps are intentionally vulnerable and share `shared_pipeline.PipelineState`.

### Shared Pipeline

Pipeline stages:

1. Parse uploaded document bytes
2. OCR embedded images where applicable
3. Chunk extracted text
4. Embed chunks with Ollama embeddings
5. Store vectors in ChromaDB
6. Query relevant chunks and send context to Ollama chat

The pipeline now lives once in `shared_pipeline.py`; `demo/pipeline.py` and `demo-chatbot/pipeline.py` are thin wrappers configured with different collection names.

### Demo-API

Endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/upload` | Upload and ingest a document |
| POST | `/ask` | Query ingested content |
| GET | `/extracted` | Return raw extracted text |
| GET | `/chunks` | Return stored chunks |
| POST | `/reset` | Clear ingested state |
| GET | `/health` | Health check |

### Demo-Chatbot

Endpoints:

| Method | Path | Purpose | Black-box behavior |
|--------|------|---------|--------------------|
| GET | `/` | Browser chat UI | Always available |
| POST | `/chat` | Chat + optional file upload | Always available |
| GET | `/history` | Shared history view | Always available |
| GET | `/extracted` | Raw extracted text | Hidden when `BLACK_BOX=true` |
| GET | `/chunks` | Stored chunks | Hidden when `BLACK_BOX=true` |
| POST | `/reset` | Clear history + ingested state | Always available |
| GET | `/health` | Health check | Always available |

Operational detail:
- Both FastAPI apps offload blocking parse/embed/chat work with `run_in_threadpool` rather than blocking the event loop directly.

## Deployment Notes

`docker-compose.yml` builds both demo images from the repo root:

```yaml
services:
  demo-app:
    build:
      context: .
      dockerfile: demo/Dockerfile

  demo-chatbot:
    build:
      context: .
      dockerfile: demo-chatbot/Dockerfile
```

That lets both images copy `shared_pipeline.py` without duplicating the ingestion implementation.

Environment variables:

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_EMBED_MODEL`
- `BLACK_BOX` for `demo-chatbot`
- `HISTORY_LIMIT` for `demo-chatbot`

## Test Coverage

Current local suite:

- `197 passed`

Regression coverage now includes:

- transformed-carrier generator fidelity
- black-box evidence handling in adapters/evaluator
- report metadata for execution mode and skipped combinations
- shared demo pipeline structure
- demo app threadpool usage and chatbot reset availability
- `--attack-plus-format` parsing, validation, and pipeline execution
- `--delete-artifacts` / default artifact retention behavior
