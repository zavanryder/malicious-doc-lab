"""Unit tests for adapters."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from maldoc.adapters.base import BaseAdapter, QueryResult, UploadResult
from maldoc.adapters.chatbot import ChatbotAdapter
from maldoc.adapters.demo import DemoAdapter
from maldoc.adapters.http import HttpAdapter


class TestBaseAdapter:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseAdapter()


class TestDemoAdapter:
    def test_init_default_url(self):
        adapter = DemoAdapter()
        assert adapter.base_url == "http://localhost:8000"

    def test_init_custom_url(self):
        adapter = DemoAdapter(base_url="http://example.com:9000/")
        assert adapter.base_url == "http://example.com:9000"

    def test_upload(self, tmp_path, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:8000/upload",
            json={"filename": "test.pdf", "extracted_length": 100, "num_chunks": 5},
        )
        adapter = DemoAdapter()
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake pdf content")
        result = adapter.upload(test_file)
        assert isinstance(result, UploadResult)
        assert result.filename == "test.pdf"
        assert result.num_chunks == 5

    def test_query(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:8000/ask?question=test+question",
            json={"answer": "test answer", "context_chunks": ["chunk1"], "model": "llama3.2"},
        )
        adapter = DemoAdapter()
        result = adapter.query("test question")
        assert isinstance(result, QueryResult)
        assert result.answer == "test answer"

    def test_get_extracted_text(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:8000/extracted",
            json={"extracted_text": "some text"},
        )
        adapter = DemoAdapter()
        text = adapter.get_extracted_text()
        assert text == "some text"

    def test_get_chunks(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:8000/chunks",
            json={"chunks": ["a", "b"], "count": 2},
        )
        adapter = DemoAdapter()
        chunks = adapter.get_chunks()
        assert chunks == ["a", "b"]

    def test_reset(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:8000/reset",
            json={"status": "reset"},
        )
        adapter = DemoAdapter()
        adapter.reset()  # Should not raise

    def test_close(self):
        adapter = DemoAdapter()
        adapter.close()
        assert adapter.client.is_closed


class TestChatbotAdapter:
    def test_init_default_url(self):
        adapter = ChatbotAdapter()
        assert adapter.base_url == "http://localhost:8001"

    def test_init_custom_url(self):
        adapter = ChatbotAdapter(base_url="http://example.com:9001/")
        assert adapter.base_url == "http://example.com:9001"

    def test_upload_via_chat(self, tmp_path, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:8001/chat",
            json={
                "role": "assistant",
                "content": "Document analyzed.",
                "sources": [],
                "extracted_length": 200,
                "num_chunks": 4,
            },
        )
        adapter = ChatbotAdapter()
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake pdf content")
        result = adapter.upload(test_file)
        assert isinstance(result, UploadResult)
        assert result.filename == "test.pdf"
        assert result.extracted_length == 200
        assert result.num_chunks == 4

    def test_query_via_chat(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:8001/chat",
            json={
                "role": "assistant",
                "content": "The answer is 42.",
                "sources": ["chunk1", "chunk2"],
                "model": "llama3.2",
            },
        )
        adapter = ChatbotAdapter()
        result = adapter.query("What is the answer?")
        assert isinstance(result, QueryResult)
        assert result.answer == "The answer is 42."
        assert result.context_chunks == ["chunk1", "chunk2"]

    def test_get_extracted_text(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:8001/extracted",
            json={"extracted_text": "some text"},
        )
        adapter = ChatbotAdapter()
        text = adapter.get_extracted_text()
        assert text == "some text"
        assert not adapter._evidence_unavailable

    def test_get_extracted_text_black_box(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:8001/extracted",
            status_code=404,
        )
        adapter = ChatbotAdapter()
        text = adapter.get_extracted_text()
        assert text == ""
        assert adapter._evidence_unavailable

    def test_get_chunks_black_box(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:8001/chunks",
            status_code=404,
        )
        adapter = ChatbotAdapter()
        chunks = adapter.get_chunks()
        assert chunks == []
        assert adapter._evidence_unavailable

    def test_reset(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:8001/reset",
            json={"status": "reset"},
        )
        adapter = ChatbotAdapter()
        adapter.reset()  # Should not raise

    def test_reset_black_box(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:8001/reset",
            status_code=404,
        )
        adapter = ChatbotAdapter()
        adapter.reset()  # Should not raise

    def test_close(self):
        adapter = ChatbotAdapter()
        adapter.close()
        assert adapter.client.is_closed


class TestHttpAdapter:
    def test_init_defaults(self):
        adapter = HttpAdapter(base_url="http://example.com")
        assert adapter.base_url == "http://example.com"
        assert adapter.url_map["upload"] == "/upload"

    def test_custom_url_map(self):
        url_map = {"upload": "/api/v1/upload", "query": "/api/v1/query",
                    "extracted": "/api/v1/text", "chunks": "/api/v1/chunks",
                    "reset": "/api/v1/reset"}
        adapter = HttpAdapter(base_url="http://example.com", url_map=url_map)
        assert adapter.url_map["upload"] == "/api/v1/upload"

    def test_upload(self, tmp_path, httpx_mock):
        httpx_mock.add_response(
            url="http://example.com/upload",
            json={"filename": "test.pdf", "extracted_length": 50, "num_chunks": 2},
        )
        adapter = HttpAdapter(base_url="http://example.com")
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake content")
        result = adapter.upload(test_file)
        assert result.filename == "test.pdf"

    def test_close(self):
        adapter = HttpAdapter(base_url="http://example.com")
        adapter.close()
        assert adapter.client.is_closed
