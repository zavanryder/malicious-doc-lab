"""Plain-text document generation."""

from pathlib import Path

from maldoc.attacks.base import AttackResult


def generate_txt(attack_result: AttackResult, title: str, output_path: Path) -> Path:
    """Generate a text document containing attack content."""
    lines = [
        title,
        "=" * len(title),
        "",
        attack_result.visible_content,
    ]

    hints = attack_result.format_hints or {}
    if hints.get("obfuscated_variants"):
        lines.extend(
            [
                "",
                "[encoded_variants]",
                *hints["obfuscated_variants"],
            ]
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))
    return output_path
