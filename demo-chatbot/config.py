"""Demo-Chatbot configuration — reads from environment variables."""

import os


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHROMA_COLLECTION = "maldoc_chatbot"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
BLACK_BOX = os.getenv("BLACK_BOX", "false").lower() in ("true", "1", "yes")
