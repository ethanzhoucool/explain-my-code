"""IR + analysis -> annotations, and the narrative summary that sits above them.

Two knobs make the output readable rather than exhaustive:

* **Density by level.** ELI5 annotates structure and control flow only; a five-year-old
  does not need to be told that `x` is a name. DEVELOPER annotates everything that has
  a template.
* **One anchor per line.** Several nodes can start on the same line, so the most
  significant one wins the gutter and the rest stay available as hover detail.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from explain_my_code.analysis.pipeline import Analysis
from explain_my_code.ir import (
    CALLABLE_KINDS,
    LOOP_KINDS,
    Annotation,
    Kind,
    Level,
    Node,
    ParseResult,
    Source,
)
from explain_my_code.narrate.phrasebook import explains, phrase

#: Structural kinds, always annotated at every level.
CORE_KINDS = frozenset(
    {
        Kind.MODULE, Kind.CLASS, Kind.INTERFACE, Kind.FUNCTION, Kind.METHOD,
        Kind.CONSTRUCTOR, Kind.LAMBDA, Kind.BRANCH, Kind.ELSE, Kind.LOOP_FOR,
        Kind.LOOP_FOREACH, Kind.LOOP_WHILE, Kind.LOOP_DO, Kind.SWITCH, Kind.CASE,
        Kind.RETURN, Kind.YIELD, Kind.TRY, Kind.CATCH, Kind.FINALLY, Kind.THROW,
        Kind.WITH, Kind.AWAIT, Kind.IMPORT, Kind.DECORATOR, Kind.COMPREHENSION,
        Kind.SELECT, Kind.FROM, Kind.JOIN, Kind.WHERE, Kind.GROUP_BY, Kind.HAVING,
        Kind.ORDER_BY, Kind.LIMIT, Kind.CTE, Kind.WINDOW, Kind.INSERT, Kind.UPDATE,
        Kind.DELETE_ROWS, Kind.CREATE, Kind.SET_OP, Kind.SUBQUERY,
    }
)

#: Added at BEGINNER and above.
DETAIL_KINDS = frozenset(
    {
        Kind.ASSIGN, Kind.DECL, Kind.AUG_ASSIGN, Kind.CALL, Kind.METHOD_CALL, Kind.NEW,
        Kind.DELETE, Kind.PARAM, Kind.BREAK, Kind.CONTINUE, Kind.TERNARY, Kind.EXPORT,
        Kind.NAMESPACE, Kind.ANNOTATION, Kind.DESTRUCTURE, Kind.FSTRING, Kind.SPREAD,
        Kind.PROJECTION, Kind.AGGREGATE, Kind.CAST,
    }
)

#: Added only at DEVELOPER level: expression-level noise otherwise.
EXPRESSION_KINDS = frozenset(
    {
        Kind.COMPARE, Kind.BOOLOP, Kind.BINOP, Kind.UNOP, Kind.INDEX, Kind.SLICE,
        Kind.ATTRIBUTE, Kind.COLLECTION, Kind.LITERAL,
    }
)

#: Higher wins the line anchor when several nodes start on the same line.
SIGNIFICANCE: dict[Kind, int] = {
    Kind.MODULE: 0,
    Kind.CLASS: 100, Kind.INTERFACE: 100, Kind.FUNCTION: 95, Kind.METHOD: 95,
    Kind.CONSTRUCTOR: 95, Kind.SELECT: 95, Kind.INSERT: 95, Kind.UPDATE: 95,
    Kind.DELETE_ROWS: 95, Kind.CREATE: 95, Kind.CTE: 92, Kind.SET_OP: 92,
    Kind.LOOP_FOR: 90, Kind.LOOP_FOREACH: 90, Kind.LOOP_WHILE: 90, Kind.LOOP_DO: 90,
    Kind.SWITCH: 85, Kind.BRANCH: 85, Kind.TRY: 85, Kind.WITH: 85, Kind.MATCH: 85,
    Kind.JOIN: 84, Kind.WHERE: 84, Kind.GROUP_BY: 83, Kind.HAVING: 83,
    Kind.ORDER_BY: 82, Kind.FROM: 82, Kind.LIMIT: 80, Kind.WINDOW: 80,
    Kind.CATCH: 80, Kind.FINALLY: 80, Kind.ELSE: 80, Kind.CASE: 78,
    Kind.LAMBDA: 75, Kind.COMPREHENSION: 75, Kind.SUBQUERY: 75,
    Kind.RETURN: 70, Kind.YIELD: 70, Kind.THROW: 70, Kind.AWAIT: 68,
    Kind.IMPORT: 65, Kind.DECORATOR: 65, Kind.EXPORT: 65, Kind.NAMESPACE: 65,
    Kind.ASSIGN: 60, Kind.DECL: 60, Kind.AUG_ASSIGN: 58, Kind.DESTRUCTURE: 58,
    Kind.PROJECTION: 55, Kind.METHOD_CALL: 50, Kind.CALL: 50, Kind.NEW: 50,
    Kind.AGGREGATE: 50, Kind.DELETE: 50, Kind.BREAK: 45, Kind.CONTINUE: 45,
    Kind.TERNARY: 40, Kind.PARAM: 35, Kind.FSTRING: 30, Kind.CAST: 30,
    Kind.COMPARE: 25, Kind.BOOLOP: 25, Kind.BINOP: 20, Kind.UNOP: 20,
    Kind.INDEX: 20, Kind.SLICE: 20, Kind.ATTRIBUTE: 15, Kind.COLLECTION: 15,
    Kind.SPREAD: 15, Kind.ANNOTATION: 15, Kind.LITERAL: 5, Kind.COMMENT: 3,
}


def kinds_for(level: Level) -> frozenset[Kind]:
    if level is Level.ELI5:
        return CORE_KINDS
    if level is Level.BEGINNER:
        return CORE_KINDS | DETAIL_KINDS
    return CORE_KINDS | DETAIL_KINDS | EXPRESSION_KINDS


def _concepts_for(node: Node, analysis: Analysis) -> list[str]:
    return [hit.concept_id for hit in analysis.concepts if node.id in hit.node_ids]


def _detail_for(node: Node, analysis: Analysis) -> str | None:
    """Extra context only worth showing on the node it belongs to."""
    if node.kind in CALLABLE_KINDS:
        for function in analysis.functions:
            if function.node_id == node.id:
                bits = [f"{function.complexity_class}: {function.complexity_reason}"]
                if function.cyclomatic > 1:
                    bits.append(
                        f"{function.cyclomatic} independent path(s), "
                        f"cognitive complexity {function.cognitive}"
                    )
                if function.is_recursive:
                    bits.append("recursive")
                return " · ".join(bits)
    if node.kind in LOOP_KINDS and node.loop_depth >= 1:
        return f"Nested {node.loop_depth + 1} loops deep. The body runs about n^{node.loop_depth + 1} times."
    return None


def annotate(parsed: ParseResult, analysis: Analysis, level: Level) -> list[Annotation]:
    allowed = kinds_for(level)
    out: list[Annotation] = []
    for node in parsed.root.walk():
        if node.kind is Kind.MODULE or node.kind not in allowed or not explains(node.kind):
            continue
        text = phrase(node, level)
        if not text:
            continue
        out.append(
            Annotation(
                span=node.span,
                kind=node.kind,
                texts={level: text},
                source=Source.STATIC,
                confidence=1.0,
                node_id=node.id,
                concepts=_concepts_for(node, analysis),
                detail=_detail_for(node, analysis),
            )
        )
    out.sort(key=lambda a: (a.span.start_line, a.span.start_col, -SIGNIFICANCE.get(a.kind, 0)))
    return out


@dataclass(slots=True)
class LineExplanation:
    line: int
    text: str
    kind: Kind
    source: Source
    detail: str | None = None
    concepts: list[str] | None = None
    node_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "line": self.line,
            "text": self.text,
            "kind": self.kind.value,
            "source": self.source.value,
        }
        if self.detail:
            out["detail"] = self.detail
        if self.concepts:
            out["concepts"] = self.concepts
        if self.node_id is not None:
            out["nodeId"] = self.node_id
        return out


def line_view(annotations: list[Annotation], level: Level) -> list[LineExplanation]:
    """One explanation per line: the most significant construct starting there."""
    best: dict[int, Annotation] = {}
    for annotation in annotations:
        line = annotation.span.start_line
        current = best.get(line)
        if current is None or SIGNIFICANCE.get(annotation.kind, 0) > SIGNIFICANCE.get(
            current.kind, 0
        ):
            best[line] = annotation
    return [
        LineExplanation(
            line=line,
            text=annotation.text(level),
            kind=annotation.kind,
            source=annotation.source,
            detail=annotation.detail,
            concepts=annotation.concepts or None,
            node_id=annotation.node_id,
        )
        for line, annotation in sorted(best.items())
    ]


# -- narrative summary ----------------------------------------------------------------


def _joined(items: list[str], limit: int = 3) -> str:
    items = [i for i in items if i][:limit]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def summarize(analysis: Analysis, level: Level) -> str:
    """A short paragraph about the file as a whole, pitched at `level`."""
    metrics = analysis.metrics
    functions = analysis.functions
    top_concepts = [hit.label.lower() for hit in analysis.concepts[:3]]
    names = [f.name for f in functions if f.name != "<anonymous>"]

    if analysis.language.value == "sql":
        return _sql_summary(analysis, level)

    if level is Level.ELI5:
        parts = []
        if names:
            parts.append(
                f"This code defines {len(names)} named {'thing' if len(names) == 1 else 'things'}: "
                + _joined([f"`{n}`" for n in names])
                + "."
            )
        else:
            parts.append("This is a short piece of code that runs from top to bottom.")
        if metrics.loop_count:
            parts.append(
                f"It repeats work {metrics.loop_count} time{'s' if metrics.loop_count > 1 else ''} using loops."
            )
        if metrics.branch_count:
            parts.append("It makes choices along the way, doing different things in different cases.")
        if top_concepts:
            parts.append("The big ideas here are " + _joined(top_concepts) + ".")
        return " ".join(parts)

    if level is Level.BEGINNER:
        parts = []
        subject = (
            f"{metrics.function_count} function(s)" if metrics.function_count else "top-level code"
        )
        if metrics.class_count:
            subject = f"{metrics.class_count} class(es) and {subject}"
        parts.append(f"{metrics.code_lines} lines of {analysis.language.value} defining {subject}.")
        if names:
            parts.append("The entry points are " + _joined([f"`{n}`" for n in names]) + ".")
        if analysis.imports:
            parts.append("It depends on " + _joined([f"`{m}`" for m in analysis.imports]) + ".")
        hotspot = analysis.hotspot
        if hotspot and hotspot.cyclomatic > 3:
            parts.append(
                f"`{hotspot.name}` is the busiest part, with {hotspot.cyclomatic} different paths through it."
            )
        if top_concepts:
            parts.append("Concepts to know: " + _joined(top_concepts) + ".")
        return " ".join(parts)

    parts = [
        f"{metrics.code_lines} SLOC, {metrics.function_count} callable(s), "
        f"cyclomatic {metrics.cyclomatic}, cognitive {metrics.cognitive}, "
        f"maintainability {metrics.maintainability} ({metrics.to_dict()['rating']})."
    ]
    costly = [f for f in functions if f.complexity_class not in {"O(1)", "O(n)"}]
    if costly:
        parts.append(
            "Cost hotspots: "
            + _joined([f"`{f.name}` {f.complexity_class}" for f in costly], limit=3)
            + "."
        )
    if analysis.call_graph.cycles:
        parts.append(
            "Mutual recursion between "
            + _joined([" ↔ ".join(c) for c in analysis.call_graph.cycles], limit=2)
            + "."
        )
    high = [f for f in analysis.findings if f.severity == "high"]
    if high:
        parts.append(f"{len(high)} high-severity finding(s): " + _joined([f.title for f in high]) + ".")
    return " ".join(parts)


def _sql_summary(analysis: Analysis, level: Level) -> str:
    root = analysis.root
    selects = list(root.find(Kind.SELECT))
    joins = list(root.find(Kind.JOIN))
    ctes = list(root.find(Kind.CTE))
    tables = sorted({t for s in selects for t in (s.meta.get("tables") or [])})
    writes = list(root.find(Kind.INSERT, Kind.UPDATE, Kind.DELETE_ROWS))

    if level is Level.ELI5:
        if writes:
            return "This query changes data in the database rather than just reading it."
        base = "This asks the database a question"
        if tables:
            base += " about " + _joined(tables)
        if joins:
            base += ", pulling matching rows from more than one table together"
        return base + "."

    if level is Level.BEGINNER:
        parts = [
            f"A {'write' if writes else 'read'} query over "
            + (_joined([f"`{t}`" for t in tables]) or "one table")
            + "."
        ]
        if ctes:
            parts.append(
                f"{len(ctes)} named intermediate result(s) ({_joined([c.name or '' for c in ctes])}) "
                "keep the query readable."
            )
        if joins:
            parts.append(f"{len(joins)} join(s) combine rows across tables.")
        aggregates = [a for s in selects for a in (s.meta.get("aggregates") or [])]
        if aggregates:
            parts.append("It summarises groups of rows using " + _joined(sorted(set(aggregates))) + ".")
        return " ".join(parts)

    parts = [
        f"{len(selects)} SELECT block(s), {len(joins)} join(s), {len(ctes)} CTE(s) over "
        f"{len(tables)} relation(s)."
    ]
    outer = [j.name for j in joins if j.meta.get("is_outer")]
    if outer:
        parts.append(f"Outer joins present ({_joined(outer)}): NULL-extended rows survive.")
    high = [f for f in analysis.findings if f.severity == "high"]
    if high:
        parts.append("Risks: " + _joined([f.title for f in high]) + ".")
    return " ".join(parts)
