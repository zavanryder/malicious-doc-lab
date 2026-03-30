"""Unit tests for document generators."""

import csv
from pathlib import Path

import pytest

from maldoc.attacks.base import AttackResult
from maldoc.generate import generate_document, list_formats
from maldoc.generate.csv_gen import generate_csv
from maldoc.generate.docx import generate_docx
from maldoc.generate.eml import generate_eml
from maldoc.generate.html import generate_html, generate_markdown
from maldoc.generate.image import generate_image
from maldoc.generate.pptx_gen import generate_pptx
from maldoc.generate.pdf import generate_pdf
from maldoc.generate.txt_gen import generate_txt
from maldoc.generate.xlsx import generate_xlsx


@pytest.fixture
def attack_result():
    return AttackResult(
        visible_content="This is visible content for testing.",
        hidden_content="SECRET PAYLOAD",
        technique="hidden_text",
        format_hints={"font_size_zero_text": "SECRET PAYLOAD"},
    )


@pytest.fixture
def white_on_white_result():
    return AttackResult(
        visible_content="This is visible content for testing.",
        hidden_content="SECRET PAYLOAD",
        technique="white_on_white",
        format_hints={"hidden_font_color": "#FFFFFF"},
    )


@pytest.fixture
def metadata_result():
    return AttackResult(
        visible_content="This is visible content for testing.",
        hidden_content="SECRET PAYLOAD",
        technique="metadata",
        metadata={"author": "SECRET PAYLOAD", "subject": "SECRET PAYLOAD", "keywords": "SECRET PAYLOAD"},
        format_hints={"inject_metadata": True},
    )


class TestListFormats:
    def test_all_formats_present(self):
        formats = list_formats()
        assert set(formats) == {
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
            "xlsx",
            "pptx",
            "eml",
        }


class TestGenerateDocument:
    def test_unknown_format(self, attack_result):
        with pytest.raises(ValueError, match="Unknown format"):
            generate_document(attack_result, "Test", "odt")

    def test_generate_pdf(self, attack_result, tmp_path):
        path = generate_document(attack_result, "Test", "pdf", str(tmp_path))
        assert path.exists()
        assert path.suffix == ".pdf"
        assert path.stat().st_size > 0

    def test_generate_docx(self, attack_result, tmp_path):
        path = generate_document(attack_result, "Test", "docx", str(tmp_path))
        assert path.exists()
        assert path.suffix == ".docx"

    def test_generate_html(self, attack_result, tmp_path):
        path = generate_document(attack_result, "Test", "html", str(tmp_path))
        assert path.exists()
        content = path.read_text()
        assert "<html>" in content

    def test_generate_md(self, attack_result, tmp_path):
        path = generate_document(attack_result, "Test", "md", str(tmp_path))
        assert path.exists()
        content = path.read_text()
        assert "# Test" in content

    def test_generate_txt(self, attack_result, tmp_path):
        path = generate_document(attack_result, "Test", "txt", str(tmp_path))
        assert path.exists()
        assert path.suffix == ".txt"

    def test_generate_csv(self, attack_result, tmp_path):
        path = generate_document(attack_result, "Test", "csv", str(tmp_path))
        assert path.exists()
        assert path.suffix == ".csv"

    def test_generate_image(self, attack_result, tmp_path):
        path = generate_document(attack_result, "Test", "image", str(tmp_path))
        assert path.exists()
        assert path.suffix == ".png"

    def test_generate_png_alias(self, attack_result, tmp_path):
        path = generate_document(attack_result, "Test", "png", str(tmp_path))
        assert path.exists()
        assert path.suffix == ".png"

    def test_generate_jpg_alias(self, attack_result, tmp_path):
        path = generate_document(attack_result, "Test", "jpg", str(tmp_path))
        assert path.exists()
        assert path.suffix == ".jpg"

    def test_generate_eml(self, attack_result, tmp_path):
        path = generate_document(attack_result, "Test", "eml", str(tmp_path))
        assert path.exists()
        assert path.suffix == ".eml"

    def test_generate_xlsx(self, attack_result, tmp_path):
        pytest.importorskip("openpyxl")
        path = generate_document(attack_result, "Test", "xlsx", str(tmp_path))
        assert path.exists()
        assert path.suffix == ".xlsx"

    def test_generate_pptx(self, attack_result, tmp_path):
        pytest.importorskip("pptx")
        path = generate_document(attack_result, "Test", "pptx", str(tmp_path))
        assert path.exists()
        assert path.suffix == ".pptx"


class TestPdfGenerator:
    def test_creates_file(self, attack_result, tmp_path):
        path = tmp_path / "test.pdf"
        result = generate_pdf(attack_result, "Test Title", path)
        assert result.exists()
        assert result.stat().st_size > 100

    def test_white_on_white(self, white_on_white_result, tmp_path):
        path = tmp_path / "test.pdf"
        result = generate_pdf(white_on_white_result, "Test", path)
        assert result.exists()

    def test_metadata_injection(self, metadata_result, tmp_path):
        path = tmp_path / "test.pdf"
        result = generate_pdf(metadata_result, "Test", path)
        assert result.exists()

    def test_hidden_text_applies_font_size_zero_hint(self, tmp_path, monkeypatch):
        class FakePdf:
            def __init__(self):
                self.multi_cell_calls = []
                self.l_margin = 10

            def add_page(self):
                return None

            def set_auto_page_break(self, auto, margin):
                return None

            def add_font(self, family, style, path):
                return None

            def set_author(self, value):
                return None

            def set_subject(self, value):
                return None

            def set_keywords(self, value):
                return None

            def set_font(self, family, style, size):
                return None

            def cell(self, w, h, text, new_x=None, new_y=None):
                return None

            def ln(self, h=None):
                return None

            def set_text_color(self, r, g, b):
                return None

            def multi_cell(self, w, h, text):
                self.multi_cell_calls.append(text)

            def write(self, h, text):
                self.multi_cell_calls.append(text)

            def set_xy(self, x, y):
                return None

            def set_x(self, x):
                return None

            def output(self, path):
                Path(path).write_text("fake pdf")

        fake_pdf = FakePdf()
        monkeypatch.setattr("maldoc.generate.pdf.FPDF", lambda: fake_pdf)

        hidden_result = AttackResult(
            visible_content="visible only",
            hidden_content="SECRET PAYLOAD",
            technique="hidden_text",
            format_hints={"font_size_zero_text": "SECRET PAYLOAD"},
        )
        out = tmp_path / "test.pdf"
        generate_pdf(hidden_result, "Test", out)

        assert any("SECRET PAYLOAD" in text for text in fake_pdf.multi_cell_calls)


class TestDocxGenerator:
    def test_creates_file(self, attack_result, tmp_path):
        path = tmp_path / "test.docx"
        result = generate_docx(attack_result, "Test Title", path)
        assert result.exists()
        assert result.stat().st_size > 100

    def test_white_on_white(self, white_on_white_result, tmp_path):
        path = tmp_path / "test.docx"
        result = generate_docx(white_on_white_result, "Test", path)
        assert result.exists()

    def test_metadata_injection(self, metadata_result, tmp_path):
        from docx import Document

        path = tmp_path / "test.docx"
        generate_docx(metadata_result, "Test", path)
        doc = Document(str(path))
        assert doc.core_properties.author == "SECRET PAYLOAD"


class TestHtmlGenerator:
    def test_creates_file(self, attack_result, tmp_path):
        path = tmp_path / "test.html"
        result = generate_html(attack_result, "Test Title", path)
        assert result.exists()
        content = path.read_text()
        assert "Test Title" in content
        assert "visible content" in content

    def test_white_on_white_has_hidden_span(self, white_on_white_result, tmp_path):
        path = tmp_path / "test.html"
        generate_html(white_on_white_result, "Test", path)
        content = path.read_text()
        assert "color:#fff" in content
        assert "SECRET PAYLOAD" in content

    def test_metadata_has_meta_tags(self, metadata_result, tmp_path):
        path = tmp_path / "test.html"
        generate_html(metadata_result, "Test", path)
        content = path.read_text()
        assert '<meta name="author"' in content


class TestMarkdownGenerator:
    def test_creates_file(self, attack_result, tmp_path):
        path = tmp_path / "test.md"
        result = generate_markdown(attack_result, "Test Title", path)
        assert result.exists()
        content = path.read_text()
        assert "# Test Title" in content


class TestImageGenerator:
    def test_creates_file(self, attack_result, tmp_path):
        path = tmp_path / "test.png"
        result = generate_image(attack_result, "Test Title", path)
        assert result.exists()
        assert result.stat().st_size > 100


class TestCsvGenerator:
    def test_creates_file(self, attack_result, tmp_path):
        path = tmp_path / "test.csv"
        result = generate_csv(attack_result, "Test Title", path)
        assert result.exists()

    def test_contains_payload(self, attack_result, tmp_path):
        path = tmp_path / "test.csv"
        generate_csv(attack_result, "Test", path)
        with path.open() as f:
            reader = csv.reader(f)
            rows = list(reader)
        # Last row should contain the hidden payload
        all_text = " ".join(" ".join(row) for row in rows)
        assert "SECRET PAYLOAD" in all_text


class TestTxtGenerator:
    def test_creates_file(self, attack_result, tmp_path):
        path = tmp_path / "test.txt"
        result = generate_txt(attack_result, "Test Title", path)
        assert result.exists()
        assert "Test Title" in result.read_text()


class TestEmlGenerator:
    def test_creates_file(self, attack_result, tmp_path):
        path = tmp_path / "test.eml"
        result = generate_eml(attack_result, "Test Title", path)
        assert result.exists()
        assert b"Subject: Test Title" in result.read_bytes()


class TestXlsxGenerator:
    def test_creates_file(self, attack_result, tmp_path):
        pytest.importorskip("openpyxl")
        path = tmp_path / "test.xlsx"
        result = generate_xlsx(attack_result, "Test Title", path)
        assert result.exists()
        assert result.stat().st_size > 0


class TestPptxGenerator:
    def test_creates_file(self, attack_result, tmp_path):
        pytest.importorskip("pptx")
        path = tmp_path / "test.pptx"
        result = generate_pptx(attack_result, "Test Title", path)
        assert result.exists()
        assert result.stat().st_size > 0
