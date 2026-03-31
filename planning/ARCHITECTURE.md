# Architecture

## Overview

`malicious-doc-lab` is a CLI tool (`maldoc`) that generates adversarial documents, evaluates them against AI document-processing pipelines, and produces evidence-rich reports.

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
│              Target (via Adapter)                    │
│                                                     │
│  Built-in demo app (FastAPI)    OR   Custom target  │
│  - upload / ingest / ask / reset     via adapter    │
└─────────────────────────────────────────────────────┘
```

---

## Package layout

```
malicious-doc-lab/
├── src/
│   └── maldoc/
│       ├── __init__.py
│       ├── cli.py                  # Typer CLI entrypoint
│       ├── generate/
│       │   ├── __init__.py
│       │   ├── payloads.py         # Attack payload definitions
│       │   ├── pdf.py              # PDF document generation
│       │   ├── docx.py             # DOCX document generation
│       │   ├── html.py             # HTML/Markdown generation
│       │   ├── image.py            # Image-based hidden text
│       │   ├── csv_gen.py          # CSV/spreadsheet payloads
│       │   └── templates.py        # Benign-looking document templates
│       ├── attacks/
│       │   ├── __init__.py
│       │   ├── base.py             # Base attack class
│       │   ├── hidden_text.py      # Hidden text attack
│       │   ├── white_on_white.py   # White-on-white text
│       │   ├── metadata.py         # Metadata injection
│       │   ├── retrieval_poison.py # Retrieval poisoning
│       │   ├── ocr_bait.py         # OCR bait (stub)
│       │   ├── off_page.py         # Off-page/layered text (stub)
│       │   ├── chunk_split.py      # Chunk-boundary split (stub)
│       │   ├── summary_steer.py    # Summary steering (stub)
│       │   ├── delayed_trigger.py  # Delayed trigger (stub)
│       │   └── tool_routing.py     # Tool-routing manipulation (stub)
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── base.py             # Base adapter interface (ABC)
│       │   ├── demo.py             # Adapter for Demo-API
│       │   ├── chatbot.py          # Adapter for Demo-Chatbot
│       │   └── http.py             # Generic HTTP adapter for custom targets
│       ├── evaluate/
│       │   ├── __init__.py
│       │   ├── runner.py           # Orchestrates evaluation pipeline
│       │   ├── scoring.py          # Survival and influence scoring
│       │   └── evidence.py         # Evidence capture and storage
│       └── report/
│           ├── __init__.py
│           ├── json_report.py      # JSON report output
│           └── markdown_report.py  # Markdown report output
├── demo/                               # Demo-API (port 8000)
│   ├── Dockerfile
│   ├── app.py                      # FastAPI REST endpoints
│   ├── pipeline.py                 # Parse → OCR → chunk → embed → store
│   ├── config.py                   # Ollama endpoint, model config
│   └── requirements.txt
├── demo-chatbot/                       # Demo-Chatbot (port 8001)
│   ├── Dockerfile
│   ├── app.py                      # FastAPI chatbot (POST /chat + browser UI)
│   ├── pipeline.py                 # Same RAG pipeline as Demo-API
│   ├── config.py                   # Ollama config + BLACK_BOX env var
│   ├── static/index.html           # Chat UI (HTML/CSS/JS)
│   └── requirements.txt
├── docker-compose.yml
├── pyproject.toml
├── planning/
│   ├── PLAN.md
│   ├── ARCHITECTURE.md
│   └── TASKS.md
└── README.md
```

---

## Core components

### CLI (`maldoc`)

Built with **Typer**. Subcommands:

| Command | Purpose |
|---------|---------|
| `maldoc generate` | Generate adversarial documents |
| `maldoc evaluate` | Evaluate documents against a target |
| `maldoc report` | Generate reports from evaluation results |
| `maldoc run` | Full pipeline: generate → evaluate → report |
| `maldoc demo` | Manage demo services (start, stop, reset) |

### Document generation (`maldoc.generate`)

Produces adversarial documents in various formats. Each generator takes a payload (attack content + benign wrapper) and writes a file.

**Libraries:**
- PDF: `fpdf2`
- DOCX: `python-docx`
- Image: `Pillow`
- CSV: stdlib `csv`
- HTML/MD: string templates

### Attack classes (`maldoc.attacks`)

Each attack class implements a common interface:

```python
class BaseAttack(ABC):
    name: str
    description: str

    @abstractmethod
    def apply(self, payload: str, template: dict) -> AttackResult:
        """Apply attack technique, return content ready for document generation."""
        ...
```

**v0.1.0 core (fully implemented):**
- `hidden_text` — zero-width characters, font-size-zero text
- `white_on_white` — white text on white background
- `metadata` — payload injected into document metadata fields
- `retrieval_poison` — content designed to rank high for target queries

**v0.1.0 stubs (interface only, implemented later):**
- `ocr_bait`, `off_page`, `chunk_split`, `summary_steer`, `delayed_trigger`, `tool_routing`

### Adapters (`maldoc.adapters`)

Adapters define how the tool interacts with a target system. This is the integration point for both the demo app and real-world targets.

```python
class BaseAdapter(ABC):
    @abstractmethod
    def upload(self, file_path: Path) -> UploadResult: ...

    @abstractmethod
    def query(self, question: str) -> QueryResult: ...

    @abstractmethod
    def get_extracted_text(self) -> str: ...

    @abstractmethod
    def reset(self) -> None: ...
```

**Built-in adapters:**
- `DemoAdapter` — talks to the Demo-API (`--target demo`, port 8000)
- `ChatbotAdapter` — talks to the Demo-Chatbot (`--target chatbot`, port 8001) via `POST /chat`; handles black-box mode (404 on evidence endpoints)
- `HttpAdapter` — configurable HTTP adapter for custom REST endpoints (`--target http`)

### Evaluation (`maldoc.evaluate`)

Orchestrates the evaluation pipeline:

1. Upload document via adapter
2. Query the target with attack-relevant questions
3. Capture evidence (extracted text, retrieval results, final responses)
4. Score each stage (parser survival, retrieval influence, response impact)

Scoring produces a structured `EvaluationResult` with per-stage scores. In black-box mode (when evidence endpoints are unavailable), extraction and chunking scores are `None` ("N/A" in reports).

### Reporting (`maldoc.report`)

Takes `EvaluationResult` and renders:
- **JSON** — machine-readable, full evidence
- **Markdown** — human-readable summary with pass/fail per stage

---

## Demo Apps

Both demo apps are deliberately vulnerable. **Not for production use.** They share the same RAG pipeline but expose different interaction models.

### Shared Pipeline

```
Document (bytes)
  → Parse (PyMuPDF, python-docx, BeautifulSoup)
  → OCR (pytesseract, if image content detected)
  → Chunk (naive fixed-size splitter)
  → Embed (Ollama embeddings)
  → Store (ChromaDB)
  → Query (ChromaDB similarity search → Ollama LLM completion)
```

### Demo-API (port 8000)

REST-style document processing API. Adapter: `DemoAdapter` (`--target demo`).

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/upload` | Upload and ingest a document |
| POST | `/ask` | Ask a question against ingested content |
| GET | `/extracted` | Return raw extracted text from last upload |
| GET | `/chunks` | Return chunks from last upload |
| POST | `/reset` | Clear all ingested data |
| GET | `/health` | Health check |

### Demo-Chatbot (port 8001)

Conversational chatbot with browser UI and file upload. Adapter: `ChatbotAdapter` (`--target chatbot`).

| Method | Path | Purpose | Black-box |
|--------|------|---------|-----------|
| GET | `/` | Chat UI (HTML) | Always |
| POST | `/chat` | Conversational endpoint (message + optional file) | Always |
| GET | `/history` | Conversation history | Always |
| GET | `/extracted` | Raw extracted text | Hidden when `BLACK_BOX=true` |
| GET | `/chunks` | Chunks | Hidden when `BLACK_BOX=true` |
| POST | `/reset` | Clear conversation + docs | Hidden when `BLACK_BOX=true` |
| GET | `/health` | Health check | Always |

The `POST /chat` endpoint accepts multipart form data (`message` + optional `file`). When a file is attached, it is ingested through the RAG pipeline and the response includes `extracted_length` and `num_chunks` metadata.

### Configuration

Both demo apps read Ollama connection details from environment variables:

- `OLLAMA_BASE_URL` — default `http://localhost:11434`
- `OLLAMA_MODEL` — default `llama3.2`
- `OLLAMA_EMBED_MODEL` — default `nomic-embed-text`

The Demo-Chatbot also reads:
- `BLACK_BOX` — default `false`; when `true`, hides evidence endpoints (`/extracted`, `/chunks`, `/reset`)

The user is responsible for providing a running Ollama instance.

---

## Docker Compose

```yaml
services:
  demo-app:
    build: ./demo
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://host.docker.internal:11434}
      - OLLAMA_MODEL=${OLLAMA_MODEL:-llama3.2}
      - OLLAMA_EMBED_MODEL=${OLLAMA_EMBED_MODEL:-nomic-embed-text}

  demo-chatbot:
    build: ./demo-chatbot
    ports:
      - "8001:8001"
    environment:
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://host.docker.internal:11434}
      - OLLAMA_MODEL=${OLLAMA_MODEL:-llama3.2}
      - OLLAMA_EMBED_MODEL=${OLLAMA_EMBED_MODEL:-nomic-embed-text}
      - BLACK_BOX=${BLACK_BOX:-false}
```

Two services. Ollama runs on the host or as a remote service — the user configures via env vars.

---

## Data flow

```
# Demo-API
User runs: maldoc run --attack hidden_text --format pdf --target demo

  1. generate:  hidden_text + pdf → output/malicious_hidden_text.pdf
  2. evaluate:  DemoAdapter.upload(pdf) → DemoAdapter.query("...") → score
  3. report:    EvaluationResult → reports/report.json + reports/report.md

# Demo-Chatbot
User runs: maldoc run --attack hidden_text --format pdf --target chatbot

  1. generate:  hidden_text + pdf → output/malicious_hidden_text.pdf
  2. evaluate:  ChatbotAdapter.upload(pdf via /chat) → ChatbotAdapter.query("..." via /chat) → score
  3. report:    EvaluationResult → reports/report.json + reports/report.md
```

---

## Key dependencies

| Package | Purpose |
|---------|---------|
| typer | CLI framework |
| fpdf2 | PDF generation |
| python-docx | DOCX generation |
| Pillow | Image generation |
| httpx | HTTP client (adapter communication) |
| pydantic | Data models |
| fastapi | Demo app |
| uvicorn | Demo app server |
| pymupdf | PDF parsing (demo) |
| pytesseract | OCR (demo) |
| chromadb | Vector store (demo) |
| ollama | Ollama Python client (demo) |
| beautifulsoup4 | HTML parsing (demo) |
