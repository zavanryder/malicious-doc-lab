"""Image-based hidden text generation with Pillow."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from maldoc.attacks.base import AttackResult


def generate_image(attack_result: AttackResult, title: str, output_path: Path) -> Path:
    """Generate an image with hidden text payload."""
    width, height = 800, 600
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # Use default font
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_hidden = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 2)
    except OSError:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_hidden = ImageFont.load_default()

    # Title
    draw.text((30, 20), title, fill="black", font=font_title)

    # Visible body (truncated to fit)
    body = attack_result.visible_content[:500]
    draw.text((30, 70), body, fill="black", font=font_body)

    # OCR bait: light gray text on light background, small but readable by OCR
    if attack_result.technique == "ocr_bait":
        try:
            ocr_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 6)
        except OSError:
            ocr_font = ImageFont.load_default()
        draw.text((30, height - 40), attack_result.hidden_content, fill="#E0E0E0", font=ocr_font)
    elif attack_result.technique == "visual_scaling_injection":
        hints = attack_result.format_hints or {}
        # Decoy region that appears benign at normal size.
        draw.rectangle((25, height - 140, width - 25, height - 20), fill="#2E2E2E")
        draw.text((35, height - 130), hints.get("decoy_text", "Reference chart"), fill="#A0A0A0", font=font_body)
        try:
            scale_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
        except OSError:
            scale_font = ImageFont.load_default()
        # Low-contrast payload intended to become more legible after transformations.
        draw.text((35, height - 45), attack_result.hidden_content, fill="#3A3A3A", font=scale_font)
    else:
        # Default: white on white, tiny font at bottom
        draw.text((30, height - 20), attack_result.hidden_content, fill="white", font=font_hidden)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path))
    return output_path
