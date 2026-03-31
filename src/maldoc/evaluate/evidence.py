"""Evidence capture models."""

from datetime import datetime

from pydantic import BaseModel


class ExtractionEvidence(BaseModel):
    """Evidence from the document extraction stage."""

    extracted_text: str
    payload_found_in_text: bool
    payload_fragments: list[str]


class ChunkEvidence(BaseModel):
    """Evidence from the chunking stage."""

    chunks: list[str]
    num_chunks: int
    chunks_containing_payload: list[int]


class RetrievalEvidence(BaseModel):
    """Evidence from the retrieval stage."""

    query: str
    retrieved_chunks: list[str]
    payload_found_in_retrieval: bool


class ResponseEvidence(BaseModel):
    """Evidence from the final LLM response."""

    query: str
    prompt_sent: str | None = None
    response: str
    payload_influenced_response: bool
    influence_indicators: list[str]


class EvaluationResult(BaseModel):
    """Complete evaluation result with all evidence."""

    attack_name: str
    document_format: str
    document_path: str
    extraction: ExtractionEvidence
    chunking: ChunkEvidence
    retrieval: RetrievalEvidence
    response: ResponseEvidence
    scores: dict[str, float | None]
    score_justifications: dict[str, str] = {}


class ConsolidatedReport(BaseModel):
    """Consolidated report containing multiple evaluation results."""

    timestamp: datetime
    target: str
    results: list[EvaluationResult]
    cli_commands: list[str] = []

    @property
    def attacks(self) -> list[str]:
        return sorted(set(r.attack_name for r in self.results))

    @property
    def formats(self) -> list[str]:
        return sorted(set(r.document_format for r in self.results))

    @property
    def test_label(self) -> str:
        """Label for filename: attack name if single, 'multiple' if many."""
        attacks = self.attacks
        if len(attacks) == 1:
            return attacks[0]
        return "multiple"
