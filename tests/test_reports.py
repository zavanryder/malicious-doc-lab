"""Unit tests for report generation."""

import json
import re
from datetime import datetime

import pytest

from maldoc.evaluate.evidence import (
    ChunkEvidence,
    ConsolidatedReport,
    EvaluationResult,
    ExtractionEvidence,
    ResponseEvidence,
    RetrievalEvidence,
)
from maldoc.report.json_report import generate_json_report, report_filename
from maldoc.report.markdown_report import generate_markdown_report


@pytest.fixture
def evaluation_result():
    return EvaluationResult(
        attack_name="hidden_text",
        document_format="pdf",
        document_path="output/malicious_hidden_text.pdf",
        extraction=ExtractionEvidence(
            extracted_text="some extracted text with IGNORE in it",
            payload_found_in_text=True,
            payload_fragments=["IGNORE"],
        ),
        chunking=ChunkEvidence(
            chunks=["chunk1", "chunk2 IGNORE"],
            num_chunks=2,
            chunks_containing_payload=[1],
        ),
        retrieval=RetrievalEvidence(
            query="What are the instructions?",
            retrieved_chunks=["chunk2 IGNORE"],
            payload_found_in_retrieval=True,
        ),
        response=ResponseEvidence(
            query="What are the instructions?",
            response="ACCESS GRANTED",
            payload_influenced_response=True,
            influence_indicators=["phrase_detected: access granted"],
        ),
        scores={
            "extraction_survival": 0.33,
            "chunk_survival": 0.5,
            "retrieval_influence": 1.0,
            "response_influence": 0.33,
        },
    )


@pytest.fixture
def consolidated_report(evaluation_result):
    return ConsolidatedReport(
        timestamp=datetime(2026, 3, 29, 14, 30, 0),
        target="demo",
        results=[evaluation_result],
    )


@pytest.fixture
def multi_result_report(evaluation_result):
    second = evaluation_result.model_copy(
        update={"attack_name": "metadata", "document_format": "docx"}
    )
    return ConsolidatedReport(
        timestamp=datetime(2026, 3, 29, 14, 30, 0),
        target="demo",
        results=[evaluation_result, second],
    )


class TestReportFilename:
    def test_single_attack(self, consolidated_report):
        name = report_filename(consolidated_report)
        assert "20260329_143000" in name
        assert "demo" in name
        assert "hidden_text" in name

    def test_multiple_attacks(self, multi_result_report):
        name = report_filename(multi_result_report)
        assert "multiple" in name
        assert "demo" in name

    def test_filename_contract(self, consolidated_report):
        name = report_filename(consolidated_report)
        assert re.fullmatch(
            r"\d{8}_\d{6}_[a-zA-Z0-9_.-]+_[a-zA-Z0-9_.-]+_report",
            name,
        )


class TestJsonReport:
    def test_creates_file(self, consolidated_report, tmp_path):
        path = tmp_path / "report.json"
        result = generate_json_report(consolidated_report, path)
        assert result.exists()

    def test_valid_json(self, consolidated_report, tmp_path):
        path = tmp_path / "report.json"
        generate_json_report(consolidated_report, path)
        data = json.loads(path.read_text())
        assert data["target"] == "demo"
        assert len(data["results"]) == 1
        assert data["results"][0]["attack_name"] == "hidden_text"

    def test_roundtrip(self, consolidated_report, tmp_path):
        path = tmp_path / "report.json"
        generate_json_report(consolidated_report, path)
        loaded = ConsolidatedReport.model_validate_json(path.read_text())
        assert loaded.target == consolidated_report.target
        assert len(loaded.results) == len(consolidated_report.results)

    def test_multi_result_roundtrip(self, multi_result_report, tmp_path):
        path = tmp_path / "report.json"
        generate_json_report(multi_result_report, path)
        loaded = ConsolidatedReport.model_validate_json(path.read_text())
        assert len(loaded.results) == 2


class TestMarkdownReport:
    def test_creates_file(self, consolidated_report, tmp_path):
        path = tmp_path / "report.md"
        result = generate_markdown_report(consolidated_report, path)
        assert result.exists()

    def test_contains_header(self, consolidated_report, tmp_path):
        path = tmp_path / "report.md"
        generate_markdown_report(consolidated_report, path)
        content = path.read_text()
        assert "# Evaluation Report" in content
        assert "demo" in content

    def test_contains_summary_table(self, consolidated_report, tmp_path):
        path = tmp_path / "report.md"
        generate_markdown_report(consolidated_report, path)
        content = path.read_text()
        assert "## All Results" in content
        assert "| Attack |" in content
        assert "hidden_text" in content

    def test_contains_detailed_results(self, consolidated_report, tmp_path):
        path = tmp_path / "report.md"
        generate_markdown_report(consolidated_report, path)
        content = path.read_text()
        assert "## Detailed Results" in content
        assert "### hidden_text / pdf" in content

    def test_contains_raw_response(self, consolidated_report, tmp_path):
        path = tmp_path / "report.md"
        generate_markdown_report(consolidated_report, path)
        content = path.read_text()
        assert "ACCESS GRANTED" in content

    def test_multi_result_report(self, multi_result_report, tmp_path):
        path = tmp_path / "report.md"
        generate_markdown_report(multi_result_report, path)
        content = path.read_text()
        assert "### hidden_text / pdf" in content
        assert "### metadata / docx" in content
        assert "Tests run**: 2" in content

    def test_attack_summary_present_for_multi_attack(self, multi_result_report, tmp_path):
        path = tmp_path / "report.md"
        generate_markdown_report(multi_result_report, path)
        content = path.read_text()
        assert "## Attack Summary" in content
        assert "hidden_text" in content
        assert "metadata" in content

    def test_attack_summary_absent_for_single_attack(self, consolidated_report, tmp_path):
        path = tmp_path / "report.md"
        generate_markdown_report(consolidated_report, path)
        content = path.read_text()
        assert "## Attack Summary" not in content

    def test_appendix_present_when_commands_set(self, tmp_path):
        from maldoc.evaluate.evidence import ConsolidatedReport

        report = ConsolidatedReport(
            timestamp=datetime(2026, 3, 29, 14, 30, 0),
            target="demo",
            results=[],
            cli_commands=["uv sync", "uv run maldoc run --attack hidden_text --format pdf"],
        )
        path = tmp_path / "report.md"
        generate_markdown_report(report, path)
        content = path.read_text()
        assert "## Appendix: CLI Commands" in content
        assert "uv sync" in content
        assert "uv run maldoc run --attack hidden_text --format pdf" in content

    def test_appendix_absent_when_no_commands(self, consolidated_report, tmp_path):
        path = tmp_path / "report.md"
        generate_markdown_report(consolidated_report, path)
        content = path.read_text()
        assert "## Appendix: CLI Commands" not in content

    def test_black_box_none_scores_show_na(self, tmp_path):
        result = EvaluationResult(
            attack_name="hidden_text",
            document_format="pdf",
            document_path="output/test.pdf",
            extraction=ExtractionEvidence(
                extracted_text="",
                payload_found_in_text=False,
                payload_fragments=[],
            ),
            chunking=ChunkEvidence(
                chunks=[], num_chunks=0, chunks_containing_payload=[]
            ),
            retrieval=RetrievalEvidence(
                query="q",
                retrieved_chunks=["chunk"],
                payload_found_in_retrieval=True,
            ),
            response=ResponseEvidence(
                query="q",
                response="ACCESS GRANTED",
                payload_influenced_response=True,
                influence_indicators=["phrase_detected: access granted"],
            ),
            scores={
                "extraction_survival": None,
                "chunk_survival": None,
                "retrieval_influence": 1.0,
                "response_influence": 0.33,
            },
            score_justifications={
                "extraction_survival": "Evidence not available (black-box mode)",
                "chunk_survival": "Evidence not available (black-box mode)",
            },
        )
        report = ConsolidatedReport(
            timestamp=datetime(2026, 3, 30, 12, 0, 0),
            target="chatbot",
            results=[result],
        )
        path = tmp_path / "report.md"
        generate_markdown_report(report, path)
        content = path.read_text()
        assert "N/A" in content
        assert "black-box" in content

    def test_json_roundtrip_with_none_scores(self, tmp_path):
        result = EvaluationResult(
            attack_name="hidden_text",
            document_format="pdf",
            document_path="output/test.pdf",
            extraction=ExtractionEvidence(
                extracted_text="", payload_found_in_text=False, payload_fragments=[]
            ),
            chunking=ChunkEvidence(
                chunks=[], num_chunks=0, chunks_containing_payload=[]
            ),
            retrieval=RetrievalEvidence(
                query="q", retrieved_chunks=[], payload_found_in_retrieval=False
            ),
            response=ResponseEvidence(
                query="q", response="ok", payload_influenced_response=False,
                influence_indicators=[],
            ),
            scores={
                "extraction_survival": None,
                "chunk_survival": None,
                "retrieval_influence": 0.0,
                "response_influence": 0.0,
            },
        )
        report = ConsolidatedReport(
            timestamp=datetime(2026, 3, 30, 12, 0, 0),
            target="chatbot",
            results=[result],
        )
        path = tmp_path / "report.json"
        generate_json_report(report, path)
        loaded = ConsolidatedReport.model_validate_json(path.read_text())
        assert loaded.results[0].scores["extraction_survival"] is None
        assert loaded.results[0].scores["chunk_survival"] is None
        assert loaded.results[0].scores["retrieval_influence"] == 0.0
