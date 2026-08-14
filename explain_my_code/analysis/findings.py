"""Risk and quality findings.

Scoped to things visible in a snippet with no project context — no import graph, no
call sites outside the paste. Every rule states the threshold it tripped, because an
unexplained "too complex" badge is not an explanation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from explain_my_code.ir import CALLABLE_KINDS, Kind, Language, Node, Span

if TYPE_CHECKING:
    from explain_my_code.analysis.metrics import FunctionMetrics
    from explain_my_code.analysis.symbols import SymbolTable

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}

# Thresholds, named so the message can quote them.
MAX_NESTING = 3
MAX_FUNCTION_LINES = 50
MAX_CYCLOMATIC = 10
MAX_COGNITIVE = 15
MAX_PARAMS = 5

SQL_IN_STRING = re.compile(r"\b(select|insert|update|delete|drop)\b\s", re.IGNORECASE)


@dataclass(slots=True)
class Finding:
    rule: str
    title: str
    message: str
    severity: str
    span: Span | None = None
    suggestion: str = ""
    concepts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "rule": self.rule,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
        }
        if self.span:
            out["span"] = self.span.to_dict()
            out["line"] = self.span.start_line
        if self.suggestion:
            out["suggestion"] = self.suggestion
        return out


def collect_findings(
    root: Node,
    language: Language,
    functions: list[FunctionMetrics],
    symbols: SymbolTable,
) -> list[Finding]:
    out: list[Finding] = []
    out += _structural(functions)
    out += _error_handling(root)
    out += _language_specific(root, language)
    out += _symbol_findings(symbols)
    out += _todos(root)
    out.sort(key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.span.start_line if f.span else 0))
    return out


def _span_of(function: FunctionMetrics) -> Span:
    return Span(function.line, 0, function.line, 10_000)


def _structural(functions: list[FunctionMetrics]) -> list[Finding]:
    out: list[Finding] = []
    for function in functions:
        if function.max_nesting > MAX_NESTING:
            out.append(
                Finding(
                    "deep-nesting",
                    "Deeply nested logic",
                    f"`{function.name}` nests {function.max_nesting} levels deep "
                    f"(over the {MAX_NESTING}-level threshold). Each level is another "
                    "condition the reader has to keep in mind at once.",
                    "medium",
                    _span_of(function),
                    "Invert the outer conditions into early returns, or lift the inner block into its own function.",
                    ["guard-clause"],
                )
            )
        if function.cyclomatic > MAX_CYCLOMATIC:
            out.append(
                Finding(
                    "high-complexity",
                    "High cyclomatic complexity",
                    f"`{function.name}` has {function.cyclomatic} independent paths "
                    f"(threshold {MAX_CYCLOMATIC}), so it needs at least that many tests "
                    "to cover every branch.",
                    "medium",
                    _span_of(function),
                    "Split the branches into separate functions or replace the chain with a lookup table.",
                )
            )
        elif function.cognitive > MAX_COGNITIVE:
            out.append(
                Finding(
                    "high-cognitive-load",
                    "Hard to follow",
                    f"`{function.name}` scores {function.cognitive} on cognitive complexity "
                    f"(threshold {MAX_COGNITIVE}) — the branches are nested rather than sequential.",
                    "low",
                    _span_of(function),
                    "Flatten the nesting; sequential branches cost far less to read than nested ones.",
                )
            )
        if function.lines > MAX_FUNCTION_LINES:
            out.append(
                Finding(
                    "long-function",
                    "Long function",
                    f"`{function.name}` runs {function.lines} lines "
                    f"(threshold {MAX_FUNCTION_LINES}).",
                    "low",
                    _span_of(function),
                    "Look for a section with its own name — that section is usually a function.",
                )
            )
        if function.param_count > MAX_PARAMS:
            out.append(
                Finding(
                    "too-many-params",
                    "Long parameter list",
                    f"`{function.name}` takes {function.param_count} parameters "
                    f"(threshold {MAX_PARAMS}), which makes call sites hard to read and easy to mis-order.",
                    "low",
                    _span_of(function),
                    "Group related parameters into an object or dataclass.",
                )
            )
        if function.complexity_class.startswith(("O(2^n", "O(3^n")):
            out.append(
                Finding(
                    "exponential-recursion",
                    "Exponential recursion",
                    f"`{function.name}` looks exponential: {function.complexity_reason}",
                    "high",
                    _span_of(function),
                    "Memoise the results, or rewrite it bottom-up so each subproblem is solved once.",
                    ["memoization", "recursion"],
                )
            )
    return out


def _error_handling(root: Node) -> list[Finding]:
    out: list[Finding] = []
    for node in root.find(Kind.CATCH):
        if node.meta.get("is_bare"):
            out.append(
                Finding(
                    "bare-except",
                    "Catches everything",
                    "This handler catches every exception type, including the ones that mean "
                    "the program should stop (interrupts, out-of-memory).",
                    "medium",
                    node.span,
                    "Catch the specific exceptions you can actually handle.",
                    ["error-handling"],
                )
            )
        if node.meta.get("swallows"):
            out.append(
                Finding(
                    "swallowed-exception",
                    "Silently swallowed error",
                    "The handler body does nothing, so a failure here leaves no trace.",
                    "high",
                    node.span,
                    "Log it, re-raise it, or explain in a comment why it is safe to ignore.",
                    ["error-handling"],
                )
            )
    for node in root.find(Kind.LOOP_WHILE):
        if node.meta.get("is_infinite") and not node.meta.get("has_break"):
            out.append(
                Finding(
                    "infinite-loop",
                    "Loop with no exit",
                    "The condition is always true and the body contains no break.",
                    "high",
                    node.span,
                    "Add an exit condition, or make the non-termination explicit and intentional.",
                )
            )
    return out


def _language_specific(root: Node, language: Language) -> list[Finding]:
    out: list[Finding] = []

    if language is Language.SQL:
        for node in root.find(Kind.SELECT):
            if node.meta.get("selects_star"):
                out.append(
                    Finding(
                        "select-star",
                        "SELECT *",
                        "Selecting every column moves data nobody asked for and breaks silently "
                        "when the table gains a column.",
                        "low",
                        node.span,
                        "List the columns you actually use.",
                    )
                )
        for node in root.find(Kind.UPDATE, Kind.DELETE_ROWS):
            if not node.meta.get("has_where"):
                out.append(
                    Finding(
                        "unfiltered-write",
                        "Write with no WHERE clause",
                        f"This {node.name} affects every row in {node.meta.get('table', 'the table')}.",
                        "high",
                        node.span,
                        "Add a WHERE clause, and run it as a SELECT first to see what it would touch.",
                    )
                )
        for node in root.find(Kind.JOIN):
            if node.meta.get("is_cross"):
                out.append(
                    Finding(
                        "cross-join",
                        "Join with no condition",
                        "Without an ON clause every left row is paired with every right row, "
                        "so the result is the product of both row counts.",
                        "high",
                        node.span,
                        "Add the join key, or say CROSS JOIN explicitly if that is the intent.",
                        ["sql-join"],
                    )
                )
        return out

    if language is Language.CPP:
        allocations = list(root.find(Kind.NEW))
        frees = list(root.find(Kind.DELETE))
        if allocations and len(frees) < len(allocations):
            out.append(
                Finding(
                    "unbalanced-allocation",
                    "More allocations than frees",
                    f"{len(allocations)} allocation(s) but {len(frees)} delete(s) in this snippet. "
                    "Any path that returns early leaks.",
                    "medium",
                    allocations[0].span,
                    "Use std::vector or a smart pointer so cleanup happens on scope exit.",
                    ["manual-memory"],
                )
            )

    # A query assembled by interpolation is the classic injection shape.
    for node in root.find(Kind.FSTRING):
        slots = node.meta.get("slots") or []
        if slots and SQL_IN_STRING.search(str(node.meta.get("text", "")) or str(node.name or "")):
            out.append(
                Finding(
                    "sql-injection-risk",
                    "Query built by interpolation",
                    "Interpolating values into SQL lets a crafted input change the query.",
                    "high",
                    node.span,
                    "Use bound parameters and let the driver escape the values.",
                    ["string-interpolation"],
                )
            )

    if language is Language.PYTHON:
        for node in root.find(Kind.PARAM):
            default = str(node.meta.get("default") or "")
            if default.startswith(("[", "{", "set(", "dict(", "list(")):
                out.append(
                    Finding(
                        "mutable-default",
                        "Mutable default argument",
                        f"`{node.name}={default}` is built once when the function is defined, "
                        "then shared by every call that omits the argument.",
                        "medium",
                        node.span,
                        f"Default to None and create the {default} inside the function body.",
                    )
                )
    return out


def _symbol_findings(symbols: SymbolTable) -> list[Finding]:
    out: list[Finding] = []
    for symbol in symbols.unused[:6]:
        out.append(
            Finding(
                "unused-binding",
                "Assigned but never read",
                f"`{symbol.name}` is assigned here and not read again in this snippet.",
                "info",
                symbol.defined_at[0] if symbol.defined_at else None,
                "Remove it, or prefix it with an underscore to mark it deliberately unused.",
            )
        )
    for symbol in symbols.shadowed[:4]:
        out.append(
            Finding(
                "shadowed-name",
                "Shadows an outer name",
                f"`{symbol.name}` reuses a name that already exists in the {symbol.shadows} scope, "
                "so the outer one is unreachable from here.",
                "low",
                symbol.defined_at[0] if symbol.defined_at else None,
                "Rename one of them; the reader cannot tell which is which at a glance.",
            )
        )
    return out


def _todos(root: Node) -> list[Finding]:
    return [
        Finding(
            "todo-comment",
            "Unfinished work marked in a comment",
            str(node.meta.get("text", ""))[:160],
            "info",
            node.span,
        )
        for node in root.find(Kind.COMMENT)
        if node.meta.get("is_todo")
    ][:5]


def nesting_of(node: Node) -> int:
    return sum(1 for ancestor in node.ancestors() if ancestor.kind in CALLABLE_KINDS)
