"""Adapter for the built-in demo app."""

from pathlib import Path

import httpx

from maldoc.adapters.base import BaseAdapter, QueryResult, UploadResult


class DemoAdapter(BaseAdapter):
    """Adapter targeting the local FastAPI demo app."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=300.0)

    def upload(self, file_path: Path) -> UploadResult:
        with file_path.open("rb") as f:
            response = self.client.post(
                "/upload", files={"file": (file_path.name, f)}
            )
        response.raise_for_status()
        data = response.json()
        return UploadResult(
            filename=data["filename"],
            extracted_length=data["extracted_length"],
            num_chunks=data["num_chunks"],
            raw_response=data,
        )

    def query(self, question: str) -> QueryResult:
        response = self.client.post("/ask", params={"question": question})
        response.raise_for_status()
        data = response.json()
        return QueryResult(
            answer=data["answer"],
            context_chunks=data["context_chunks"],
            model=data.get("model"),
            prompt=data.get("prompt"),
            raw_response=data,
        )

    def get_extracted_text(self) -> str:
        response = self.client.get("/extracted")
        response.raise_for_status()
        return response.json()["extracted_text"]

    def get_chunks(self) -> list[str]:
        response = self.client.get("/chunks")
        response.raise_for_status()
        return response.json()["chunks"]

    def reset(self) -> None:
        response = self.client.post("/reset")
        response.raise_for_status()

    def close(self) -> None:
        self.client.close()
