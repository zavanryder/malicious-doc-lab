"""PDF document generation with fpdf2."""

from pathlib import Path

from fpdf import FPDF

from maldoc.attacks.base import AttackResult


def generate_pdf(attack_result: AttackResult, title: str, output_path: Path) -> Path:
    """Generate a PDF containing the attack payload."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    hints = attack_result.format_hints or {}

    # Use a TTF font for Unicode support
    ttf_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ttf_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        pdf.add_font("DejaVu", "", ttf_path)
        pdf.add_font("DejaVu", "B", ttf_bold_path)
        font_family = "DejaVu"
    except (RuntimeError, OSError):
        font_family = "Helvetica"

    # Metadata injection
    if attack_result.metadata:
        pdf.set_author(attack_result.metadata.get("author", ""))
        pdf.set_subject(attack_result.metadata.get("subject", ""))
        pdf.set_keywords(attack_result.metadata.get("keywords", ""))

    # Title
    pdf.set_font(font_family, "B", 16)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Visible body
    pdf.set_font(font_family, "", 11)
    pdf.multi_cell(0, 6, attack_result.visible_content)

    # White-on-white: append hidden text in white
    if attack_result.technique == "white_on_white":
        pdf.ln(5)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(font_family, "", 1)
        pdf.multi_cell(0, 1, attack_result.hidden_content)
        pdf.set_text_color(0, 0, 0)

    # Font-size-zero hidden text fallback for techniques that include this hint.
    if hints.get("font_size_zero_text"):
        pdf.set_font(font_family, "", 4)
        pdf.set_text_color(255, 255, 255)
        pdf.set_x(pdf.l_margin)
        pdf.write(3, hints["font_size_zero_text"])
        pdf.set_text_color(0, 0, 0)

    # Off-page text: render payload outside the visible page area
    if attack_result.technique == "off_page":
        pdf.set_font(font_family, "", 8)
        pdf.set_text_color(0, 0, 0)
        # Write text at negative coordinates (off-page to the left/above)
        pdf.set_xy(-200, -200)
        pdf.cell(0, 5, attack_result.hidden_content)

    # OCR bait: embed payload as a near-invisible image-like text block
    if attack_result.technique == "ocr_bait":
        pdf.ln(10)
        pdf.set_font(font_family, "", 4)
        pdf.set_text_color(224, 224, 224)
        pdf.multi_cell(0, 3, attack_result.hidden_content)
        pdf.set_text_color(0, 0, 0)

    # Visual scaling injection: low-contrast payload inside a dense footer block.
    if attack_result.technique == "visual_scaling_injection":
        hints = attack_result.format_hints or {}
        pdf.ln(8)
        pdf.set_x(pdf.l_margin)
        pdf.set_font(font_family, "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5, hints.get("decoy_text", "Reference visualization"))
        pdf.set_x(pdf.l_margin)
        pdf.set_font(font_family, "", 6)
        pdf.set_text_color(75, 75, 75)
        pdf.multi_cell(0, 3, attack_result.hidden_content)
        pdf.set_text_color(0, 0, 0)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path
