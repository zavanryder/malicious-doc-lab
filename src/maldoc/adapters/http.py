"""Generic HTTP adapter for custom REST targets."""

from pathlib import Path

import httpx

from maldoc.adapters.base import BaseAdapter, QueryResult, UploadResult


class HttpAdapter(BaseAdapter):
    """Configurable HTTP adapter for custom REST endpoints.

    URL mappings define how to interact with an arbitrary target:
        {
            "upload": "/api/upload",
            "query": "/api/query",
            "extracted": "/api/extracted",
            "chunks": "/api/chunks",
            "reset": "/api/reset",
        }
    """

    def __init__(
        self,
        base_url: str,
        url_map: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        upload_field: str = "file",
        query_param: str = "question",
    ):
        self.base_url = base_url.rstrip("/")
        self.url_map = url_map or {
            "upload": "/upload",
            "query": "/ask",
            "extracted": "/extracted",
            "chunks": "/chunks",
            "reset": "/reset",
        }
        self.upload_field = upload_field
        self.query_param = query_param
        self.client = httpx.Client(
            base_url=self.base_url, headers=headers or {}, timeout=300.0
        )

    def upload(self, file_path: Path) -> UploadResult:
        with file_path.open("rb") as f:
            response = self.client.post(
                self.url_map["upload"],
                files={self.upload_field: (file_path.name, f)},
            )
        response.raise_for_status()
        data = response.json()
        return UploadResult(
            filename=data.get("filename", file_path.name),
            extracted_length=data.get("extracted_length", 0),
            num_chunks=data.get("num_chunks", 0),
            raw_response=data,
        )

    def query(self, question: str) -> QueryResult:
        response = self.client.post(
            self.url_map["query"], params={self.query_param: question}
        )
        response.raise_for_status()
        data = response.json()
        return QueryResult(
            answer=data.get("answer", ""),
            context_chunks=data.get("context_chunks", []),
            model=data.get("model"),
            prompt=data.get("prompt"),
            raw_response=data,
        )

    def get_extracted_text(self) -> str:
        response = self.client.get(self.url_map["extracted"])
        response.raise_for_status()
        return response.json().get("extracted_text", "")

    def get_chunks(self) -> list[str]:
        response = self.client.get(self.url_map["chunks"])
        response.raise_for_status()
        return response.json().get("chunks", [])

    def reset(self) -> None:
        response = self.client.post(self.url_map["reset"])
        response.raise_for_status()

    def close(self) -> None:
        self.client.close()
