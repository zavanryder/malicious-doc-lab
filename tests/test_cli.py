"""CLI smoke tests."""

from datetime import datetime
import importlib.util

from typer.testing import CliRunner

from maldoc.adapters.chatbot import ChatbotAdapter
from maldoc.attacks.base import AttackResult
from maldoc.cli import _get_adapter, _resolve_target_url, app
from maldoc.evaluate.evidence import (
    ChunkEvidence,
    EvaluationResult,
    ExtractionEvidence,
    ResponseEvidence,
    RetrievalEvidence,
)

runner = CliRunner()


def _sample_eval_result(
    attack_name: str = "hidden_text",
    fmt: str = "pdf",
) -> EvaluationResult:
    return EvaluationResult(
        attack_name=attack_name,
        document_format=fmt,
        document_path=f"output/{attack_name}.{fmt}",
        extraction=ExtractionEvidence(
            extracted_text="text",
            payload_found_in_text=True,
            payload_fragments=["IGNORE"],
        ),
        chunking=ChunkEvidence(
            chunks=["chunk"], num_chunks=1, chunks_containing_payload=[0]
        ),
        retrieval=RetrievalEvidence(
            query="q", retrieved_chunks=["chunk"], payload_found_in_retrieval=True
        ),
        response=ResponseEvidence(
            query="q",
            response="ACCESS GRANTED",
            payload_influenced_response=True,
            influence_indicators=["phrase_detected: access granted"],
        ),
        scores={
            "extraction_survival": 1.0,
            "chunk_survival": 1.0,
            "retrieval_influence": 1.0,
            "response_influence": 1.0,
        },
    )


class TestCli:
    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "generate" in result.output
        assert "evaluate" in result.output
        assert "run" in result.output

    def test_generate_help(self):
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--attack" in result.output

    def test_generate_hidden_text_pdf(self, tmp_path):
        result = runner.invoke(app, [
            "generate",
            "--attack", "hidden_text",
            "--format", "pdf",
            "--output-dir", str(tmp_path),
        ])
        assert result.exit_code == 0
        assert "Generated:" in result.output

    def test_generate_all_attacks(self, tmp_path):
        for attack in [
            "hidden_text", "white_on_white", "metadata", "retrieval_poison",
            "ocr_bait", "off_page", "chunk_split", "summary_steer",
            "delayed_trigger", "tool_routing",
            "encoding_obfuscation", "typoglycemia", "markdown_exfil",
            "visual_scaling_injection",
        ]:
            result = runner.invoke(app, [
                "generate",
                "--attack", attack,
                "--format", "pdf",
                "--output-dir", str(tmp_path),
            ])
            assert result.exit_code == 0, f"Failed for attack: {attack}"

    def test_generate_all_formats(self, tmp_path):
        formats = [
            "pdf",
            "docx",
            "html",
            "md",
            "txt",
            "csv",
            "image",
            "png",
            "jpg",
            "jpeg",
            "eml",
        ]
        if importlib.util.find_spec("openpyxl"):
            formats.append("xlsx")
        if importlib.util.find_spec("pptx"):
            formats.append("pptx")

        for fmt in formats:
            result = runner.invoke(app, [
                "generate",
                "--attack", "hidden_text",
                "--format", fmt,
                "--output-dir", str(tmp_path),
            ])
            assert result.exit_code == 0, f"Failed for format: {fmt}"

    def test_generate_custom_payload(self, tmp_path):
        result = runner.invoke(app, [
            "generate",
            "--attack", "hidden_text",
            "--format", "html",
            "--output-dir", str(tmp_path),
            "--payload", "CUSTOM ATTACK PAYLOAD",
        ])
        assert result.exit_code == 0

    def test_generate_unknown_attack(self, tmp_path):
        result = runner.invoke(app, [
            "generate",
            "--attack", "nonexistent",
            "--format", "pdf",
            "--output-dir", str(tmp_path),
        ])
        assert result.exit_code != 0

    def test_report_from_json(self, tmp_path):
        from maldoc.evaluate.evidence import (
            ChunkEvidence,
            ConsolidatedReport,
            EvaluationResult,
            ExtractionEvidence,
            ResponseEvidence,
            RetrievalEvidence,
        )

        eval_result = EvaluationResult(
            attack_name="test",
            document_format="pdf",
            document_path="test.pdf",
            extraction=ExtractionEvidence(
                extracted_text="text", payload_found_in_text=False, payload_fragments=[]
            ),
            chunking=ChunkEvidence(chunks=[], num_chunks=0, chunks_containing_payload=[]),
            retrieval=RetrievalEvidence(
                query="q", retrieved_chunks=[], payload_found_in_retrieval=False
            ),
            response=ResponseEvidence(
                query="q", response="a", payload_influenced_response=False, influence_indicators=[]
            ),
            scores={"extraction_survival": 0.0},
        )
        report = ConsolidatedReport(
            timestamp=datetime.now(),
            target="demo",
            results=[eval_result],
        )
        json_path = tmp_path / "eval.json"
        json_path.write_text(report.model_dump_json(indent=2))

        result = runner.invoke(app, [
            "report",
            "--input", str(json_path),
            "--format", "markdown",
            "--reports-dir", str(tmp_path),
        ])
        assert result.exit_code == 0
        assert "Report generated:" in result.output

    def test_report_rejects_invalid_format(self, tmp_path):
        from maldoc.evaluate.evidence import ConsolidatedReport

        report = ConsolidatedReport(
            timestamp=datetime.now(),
            target="demo",
            results=[_sample_eval_result()],
        )
        json_path = tmp_path / "eval.json"
        json_path.write_text(report.model_dump_json(indent=2))

        result = runner.invoke(app, [
            "report",
            "--input", str(json_path),
            "--format", "yaml",
            "--reports-dir", str(tmp_path),
        ])
        assert result.exit_code != 0
        assert "Invalid value for '--format'" in result.output

    def test_evaluate_uses_custom_payload(self, tmp_path, monkeypatch):
        captured = {}

        class FakeAttack:
            def default_payload(self):
                return "DEFAULT PAYLOAD"

            def apply(self, payload, template):
                captured["payload"] = payload
                return AttackResult(
                    visible_content="visible",
                    hidden_content=payload,
                    technique="hidden_text",
                )

        class FakeAdapter:
            def close(self):
                return None

        def fake_report_filename(_report):
            return "unit_test_report"

        monkeypatch.setattr("maldoc.attacks.get_attack", lambda _name: FakeAttack())
        monkeypatch.setattr("maldoc.cli._get_adapter", lambda _t, _u: FakeAdapter())
        monkeypatch.setattr(
            "maldoc.evaluate.runner.evaluate",
            lambda _adapter, _attack_result, _path, _query: _sample_eval_result(),
        )
        monkeypatch.setattr("maldoc.report.json_report.report_filename", fake_report_filename)
        monkeypatch.setattr(
            "maldoc.report.json_report.generate_json_report",
            lambda _report, path: path,
        )
        monkeypatch.setattr(
            "maldoc.report.markdown_report.generate_markdown_report",
            lambda _report, path: path,
        )

        doc_path = tmp_path / "doc.pdf"
        doc_path.write_text("doc")

        result = runner.invoke(app, [
            "evaluate",
            "--file", str(doc_path),
            "--attack", "hidden_text",
            "--payload", "CUSTOM PAYLOAD",
            "--reports-dir", str(tmp_path),
        ])

        assert result.exit_code == 0
        assert captured["payload"] == "CUSTOM PAYLOAD"

    def test_run_command_executes_pipeline(self, tmp_path, monkeypatch):
        class FakeAttack:
            def default_payload(self):
                return "DEFAULT PAYLOAD"

            def apply(self, payload, template):
                return AttackResult(
                    visible_content=f"visible {payload}",
                    hidden_content=payload,
                    technique="hidden_text",
                )

        class FakeAdapter:
            def close(self):
                return None

        monkeypatch.setattr("maldoc.attacks.get_attack", lambda _name: FakeAttack())
        monkeypatch.setattr("maldoc.cli._get_adapter", lambda _t, _u: FakeAdapter())
        monkeypatch.setattr(
            "maldoc.generate.generate_document",
            lambda _attack_result, _title, _fmt, _output_dir: tmp_path / "generated.pdf",
        )
        monkeypatch.setattr(
            "maldoc.evaluate.runner.evaluate",
            lambda _adapter, _attack_result, _path, _query: _sample_eval_result(),
        )
        monkeypatch.setattr("maldoc.report.json_report.report_filename", lambda _r: "run_report")
        monkeypatch.setattr(
            "maldoc.report.json_report.generate_json_report",
            lambda _report, path: path,
        )
        monkeypatch.setattr(
            "maldoc.report.markdown_report.generate_markdown_report",
            lambda _report, path: path,
        )

        result = runner.invoke(app, [
            "run",
            "--attack", "hidden_text",
            "--format", "pdf",
            "--output-dir", str(tmp_path),
            "--reports-dir", str(tmp_path),
        ])
        assert result.exit_code == 0
        assert "[1/1] hidden_text / pdf" in result.output

    def test_demo_invalid_action_fails(self):
        result = runner.invoke(app, ["demo", "unknown"])
        assert result.exit_code != 0
        assert "ACTION:{start|stop|reset}" in result.output

    def test_demo_start_uses_explicit_compose_file(self, tmp_path, monkeypatch):
        compose_path = tmp_path / "docker-compose.yml"
        compose_path.write_text("services: {}")
        called = {}

        def fake_run(command, check):
            called["command"] = command
            called["check"] = check
            return None

        monkeypatch.setattr("maldoc.cli._resolve_compose_file", lambda: compose_path)
        monkeypatch.setattr("subprocess.run", fake_run)

        result = runner.invoke(app, ["demo", "start"])

        assert result.exit_code == 0
        assert called["check"] is True
        assert called["command"][:4] == [
            "docker",
            "compose",
            "-f",
            str(compose_path),
        ]

    def test_get_adapter_chatbot(self):
        adapter = _get_adapter("chatbot", "http://localhost:8001")
        assert isinstance(adapter, ChatbotAdapter)
        assert adapter.base_url == "http://localhost:8001"
        adapter.close()

    def test_resolve_target_url_defaults(self):
        assert _resolve_target_url("demo", "") == "http://localhost:8000"
        assert _resolve_target_url("chatbot", "") == "http://localhost:8001"
        assert _resolve_target_url("http", "") == "http://localhost:8000"

    def test_resolve_target_url_explicit(self):
        assert _resolve_target_url("demo", "http://custom:9000") == "http://custom:9000"
        assert _resolve_target_url("chatbot", "http://custom:9001") == "http://custom:9001"

    def test_demo_start_starts_both_services(self, tmp_path, monkeypatch):
        compose_path = tmp_path / "docker-compose.yml"
        compose_path.write_text("services: {}")
        called = {}

        def fake_run(command, check):
            called["command"] = command
            return None

        monkeypatch.setattr("maldoc.cli._resolve_compose_file", lambda: compose_path)
        monkeypatch.setattr("subprocess.run", fake_run)

        result = runner.invoke(app, ["demo", "start"])

        assert result.exit_code == 0
        assert "demo-app" in called["command"]
        assert "demo-chatbot" in called["command"]
        assert "Demo-API" in result.output
        assert "Demo-Chatbot" in result.output
