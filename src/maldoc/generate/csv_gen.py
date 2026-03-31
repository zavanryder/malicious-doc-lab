"""CSV payload generation."""

import csv
from pathlib import Path

from maldoc.attacks.base import AttackResult


def generate_csv(attack_result: AttackResult, title: str, output_path: Path) -> Path:
    """Generate a CSV file with hidden payload in data cells."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    hints = attack_result.format_hints or {}

    with output_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Content", "Notes"])

        # Visible rows from body
        for i, line in enumerate(attack_result.visible_content.split("\n")):
            line = line.strip()
            if line:
                writer.writerow([f"Row {i + 1}", line, ""])

        # Preserve transformed carriers without leaking the literal payload.
        if hints.get("font_size_zero_text"):
            writer.writerow(["", "", hints["font_size_zero_text"]])
        elif hints.get("obfuscated_variants"):
            writer.writerow(["", "", hints["obfuscated_variants"][0]])
        elif hints.get("obfuscated_payload"):
            writer.writerow(["", "", hints["obfuscated_payload"]])

    return output_path
