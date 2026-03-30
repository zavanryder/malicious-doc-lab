"""JSON report output."""

from pathlib import Path

from maldoc.evaluate.evidence import ConsolidatedReport


def report_filename(report: ConsolidatedReport) -> str:
    """Generate a descriptive report filename.

    Format: {YYYYMMDD}_{HHMMSS}_{target}_{attack_or_multiple}_report
    """
    ts = report.timestamp.strftime("%Y%m%d_%H%M%S")
    target = report.target.replace("://", "_").replace("/", "_").rstrip("_")
    label = report.test_label
    return f"{ts}_{target}_{label}_report"


def generate_json_report(report: ConsolidatedReport, output_path: Path) -> Path:
    """Write consolidated report as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2))
    return output_path
