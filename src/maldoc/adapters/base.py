"""Base adapter interface for target systems."""

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel


class UploadResult(BaseModel):
    """Result of uploading a document to a target."""

    filename: str
    extracted_length: int
    num_chunks: int
    raw_response: dict | None = None


class QueryResult(BaseModel):
    """Result of querying a target."""

    answer: str
    context_chunks: list[str]
    model: str | None = None
    prompt: str | None = None
    raw_response: dict | None = None


class BaseAdapter(ABC):
    """Abstract base for target adapters."""

    @abstractmethod
    def upload(self, file_path: Path) -> UploadResult:
        """Upload a document to the target."""
        ...

    @abstractmethod
    def query(self, question: str) -> QueryResult:
        """Query the target with a question."""
        ...

    @abstractmethod
    def get_extracted_text(self) -> str:
        """Get the raw extracted text from the last upload."""
        ...

    @abstractmethod
    def get_chunks(self) -> list[str]:
        """Get the chunks from the last upload."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Clear all ingested data on the target."""
        ...

    def close(self) -> None:
        """Release adapter resources."""
        return None
