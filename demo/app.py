"""FastAPI demo application — intentionally vulnerable document processing app."""

from fastapi import FastAPI, UploadFile
import ollama
from starlette.concurrency import run_in_threadpool

from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from pipeline import (
    get_last_chunks,
    get_last_extracted_text,
    ingest,
    query_documents,
    reset_state,
)

app = FastAPI(title="maldoc demo", description="Intentionally vulnerable demo app")
ollama_client = ollama.Client(host=OLLAMA_BASE_URL)


@app.post("/upload")
async def upload(file: UploadFile):
    """Upload and ingest a document."""
    contents = await file.read()
    result = await run_in_threadpool(ingest, contents, file.filename)
    return result


@app.post("/ask")
async def ask(question: str):
    """Ask a question against ingested content."""
    relevant_chunks = await run_in_threadpool(query_documents, question)
    context = "\n\n".join(relevant_chunks)

    # Intentionally vulnerable: raw context injection into prompt
    prompt = (
        f"Answer the following question based on the provided context.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer:"
    )

    response = await run_in_threadpool(
        ollama_client.chat,
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return {
        "answer": response["message"]["content"],
        "context_chunks": relevant_chunks,
        "model": OLLAMA_MODEL,
        "prompt": prompt,
    }


@app.get("/extracted")
async def extracted():
    """Return raw extracted text from last upload."""
    return {"extracted_text": get_last_extracted_text()}


@app.get("/chunks")
async def chunks():
    """Return chunks from last upload."""
    chunks = get_last_chunks()
    return {"chunks": chunks, "count": len(chunks)}


@app.post("/reset")
async def reset():
    """Clear all ingested data."""
    reset_state()
    return {"status": "reset"}


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}
