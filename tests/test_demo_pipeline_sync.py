"""Guardrail tests for the shared demo pipeline structure."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_PIPELINE = REPO_ROOT / "demo" / "pipeline.py"
CHATBOT_PIPELINE = REPO_ROOT / "demo-chatbot" / "pipeline.py"
SHARED_PIPELINE = REPO_ROOT / "shared_pipeline.py"


def test_demo_and_chatbot_pipelines_use_shared_pipeline_module():
    demo_text = DEMO_PIPELINE.read_text()
    chatbot_text = CHATBOT_PIPELINE.read_text()

    assert "from shared_pipeline import PipelineState" in demo_text
    assert "from shared_pipeline import PipelineState" in chatbot_text
    assert "PipelineState(" in demo_text
    assert "PipelineState(" in chatbot_text


def test_shared_pipeline_exists():
    assert SHARED_PIPELINE.exists()
