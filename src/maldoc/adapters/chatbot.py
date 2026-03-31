"""Adapter for the Demo-Chatbot app."""

from pathlib import Path

import httpx

from maldoc.adapters.base import (
    BaseAdapter,
    EvidenceUnavailableError,
    QueryResult,
    UploadResult,
)


class ChatbotAdapter(BaseAdapter):
    """Adapter targeting the Demo-Chatbot via its conversational /chat endpoint."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=300.0)

    def upload(self, file_path: Path) -> UploadResult:
        with file_path.open("rb") as f:
            response = self.client.post(
                "/chat",
                data={"message": "Please analyze this document."},
                files={"file": (file_path.name, f)},
            )
        response.raise_for_status()
        data = response.json()
        return UploadResult(
            filename=file_path.name,
            extracted_length=data.get("extracted_length", 0),
            num_chunks=data.get("num_chunks", 0),
            raw_response=data,
        )

    def query(self, question: str) -> QueryResult:
        response = self.client.post("/chat", data={"message": question})
        response.raise_for_status()
        data = response.json()
        return QueryResult(
            answer=data["content"],
            context_chunks=data.get("sources", []),
            model=data.get("model"),
            raw_response=data,
        )

    def get_extracted_text(self) -> str:
        try:
            response = self.client.get("/extracted")
            response.raise_for_status()
            return response.json().get("extracted_text", "")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise EvidenceUnavailableError("Extraction evidence endpoint unavailable") from exc
            raise

    def get_chunks(self) -> list[str]:
        try:
            response = self.client.get("/chunks")
            response.raise_for_status()
            return response.json().get("chunks", [])
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise EvidenceUnavailableError("Chunk evidence endpoint unavailable") from exc
            raise

    def reset(self) -> None:
        try:
            response = self.client.post("/reset")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return
            raise

    def close(self) -> None:
        self.client.close()
