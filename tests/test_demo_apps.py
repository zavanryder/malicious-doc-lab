"""Structural tests for demo app behavior that do not need Docker or Ollama."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_APP = REPO_ROOT / "demo" / "app.py"
CHATBOT_APP = REPO_ROOT / "demo-chatbot" / "app.py"


def test_demo_app_uses_threadpool_for_blocking_calls():
    content = DEMO_APP.read_text()
    assert "from starlette.concurrency import run_in_threadpool" in content
    assert "await run_in_threadpool(ingest, contents, file.filename)" in content
    assert "await run_in_threadpool(query_documents, question)" in content
    assert "ollama_client.chat" in content


def test_chatbot_app_uses_threadpool_for_blocking_calls():
    content = CHATBOT_APP.read_text()
    assert "from starlette.concurrency import run_in_threadpool" in content
    assert "await run_in_threadpool(ingest, contents, file.filename)" in content
    assert "await run_in_threadpool(query_documents, query_text)" in content
    assert "ollama_client.chat" in content


def test_chatbot_reset_route_is_not_gated_by_black_box_block():
    content = CHATBOT_APP.read_text()
    reset_index = content.index('@app.post("/reset")')
    black_box_index = content.index("if not BLACK_BOX:")
    assert reset_index < black_box_index
