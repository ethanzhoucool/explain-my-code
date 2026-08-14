"""`emc` — the command line front end.

Same pipeline as the API, rendered for a terminal: complexity in the gutter, the
explanation beside the code, metrics and findings underneath.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from explain_my_code import __version__
from explain_my_code.core import detect_language, explain, supported_languages
from explain_my_code.ir import Language, Level, Source

app = typer.Typer(
    name="emc",
    help="Static analysis that explains itself.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()

SEVERITY_STYLE = {"high": "bold red", "medium": "yellow", "low": "cyan", "info": "dim"}
RATING_STYLE = {"A": "bold green", "B": "green", "C": "yellow", "D": "red", "F": "bold red"}


def _read_source(path: str | None) -> tuple[str, str | None]:
    if path is None or path == "-":
        if sys.stdin.isatty():
            raise typer.BadParameter("No input. Pass a file path, or pipe source on stdin.")
        return sys.stdin.read(), None
    file = Path(path)
    if not file.exists():
        raise typer.BadParameter(f"No such file: {path}")
    return file.read_text("utf-8"), file.name


def _complexity_marker(line: int, result: Any) -> Text:
    """Gutter marker for lines that start a callable, coloured by its rating."""
    for function in result.analysis.functions:
        if function.line == line:
            rating = function.to_dict()["rating"]
            return Text(f"{rating}", style=RATING_STYLE.get(rating, "white"))
    return Text(" ")


@app.command()
def version() -> None:
    """Print the version."""
    console.print(f"explain-my-code {__version__}")


@app.command()
def languages() -> None:
    """List supported languages and their parsers."""
    table = Table(title="Supported languages", header_style="bold")
    table.add_column("Language")
    table.add_column("Parser")
    table.add_column("Extensions")
    table.add_column("Status")
    for entry in supported_languages():
        table.add_row(
            entry["id"],
            entry["parser"],
            " ".join(entry["extensions"]),
            "[green]ready[/green]" if entry["available"] else "[red]unavailable[/red]",
        )
    console.print(table)


@app.command()
def detect(path: str = typer.Argument(None, help="File to inspect, or - for stdin.")) -> None:
    """Guess the language of a file."""
    source, filename = _read_source(path)
    result = detect_language(source, filename)
    console.print(
        f"[bold]{result.language.value}[/bold] "
        f"(confidence {result.confidence:.0%}"
        + (f", runner-up {result.runner_up.value}" if result.runner_up else "")
        + ")"
    )


@app.command("explain")
def explain_command(
    path: str = typer.Argument(None, help="File to explain, or - for stdin."),
    level: str = typer.Option("beginner", "--level", "-l", help="eli5 | beginner | developer."),
    language: str = typer.Option(None, "--language", "-L", help="Override detection."),
    output: str = typer.Option("terminal", "--format", "-f", help="terminal | json | markdown."),
    enrich: bool = typer.Option(False, "--enrich", help="Add an LLM pass on top."),
    provider: str = typer.Option(None, "--provider", help="anthropic | gemini."),
    no_code: bool = typer.Option(False, "--no-code", help="Explanations only."),
) -> None:
    """Explain a file at one of three audience levels."""
    source, filename = _read_source(path)
    try:
        level_value = Level(level)
    except ValueError as exc:
        raise typer.BadParameter("level must be eli5, beginner or developer") from exc

    result = explain(
        source,
        language=Language(language) if language else None,
        level=level_value,
        filename=filename,
        enrich=(provider or True) if enrich else False,
    )

    if output == "json":
        console.print_json(json.dumps(result.to_dict()))
        return
    if output == "markdown":
        console.print(_markdown(result))
        return

    _render_terminal(result, show_code=not no_code)


def _render_terminal(result: Any, *, show_code: bool) -> None:
    metrics = result.analysis.metrics.to_dict()
    header = (
        f"[bold]{result.language.value}[/bold] · {result.level.value} · "
        f"parsed by {result.analysis.parser} · "
        f"[{RATING_STYLE.get(metrics['rating'], 'white')}]{metrics['rating']}[/] "
        f"({metrics['maintainability']}/100)"
    )
    console.print(Panel(escape(result.summary), title=header, border_style="blue"))

    if result.diagnostics:
        for diagnostic in result.diagnostics:
            style = "red" if diagnostic.severity == "error" else "yellow"
            location = f" (line {diagnostic.span.start_line})" if diagnostic.span else ""
            console.print(f"[{style}]! {escape(diagnostic.message)}{location}[/{style}]")

    by_line = {line.line: line for line in result.lines}
    source_lines = result.source.splitlines()

    if show_code:
        console.print()
        for index, text in enumerate(source_lines, start=1):
            marker = _complexity_marker(index, result)
            gutter = Text(f"{index:>4} ", style="dim")
            code = Syntax(
                text or " ",
                result.language.value,
                theme="ansi_dark",
                background_color="default",
                word_wrap=False,
            )
            console.print(Text.assemble(marker, " ", gutter), code, sep="", end="")
            explanation = by_line.get(index)
            if explanation:
                tag = "[magenta]ai[/magenta]" if explanation.source is Source.LLM else ""
                console.print(f"       [dim]↳[/dim] {escape(explanation.text)} {tag}")
    else:
        for line in result.lines:
            console.print(f"[dim]{line.line:>4}[/dim]  {escape(line.text)}")

    _render_metrics(result)
    _render_concepts(result)
    _render_findings(result)


def _render_metrics(result: Any) -> None:
    if not result.analysis.functions:
        return
    table = Table(title="Functions", header_style="bold", show_edge=False)
    for column in ("Line", "Name", "Params", "Cyclo", "Cognitive", "Nesting", "Cost", "Rating"):
        table.add_column(column)
    for function in result.analysis.functions:
        data = function.to_dict()
        table.add_row(
            str(function.line),
            escape(function.name) + (" ↻" if function.is_recursive else ""),
            str(function.param_count),
            str(function.cyclomatic),
            str(function.cognitive),
            str(function.max_nesting),
            function.complexity_class,
            f"[{RATING_STYLE.get(data['rating'], 'white')}]{data['rating']}[/]",
        )
    console.print()
    console.print(table)


def _render_concepts(result: Any) -> None:
    concepts = result.analysis.concepts
    if not concepts:
        return
    console.print()
    console.print("[bold]Concepts[/bold]")
    for hit in concepts[:8]:
        lines = ", ".join(str(line) for line in sorted({s.start_line for s in hit.spans})[:6])
        console.print(f"  [cyan]{hit.label}[/cyan] [dim](lines {lines})[/dim]")
        console.print(f"    {escape(hit.texts.get(result.level, ''))}")


def _render_findings(result: Any) -> None:
    findings = result.analysis.findings
    if not findings:
        return
    console.print()
    console.print("[bold]Findings[/bold]")
    for finding in findings:
        style = SEVERITY_STYLE.get(finding.severity, "white")
        location = f"line {finding.span.start_line}" if finding.span else "file"
        console.print(f"  [{style}]{finding.severity:>6}[/{style}] {location:>9}  {escape(finding.title)}")
        console.print(f"           {escape(finding.message)}")
        if finding.suggestion:
            console.print(f"           [dim]→ {escape(finding.suggestion)}[/dim]")


def _markdown(result: Any) -> str:
    metrics = result.analysis.metrics.to_dict()
    out = [
        f"# Explanation ({result.language.value}, {result.level.value})",
        "",
        result.summary,
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Lines of code | {metrics['codeLines']} |",
        f"| Cyclomatic complexity | {metrics['cyclomatic']} |",
        f"| Cognitive complexity | {metrics['cognitive']} |",
        f"| Maintainability | {metrics['maintainability']}/100 ({metrics['rating']}) |",
        "",
    ]
    if result.analysis.functions:
        out += ["## Functions", "", "| Line | Name | Cyclomatic | Cost |", "| --- | --- | --- | --- |"]
        out += [
            f"| {f.line} | `{f.name}` | {f.cyclomatic} | {f.complexity_class} |"
            for f in result.analysis.functions
        ]
        out.append("")
    out += ["## Line by line", ""]
    source_lines = result.source.splitlines()
    by_line = {line.line: line for line in result.lines}
    for index, text in enumerate(source_lines, start=1):
        explanation = by_line.get(index)
        out.append(f"```{result.language.value}")
        out.append(text)
        out.append("```")
        if explanation:
            out.append(f"> {explanation.text}")
        out.append("")
    if result.analysis.findings:
        out += ["## Findings", ""]
        out += [
            f"- **{f.title}** ({f.severity}"
            + (f", line {f.span.start_line}" if f.span else "")
            + f"): {f.message}"
            for f in result.analysis.findings
        ]
    return "\n".join(out)


@app.command()
def metrics(
    path: str = typer.Argument(None, help="File to measure, or - for stdin."),
    language: str = typer.Option(None, "--language", "-L"),
    output: str = typer.Option("terminal", "--format", "-f", help="terminal | json."),
) -> None:
    """Metrics and findings only — no prose."""
    source, filename = _read_source(path)
    result = explain(source, language=Language(language) if language else None, filename=filename)
    if output == "json":
        console.print_json(json.dumps(result.analysis.to_dict()))
        return
    _render_metrics(result)
    _render_findings(result)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(5000, "--port", "-p"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Run the web UI and API."""
    import uvicorn

    console.print(f"[bold]Explain My Code[/bold] on http://{host}:{port}  (docs at /docs)")
    uvicorn.run("explain_my_code.api.main:app", host=host, port=port, reload=reload)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
