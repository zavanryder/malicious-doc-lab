"""CSV payload generation."""

import csv
from pathlib import Path

from maldoc.attacks.base import AttackResult


def generate_csv(attack_result: AttackResult, title: str, output_path: Path) -> Path:
    """Generate a CSV file with hidden payload in data cells."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Content", "Notes"])

        # Visible rows from body
        for i, line in enumerate(attack_result.visible_content.split("\n")):
            line = line.strip()
            if line:
                writer.writerow([f"Row {i + 1}", line, ""])

        # Hidden payload row — payload embedded in notes column
        writer.writerow(["", "", attack_result.hidden_content])

    return output_path
