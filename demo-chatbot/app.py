"""FastAPI Demo-Chatbot — intentionally vulnerable chatbot with document upload."""

from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
import ollama
from starlette.concurrency import run_in_threadpool

from config import BLACK_BOX, HISTORY_LIMIT, OLLAMA_BASE_URL, OLLAMA_MODEL
from pipeline import (
    get_last_chunks,
    get_last_extracted_text,
    ingest,
    query_documents,
    reset_state,
)

app = FastAPI(title="maldoc Demo-Chatbot", description="Intentionally vulnerable chatbot demo")
ollama_client = ollama.Client(host=OLLAMA_BASE_URL)

# Global conversation history (intentionally vulnerable: single shared session)
conversation_history: list[dict] = []

STATIC_DIR = Path(__file__).parent / "static"


def _append_history(role: str, content: str) -> None:
    """Append to shared history with a bounded in-memory size."""
    conversation_history.append({"role": role, "content": content})
    overflow = len(conversation_history) - HISTORY_LIMIT
    if overflow > 0:
        del conversation_history[:overflow]


@app.get("/")
async def index():
    """Serve the chat UI."""
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/chat")
async def chat(
    message: str = Form(""),
    file: UploadFile | None = File(None),
):
    """Conversational endpoint with optional file upload."""
    file_metadata = {}
    user_display = message

    # Handle file upload through the chat interface
    if file and file.filename:
        contents = await file.read()
        result = await run_in_threadpool(ingest, contents, file.filename)
        file_metadata = {
            "extracted_length": result["extracted_length"],
            "num_chunks": result["num_chunks"],
        }
        file_label = f"[Uploaded: {file.filename}]"
        user_display = f"{file_label} {message}" if message else file_label

    # Record user message in history
    _append_history("user", user_display)

    # Retrieve relevant context from ingested documents
    query_text = message or "Summarize the uploaded document."
    relevant_chunks = await run_in_threadpool(query_documents, query_text)
    context = "\n\n".join(relevant_chunks)

    # Build conversation messages for Ollama (intentionally vulnerable: raw injection)
    system_prompt = (
        "You are a helpful assistant. Answer questions based on the provided context "
        "and conversation history. If a document was just uploaded, acknowledge it and "
        "provide your analysis."
    )
    messages = [{"role": "system", "content": system_prompt}]

    # Include context if available
    if context:
        messages.append({
            "role": "system",
            "content": f"Document context:\n{context}",
        })

    # Include recent conversation history (last 20 messages)
    for msg in conversation_history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    response = await run_in_threadpool(
        ollama_client.chat,
        model=OLLAMA_MODEL,
        messages=messages,
    )
    assistant_content = response["message"]["content"]

    # Record assistant response in history
    _append_history("assistant", assistant_content)

    result = {
        "role": "assistant",
        "content": assistant_content,
        "sources": relevant_chunks,
        "model": OLLAMA_MODEL,
    }
    result.update(file_metadata)
    return result


@app.get("/history")
async def history():
    """Return conversation history."""
    return {"messages": conversation_history[-HISTORY_LIMIT:]}


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}


@app.post("/reset")
async def reset():
    """Clear conversation history and all ingested data."""
    conversation_history.clear()
    reset_state()
    return {"status": "reset"}


# Evidence endpoints — conditionally registered based on BLACK_BOX setting
if not BLACK_BOX:

    @app.get("/extracted")
    async def extracted():
        """Return raw extracted text from last upload."""
        return {"extracted_text": get_last_extracted_text()}

    @app.get("/chunks")
    async def chunks():
        """Return chunks from last upload."""
        chunks = get_last_chunks()
        return {"chunks": chunks, "count": len(chunks)}
