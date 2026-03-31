"""CLI entrypoint for maldoc."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

import httpx
import typer

app = typer.Typer(
    name="maldoc",
    help="Adversarial document generation and evaluation framework.",
    no_args_is_help=True,
)

DEFAULT_REPORTS_DIR = "reports"
DEFAULT_OUTPUT_DIR = "output"
SUPPORTED_FORMATS_HELP = (
    "Document format: pdf, docx, html, md, txt, csv, image, png, jpg, jpeg, xlsx, pptx, eml"
)


def _resolve_target_url(target: str, target_url: str) -> str:
    """Resolve target URL, applying defaults when not explicitly provided."""
    if target_url:
        return target_url
    if target == "http":
        raise typer.BadParameter("--target-url is required when --target=http")
    defaults = {
        "demo": "http://localhost:8000",
        "chatbot": "http://localhost:8001",
    }
    return defaults.get(target, "http://localhost:8000")


def _get_adapter(target: str, target_url: str):
    """Create an adapter instance by name."""
    url = _resolve_target_url(target, target_url)
    if target == "demo":
        from maldoc.adapters.demo import DemoAdapter

        return DemoAdapter(base_url=url)
    if target == "chatbot":
        from maldoc.adapters.chatbot import ChatbotAdapter

        return ChatbotAdapter(base_url=url)
    if target == "http":
        from maldoc.adapters.http import HttpAdapter

        return HttpAdapter(base_url=url)
    raise typer.BadParameter(f"Unknown target adapter: {target}")


def _build_cli_commands(argv: list[str]) -> list[str]:
    """Build the list of CLI commands for the report appendix."""
    import shlex

    commands = ["uv sync"]
    # Reconstruct the maldoc invocation from sys.argv
    args = " ".join(shlex.quote(a) for a in argv[1:]) if len(argv) > 1 else ""
    commands.append(f"uv run maldoc {args}")
    return commands


def _target_label(target: str, target_url: str) -> str:
    """Short label for the target, used in report filenames."""
    if target in ("demo", "chatbot"):
        return target
    return target_url.split("://")[-1].split("/")[0].replace(":", "_")


def _is_transient_eval_error(exc: Exception) -> bool:
    """Return whether an evaluation error is likely transient."""
    transient_types = (
        httpx.TimeoutException,
        httpx.NetworkError,
        httpx.RemoteProtocolError,
    )
    return isinstance(exc, transient_types)


def _aggregate_execution_mode(results: list) -> str:
    """Collapse per-result evidence modes into a report-level mode."""
    modes = {getattr(result, "evidence_mode", "white_box") for result in results}
    if len(modes) == 1:
        return modes.pop()
    return "mixed"


def _resolve_compose_file() -> Path:
    """Find docker-compose.yml used by the demo command."""
    candidates = [
        Path.cwd() / "docker-compose.yml",
        Path(__file__).resolve().parents[2] / "docker-compose.yml",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise typer.BadParameter("Could not find docker-compose.yml")


@app.command()
def generate(
    attack: Annotated[str, typer.Option(help="Attack class to use")],
    format: Annotated[str, typer.Option(help=SUPPORTED_FORMATS_HELP)] = "pdf",
    output_dir: Annotated[str, typer.Option(help="Output directory for generated documents")] = DEFAULT_OUTPUT_DIR,
    payload: Annotated[str | None, typer.Option(help="Custom payload text")] = None,
    template: Annotated[str, typer.Option(help="Document template: memo, report, invoice")] = "memo",
):
    """Generate adversarial documents."""
    from maldoc.attacks import get_attack
    from maldoc.coverage import assess_attack_format
    from maldoc.generate import generate_document
    from maldoc.generate.templates import get_template

    atk = get_attack(attack)
    tmpl = get_template(template)
    text = payload or atk.default_payload()
    result = atk.apply(text, tmpl)
    allowed, degraded, message = assess_attack_format(result.technique, format)
    if not allowed:
        raise typer.BadParameter(message)
    if degraded:
        typer.echo(f"Warning: {message}")
    path = generate_document(result, tmpl["title"], format, output_dir)
    typer.echo(f"Generated: {path}")


@app.command()
def evaluate(
    file: Annotated[str, typer.Option(help="Path to document to evaluate")],
    attack: Annotated[str, typer.Option(help="Attack class used to generate the document")],
    target: Annotated[str, typer.Option(help="Target adapter: demo, chatbot, http")] = "demo",
    target_url: Annotated[str, typer.Option(help="Target base URL (default: auto per target)")] = "",
    query: Annotated[str | None, typer.Option(help="Custom query for evaluation")] = None,
    payload: Annotated[str | None, typer.Option(help="Payload used in the document")] = None,
    template: Annotated[str, typer.Option(help="Document template used for generation")] = "memo",
    reports_dir: Annotated[str, typer.Option(help="Output directory for reports")] = DEFAULT_REPORTS_DIR,
):
    """Evaluate a document against a target."""
    from maldoc.attacks import get_attack
    from maldoc.evaluate.evidence import ConsolidatedReport, SkippedCombination
    from maldoc.evaluate.runner import evaluate as run_eval
    from maldoc.report.json_report import generate_json_report, report_filename
    from maldoc.report.markdown_report import generate_markdown_report

    atk = get_attack(attack)
    resolved_url = _resolve_target_url(target, target_url)
    adapter = _get_adapter(target, resolved_url)
    try:
        from maldoc.generate.templates import get_template

        tmpl = get_template(template)
        attack_payload = payload or atk.default_payload()
        attack_result = atk.apply(attack_payload, tmpl)
        result = run_eval(adapter, attack_result, Path(file), query)

        report = ConsolidatedReport(
            timestamp=datetime.now(),
            target=_target_label(target, resolved_url),
            results=[result],
            requested_attacks=[attack],
            requested_formats=[Path(file).suffix.lstrip(".")],
            execution_mode=result.evidence_mode,
        )
        name = report_filename(report)
        json_path = Path(reports_dir) / f"{name}.json"
        md_path = Path(reports_dir) / f"{name}.md"
        generate_json_report(report, json_path)
        generate_markdown_report(report, md_path)

        typer.echo(f"Reports: {json_path}, {md_path}")
        for stage, score in result.scores.items():
            label = f"{score:.2f}" if score is not None else "N/A"
            typer.echo(f"  {stage}: {label}")
    finally:
        adapter.close()


@app.command()
def report(
    input: Annotated[str, typer.Option(help="Path to evaluation result JSON")],
    format: Annotated[Literal["json", "markdown"], typer.Option(help="Report format: json, markdown")] = "markdown",
    reports_dir: Annotated[str, typer.Option(help="Output directory for reports")] = DEFAULT_REPORTS_DIR,
):
    """Generate a report from evaluation results."""
    from maldoc.evaluate.evidence import ConsolidatedReport, SkippedCombination
    from maldoc.report.json_report import generate_json_report, report_filename
    from maldoc.report.markdown_report import generate_markdown_report

    data = Path(input).read_text()
    report = ConsolidatedReport.model_validate_json(data)
    name = report_filename(report)

    if format == "json":
        path = generate_json_report(report, Path(reports_dir) / f"{name}.json")
    else:
        path = generate_markdown_report(report, Path(reports_dir) / f"{name}.md")

    typer.echo(f"Report generated: {path}")


@app.command()
def run(
    attack: Annotated[str, typer.Option(help="Attack(s), comma-separated")],
    format: Annotated[str, typer.Option(help="Format(s), comma-separated; see generate --help")] = "pdf",
    target: Annotated[str, typer.Option(help="Target adapter: demo, chatbot, http")] = "demo",
    target_url: Annotated[str, typer.Option(help="Target base URL (default: auto per target)")] = "",
    output_dir: Annotated[str, typer.Option(help="Output directory for generated documents")] = DEFAULT_OUTPUT_DIR,
    reports_dir: Annotated[str, typer.Option(help="Output directory for reports")] = DEFAULT_REPORTS_DIR,
    query: Annotated[str | None, typer.Option(help="Custom query for evaluation")] = None,
    template: Annotated[str, typer.Option(help="Document template")] = "memo",
    payload: Annotated[str | None, typer.Option(help="Custom payload text")] = None,
):
    """Run full pipeline: generate -> evaluate -> report.

    Supports comma-separated attacks and formats to run multiple combos.
    Results are consolidated into a single report.
    """
    from maldoc.attacks import get_attack
    from maldoc.coverage import assess_attack_format
    from maldoc.evaluate.evidence import ConsolidatedReport, SkippedCombination
    from maldoc.evaluate.runner import evaluate as run_eval
    from maldoc.generate import generate_document
    from maldoc.generate.templates import get_template
    from maldoc.report.json_report import generate_json_report, report_filename
    from maldoc.report.markdown_report import generate_markdown_report

    attacks = [a.strip() for a in attack.split(",")]
    formats = [f.strip() for f in format.split(",")]
    tmpl = get_template(template)
    resolved_url = _resolve_target_url(target, target_url)
    adapter = _get_adapter(target, resolved_url)

    try:
        results = []
        skipped = []
        total = len(attacks) * len(formats)
        current = 0

        for atk_name in attacks:
            for fmt in formats:
                current += 1
                typer.echo(f"[{current}/{total}] {atk_name} / {fmt}")

                atk = get_attack(atk_name)
                allowed, degraded, message = assess_attack_format(atk_name, fmt)
                if not allowed:
                    typer.echo(f"  Skipped: {message}")
                    skipped.append(
                        SkippedCombination(
                            attack_name=atk_name,
                            document_format=fmt,
                            reason=message,
                        )
                    )
                    continue
                if degraded:
                    typer.echo(f"  Warning: {message}")
                text = payload or atk.default_payload()
                attack_result = atk.apply(text, tmpl)
                doc_path = generate_document(attack_result, tmpl["title"], fmt, output_dir)
                typer.echo(f"  Generated: {doc_path}")

                for attempt in range(3):
                    try:
                        result = run_eval(adapter, attack_result, doc_path, query)
                        break
                    except Exception as exc:
                        if attempt < 2 and _is_transient_eval_error(exc):
                            import time
                            typer.echo(f"  Retry {attempt + 1}/2 after error: {exc}")
                            time.sleep(5)
                        else:
                            raise
                results.append(result)

                for stage, score in result.scores.items():
                    label = f"{score:.2f}" if score is not None else "N/A"
                    typer.echo(f"  {stage}: {label}")

        # Consolidated report
        cli_commands = _build_cli_commands(sys.argv)
        report = ConsolidatedReport(
            timestamp=datetime.now(),
            target=_target_label(target, resolved_url),
            results=results,
            cli_commands=cli_commands,
            requested_attacks=attacks,
            requested_formats=formats,
            skipped_combinations=skipped,
            execution_mode=_aggregate_execution_mode(results),
        )
        name = report_filename(report)
        json_path = Path(reports_dir) / f"{name}.json"
        md_path = Path(reports_dir) / f"{name}.md"
        generate_json_report(report, json_path)
        generate_markdown_report(report, md_path)

        typer.echo("")
        typer.echo(f"Reports: {json_path}, {md_path}")
        typer.echo(f"  {len(results)} tests consolidated into single report")
        if skipped:
            typer.echo(f"  {len(skipped)} combinations skipped")
    finally:
        adapter.close()


@app.command()
def demo(
    action: Annotated[Literal["start", "stop", "reset"], typer.Argument(help="Action: start, stop, reset")],
    target_url: Annotated[str, typer.Option(help="Demo app URL")] = "http://localhost:8000",
):
    """Manage the demo app."""
    import subprocess

    if action == "reset":
        adapter = _get_adapter("demo", target_url)
        try:
            adapter.reset()
            typer.echo("Demo app state reset.")
        finally:
            adapter.close()
        return

    compose_file = _resolve_compose_file()
    if action == "start":
        typer.echo("Starting demo services...")
        subprocess.run(
            [
                "docker", "compose", "-f", str(compose_file),
                "up", "--build", "-d", "demo-app", "demo-chatbot",
            ],
            check=True,
        )
        typer.echo("Demo-API started at http://localhost:8000")
        typer.echo("Demo-Chatbot started at http://localhost:8001")
    else:
        typer.echo("Stopping demo services...")
        subprocess.run(["docker", "compose", "-f", str(compose_file), "down"], check=True)
        typer.echo("Demo services stopped.")
