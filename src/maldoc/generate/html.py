"""HTML and Markdown document generation."""

from pathlib import Path

from maldoc.attacks.base import AttackResult


def generate_html(attack_result: AttackResult, title: str, output_path: Path) -> Path:
    """Generate an HTML file containing the attack payload."""
    hints = attack_result.format_hints or {}
    hidden_css = ""

    if attack_result.technique == "white_on_white":
        hidden_css = (
            f'<span style="color:#fff;font-size:1px;">'
            f"{attack_result.hidden_content}</span>"
        )
    elif attack_result.technique == "off_page":
        hidden_css = (
            f'<div style="position:absolute;left:-9999px;top:-9999px;">'
            f"{attack_result.hidden_content}</div>"
        )
    elif attack_result.technique == "ocr_bait":
        hidden_css = (
            f'<span style="color:#e0e0e0;font-size:4px;background:#f0f0f0;">'
            f"{attack_result.hidden_content}</span>"
        )
    elif hints.get("font_size_zero_text"):
        hidden_css = (
            f'<span style="font-size:0;color:transparent;">'
            f"{hints['font_size_zero_text']}</span>"
        )

    # Metadata injection via meta tags
    meta_tags = ""
    if attack_result.metadata:
        for key, value in attack_result.metadata.items():
            meta_tags += f'  <meta name="{key}" content="{value}">\n'

    body = attack_result.visible_content.replace("\n", "<br>\n")

    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>{title}</title>
{meta_tags}</head>
<body>
  <h1>{title}</h1>
  <div>{body}</div>
  {hidden_css}
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    return output_path


def generate_markdown(
    attack_result: AttackResult, title: str, output_path: Path
) -> Path:
    """Generate a Markdown file containing the attack payload."""
    # Hidden content via HTML comment or zero-width chars (already in visible_content)
    hidden = ""
    if attack_result.technique in ("white_on_white", "metadata"):
        hidden = f"\n\n<!-- {attack_result.hidden_content} -->"

    md = f"# {title}\n\n{attack_result.visible_content}{hidden}\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md)
    return output_path
