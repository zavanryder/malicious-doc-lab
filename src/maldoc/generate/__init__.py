"""Document generation modules."""

from pathlib import Path

from maldoc.attacks.base import AttackResult
from maldoc.coverage import assess_attack_format
from maldoc.generate.csv_gen import generate_csv
from maldoc.generate.docx import generate_docx
from maldoc.generate.eml import generate_eml
from maldoc.generate.html import generate_html, generate_markdown
from maldoc.generate.image import generate_image
from maldoc.generate.pptx_gen import generate_pptx
from maldoc.generate.pdf import generate_pdf
from maldoc.generate.txt_gen import generate_txt
from maldoc.generate.xlsx import generate_xlsx

FORMAT_GENERATORS = {
    "pdf": (generate_pdf, ".pdf"),
    "docx": (generate_docx, ".docx"),
    "html": (generate_html, ".html"),
    "md": (generate_markdown, ".md"),
    "txt": (generate_txt, ".txt"),
    "csv": (generate_csv, ".csv"),
    "image": (generate_image, ".png"),
    "png": (generate_image, ".png"),
    "jpg": (generate_image, ".jpg"),
    "jpeg": (generate_image, ".jpeg"),
    "xlsx": (generate_xlsx, ".xlsx"),
    "pptx": (generate_pptx, ".pptx"),
    "eml": (generate_eml, ".eml"),
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

    allowed, _degraded, message = assess_attack_format(attack_result.technique, fmt)
    if not allowed:
        raise ValueError(message)

    generator_fn, ext = FORMAT_GENERATORS[fmt]
    filename = f"malicious_{attack_result.technique}{ext}"
    output_path = Path(output_dir) / filename
    return generator_fn(attack_result, title, output_path)


def list_formats() -> list[str]:
    """Return list of available format names."""
    return list(FORMAT_GENERATORS.keys())
