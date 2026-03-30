"""Document generation modules."""

from pathlib import Path

from maldoc.attacks.base import AttackResult
from maldoc.generate.csv_gen import generate_csv
from maldoc.generate.docx import generate_docx
from maldoc.generate.html import generate_html, generate_markdown
from maldoc.generate.image import generate_image
from maldoc.generate.pdf import generate_pdf

FORMAT_GENERATORS = {
    "pdf": (generate_pdf, ".pdf"),
    "docx": (generate_docx, ".docx"),
    "html": (generate_html, ".html"),
    "md": (generate_markdown, ".md"),
    "csv": (generate_csv, ".csv"),
    "image": (generate_image, ".png"),
}


def generate_document(
    attack_result: AttackResult,
    title: str,
    fmt: str,
    output_dir: str = "output",
) -> Path:
    """Generate a document in the specified format."""
    if fmt not in FORMAT_GENERATORS:
        available = ", ".join(FORMAT_GENERATORS.keys())
        raise ValueError(f"Unknown format '{fmt}'. Available: {available}")

    generator_fn, ext = FORMAT_GENERATORS[fmt]
    filename = f"malicious_{attack_result.technique}{ext}"
    output_path = Path(output_dir) / filename
    return generator_fn(attack_result, title, output_path)


def list_formats() -> list[str]:
    """Return list of available format names."""
    return list(FORMAT_GENERATORS.keys())
