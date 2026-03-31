"""Demo-chatbot wrapper around the shared document-processing pipeline."""

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHROMA_COLLECTION,
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_MODEL,
)
from shared_pipeline import PipelineState

_pipeline = PipelineState(
    chroma_collection=CHROMA_COLLECTION,
    ollama_base_url=OLLAMA_BASE_URL,
    ollama_embed_model=OLLAMA_EMBED_MODEL,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)


def reset_state() -> None:
    """Clear all ingested data."""
    _pipeline.reset_state()


def parse_document(file_bytes: bytes, filename: str) -> str:
    """Extract text from a document based on file extension."""
    return _pipeline.parse_document(file_bytes, filename)


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks."""
    return _pipeline.chunk_text(text)


def embed_and_store(chunks: list[str]) -> None:
    """Embed chunks and store them in ChromaDB."""
    _pipeline.embed_and_store(chunks)


def query_documents(question: str, n_results: int = 3) -> list[str]:
    """Query ChromaDB for relevant chunks."""
    return _pipeline.query_documents(question, n_results=n_results)


def ingest(file_bytes: bytes, filename: str) -> dict:
    """Full ingestion pipeline: parse -> chunk -> embed -> store."""
    return _pipeline.ingest(file_bytes, filename)


def get_last_extracted_text() -> str:
    """Return raw extracted text from the last upload."""
    return _pipeline.last_extracted_text


def get_last_chunks() -> list[str]:
    """Return chunks from the last upload."""
    return _pipeline.last_chunks
