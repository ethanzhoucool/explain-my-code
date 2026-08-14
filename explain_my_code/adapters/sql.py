"""SQL -> IR, via sqlglot.

sqlglot attaches source offsets only to leaf tokens (identifiers, literals), so a
clause's span is the union of its descendants' offsets, extended backwards to swallow
the leading keyword. That keeps `WHERE created_at > '2026-01-01'` highlighting as one
clause instead of starting mid-predicate.
"""

from __future__ import annotations

import bisect
import re
from typing import Any

from explain_my_code.adapters.base import register
from explain_my_code.ir import (
    Diagnostic,
    Kind,
    Language,
    Node,
    ParseResult,
    Span,
)

try:
    import sqlglot
    from sqlglot import expressions as exp
    from sqlglot.errors import ParseError

    SQLGLOT_AVAILABLE = True
except ImportError:  # pragma: no cover
    sqlglot = None  # type: ignore[assignment]
    exp = None  # type: ignore[assignment]
    ParseError = Exception  # type: ignore[assignment,misc]
    SQLGLOT_AVAILABLE = False


MAX_REPR = 64

AGGREGATES = {"count", "sum", "avg", "min", "max", "array_agg", "string_agg", "group_concat"}

#: Cost note per join type, surfaced in developer-level explanations.
JOIN_NOTES = {
    "": "keeps only rows that match on both sides",
    "LEFT": "every left row survives, unmatched right columns are NULL",
    "RIGHT": "every right row survives, unmatched left columns are NULL",
    "FULL": "unmatched rows from both sides survive",
    "CROSS": "every left row is paired with every right row",
}


class _Positions:
    """Absolute character offset -> (line, col)."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.line_starts = [0]
        for index, char in enumerate(source):
            if char == "\n":
                self.line_starts.append(index + 1)

    def at(self, offset: int) -> tuple[int, int]:
        offset = max(0, min(offset, len(self.source)))
        line_index = bisect.bisect_right(self.line_starts, offset) - 1
        return line_index + 1, offset - self.line_starts[line_index]

    def span(self, start: int, end: int) -> Span:
        start_line, start_col = self.at(start)
        end_line, end_col = self.at(end)
        return Span(start_line, start_col, end_line, end_col)


def _offsets(expression: Any, exclude: tuple[str, ...] = ()) -> tuple[int, int] | None:
    """Union of every positioned descendant's offsets.

    `exclude` drops named args from the union: a `SELECT` sitting under a `WITH` would
    otherwise claim the CTE's text as part of its own span.
    """
    skipped = {id(expression.args[key]) for key in exclude if expression.args.get(key) is not None}
    start: int | None = None
    end: int | None = None
    stack = [expression]
    while stack:
        current = stack.pop()
        if id(current) in skipped:
            continue
        meta = current.meta
        if "start" in meta and "end" in meta:
            node_start, node_end = meta["start"], meta["end"]
            start = node_start if start is None else min(start, node_start)
            end = node_end if end is None else max(end, node_end)
        for child in current.iter_expressions():
            stack.append(child)
    if start is None or end is None:
        return None
    return start, end + 1


def _arg(expression: Any, key: str) -> Any:
    """sqlglot 30 renamed args that collide with Python keywords (`from` -> `from_`)."""
    value = expression.args.get(key)
    return expression.args.get(f"{key}_") if value is None else value


def _extend_to_keyword(source: str, start: int, keywords: tuple[str, ...]) -> int:
    """Walk the span's start back over a leading clause keyword."""
    window_start = max(0, start - 64)
    window = source[window_start:start]
    best = start
    for keyword in keywords:
        match = None
        # Built outside the f-string: a backslash in an f-string expression is a
        # SyntaxError before Python 3.12, and this package supports 3.11.
        spaced = keyword.replace(" ", r"\s+")
        pattern = r"\b" + spaced + r"\b"
        for candidate in re.finditer(pattern, window, re.IGNORECASE):
            match = candidate
        if match is not None:
            best = min(best, window_start + match.start())
    return best


#: Structural expression -> (IR kind, leading keywords to reclaim).
_CLAUSE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Select": ("SELECT",),
    "From": ("FROM",),
    "Where": ("WHERE",),
    "Group": ("GROUP BY",),
    "Order": ("ORDER BY",),
    "Having": ("HAVING",),
    "Limit": ("LIMIT",),
    "Offset": ("OFFSET",),
    "Join": ("LEFT OUTER JOIN", "RIGHT OUTER JOIN", "FULL OUTER JOIN", "CROSS JOIN",
             "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "INNER JOIN", "JOIN"),
    "With": ("WITH",),
    "CTE": (),
    "Window": ("OVER",),
    "Union": ("UNION ALL", "UNION"),
    "Intersect": ("INTERSECT",),
    "Except": ("EXCEPT",),
    "Insert": ("INSERT INTO", "INSERT"),
    "Update": ("UPDATE",),
    "Delete": ("DELETE FROM", "DELETE"),
    "Create": ("CREATE",),
    "Subquery": (),
    "Case": ("CASE",),
    "Qualify": ("QUALIFY",),
}


class SqlLowerer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.positions = _Positions(source)

    def span_for(self, expression: Any, exclude: tuple[str, ...] = ()) -> Span:
        bounds = _offsets(expression, exclude)
        if bounds is None:
            return Span(1, 0, 1, 0)
        start, end = bounds
        keywords = _CLAUSE_KEYWORDS.get(type(expression).__name__)
        if keywords:
            start = _extend_to_keyword(self.source, start, keywords)
        return self.positions.span(start, end)

    def sql_of(self, expression: Any, limit: int = MAX_REPR) -> str:
        try:
            text = " ".join(expression.sql().split())
        except Exception:
            return ""
        return text if len(text) <= limit else text[: limit - 1] + "…"

    # -- dispatch ---------------------------------------------------------------

    def lower(self, expression: Any) -> list[Node]:
        if expression is None:
            return []
        handler = getattr(self, f"on_{type(expression).__name__}", None)
        if handler is not None:
            result = handler(expression)
            return result if isinstance(result, list) else [result]
        if isinstance(expression, exp.Condition) and isinstance(
            expression, (exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE, exp.Like, exp.ILike)
        ):
            return [self.comparison(expression)]
        if isinstance(expression, (exp.And, exp.Or)):
            return [self.boolean(expression)]
        if isinstance(expression, exp.Func):
            return [self.function(expression)]
        return self.children(expression)

    def children(self, expression: Any) -> list[Node]:
        out: list[Node] = []
        for child in expression.iter_expressions():
            out.extend(self.lower(child))
        return out

    def node(self, expression: Any, kind: Kind, name: str | None, **meta: Any) -> Node:
        return Node(
            kind=kind,
            span=self.span_for(expression),
            name=name,
            meta=meta,
        )

    # -- statements ---------------------------------------------------------------

    def on_Select(self, expression: Any) -> Node:
        projections = expression.expressions or []
        tables = [t.name or t.alias_or_name for t in expression.find_all(exp.Table)]
        joins = expression.args.get("joins") or []
        node = Node(
            kind=Kind.SELECT,
            span=self.span_for(expression, exclude=("with", "with_")),
            name="SELECT",
            meta={
                "projection_count": len(projections),
                "projections": [self.sql_of(p, 32) for p in projections],
                "selects_star": any(isinstance(p, exp.Star) for p in projections),
                "is_distinct": bool(expression.args.get("distinct")),
                "tables": tables,
                "table_count": len(set(tables)),
                "join_count": len(joins),
                "has_where": bool(_arg(expression, "where")),
                "has_group": bool(_arg(expression, "group")),
                "has_order": bool(_arg(expression, "order")),
                "has_limit": bool(_arg(expression, "limit")),
                "aggregates": [
                    type(a).__name__.lower() for a in expression.find_all(exp.AggFunc)
                ],
            },
        )
        # `with` first so a CTE is explained before the query that consumes it.
        for key in ("with", "expressions", "from", "joins", "where", "group", "having",
                    "qualify", "windows", "order", "limit", "offset"):
            value = _arg(expression, key)
            if value is None:
                continue
            for child in value if isinstance(value, list) else [value]:
                if key == "expressions":
                    node.add(self.projection(child))
                else:
                    node.extend(self.lower(child))
        return node

    def projection(self, expression: Any) -> Node:
        alias = expression.alias if isinstance(expression, exp.Alias) else ""
        inner = expression.this if isinstance(expression, exp.Alias) else expression
        node = Node(
            kind=Kind.PROJECTION,
            span=self.span_for(expression),
            name=alias or self.sql_of(expression, 32),
            meta={
                "expression": self.sql_of(inner, 40),
                "alias": alias,
                "is_star": isinstance(inner, exp.Star),
                "is_aggregate": isinstance(inner, exp.AggFunc)
                or bool(list(inner.find_all(exp.AggFunc))),
                "is_column": isinstance(inner, exp.Column),
                "is_window": isinstance(inner, exp.Window),
                "table": inner.table if isinstance(inner, exp.Column) else "",
            },
        )
        node.extend(self.children(expression))
        return node

    def on_From(self, expression: Any) -> Node:
        tables = [self.sql_of(t, 32) for t in expression.find_all(exp.Table)]
        return self.node(
            expression, Kind.FROM, "FROM",
            tables=tables, table_count=len(tables),
            source=self.sql_of(expression.this, 40) if expression.this else "",
            is_subquery=isinstance(expression.this, exp.Subquery),
        )

    def on_Join(self, expression: Any) -> Node:
        side = (expression.side or "").upper()
        join_kind = (expression.kind or "").upper()
        on_clause = expression.args.get("on")
        using = expression.args.get("using")
        label = " ".join(part for part in [side, join_kind, "JOIN"] if part)
        node = self.node(
            expression, Kind.JOIN, label,
            side=side or join_kind,
            table=self.sql_of(expression.this, 32),
            on=self.sql_of(on_clause, 48) if on_clause else "",
            using=[self.sql_of(u, 24) for u in using] if using else [],
            note=JOIN_NOTES.get(side or join_kind, JOIN_NOTES[""]),
            is_cross=join_kind == "CROSS" or (not on_clause and not using),
            is_outer=side in {"LEFT", "RIGHT", "FULL"},
        )
        if on_clause is not None:
            node.extend(self.lower(on_clause))
        return node

    def on_Where(self, expression: Any) -> Node:
        condition = expression.this
        node = self.node(
            expression, Kind.WHERE, "WHERE",
            condition=self.sql_of(condition, 56),
            predicate_count=1 + len(list(condition.find_all(exp.And, exp.Or)))
            if condition is not None
            else 0,
            has_subquery=bool(list(expression.find_all(exp.Subquery))),
            uses_or=bool(list(expression.find_all(exp.Or))),
            is_sargable=not bool(list(expression.find_all(exp.Func))),
        )
        node.extend(self.lower(condition))
        return node

    def on_Group(self, expression: Any) -> Node:
        keys = [self.sql_of(k, 24) for k in expression.expressions]
        return self.node(
            expression, Kind.GROUP_BY, "GROUP BY", keys=keys, key_count=len(keys)
        )

    def on_Having(self, expression: Any) -> Node:
        node = self.node(
            expression, Kind.HAVING, "HAVING",
            condition=self.sql_of(expression.this, 48),
            filters_aggregate=bool(list(expression.find_all(exp.AggFunc))),
        )
        node.extend(self.lower(expression.this))
        return node

    def on_Order(self, expression: Any) -> Node:
        keys = []
        for ordered in expression.expressions:
            direction = "DESC" if ordered.args.get("desc") else "ASC"
            keys.append(f"{self.sql_of(ordered.this, 24)} {direction}")
        return self.node(
            expression, Kind.ORDER_BY, "ORDER BY", keys=keys, key_count=len(keys),
            has_desc=any("DESC" in k for k in keys),
        )

    def on_Limit(self, expression: Any) -> Node:
        return self.node(
            expression, Kind.LIMIT, "LIMIT", count=self.sql_of(expression.expression, 16)
        )

    def on_With(self, expression: Any) -> list[Node]:
        out: list[Node] = []
        for cte in expression.expressions:
            out.extend(self.lower(cte))
        return out

    def on_CTE(self, expression: Any) -> Node:
        node = self.node(
            expression, Kind.CTE, expression.alias,
            cte_name=expression.alias,
            is_recursive=bool(expression.parent and expression.parent.args.get("recursive")),
            body=self.sql_of(expression.this, 48),
        )
        node.extend(self.lower(expression.this))
        return node

    def on_Subquery(self, expression: Any) -> Node:
        node = self.node(
            expression, Kind.SUBQUERY, expression.alias or "subquery",
            alias=expression.alias,
            is_correlated=False,
        )
        node.extend(self.lower(expression.this))
        return node

    def on_Window(self, expression: Any) -> Node:
        partition = [self.sql_of(p, 24) for p in (expression.args.get("partition_by") or [])]
        order = expression.args.get("order")
        node = self.node(
            expression, Kind.WINDOW, "OVER",
            function=self.sql_of(expression.this, 32),
            partition_by=partition,
            order_by=self.sql_of(order, 32) if order else "",
            has_frame=bool(expression.args.get("spec")),
        )
        return node

    def _set_op(self, expression: Any, label: str) -> Node:
        node = self.node(
            expression, Kind.SET_OP, label,
            operation=label,
            deduplicates=label == "UNION",
            branch_count=2,
        )
        node.extend(self.lower(expression.this))
        node.extend(self.lower(expression.expression))
        return node

    def on_Union(self, expression: Any) -> Node:
        return self._set_op(expression, "UNION ALL" if expression.args.get("distinct") is False else "UNION")

    def on_Intersect(self, expression: Any) -> Node:
        return self._set_op(expression, "INTERSECT")

    def on_Except(self, expression: Any) -> Node:
        return self._set_op(expression, "EXCEPT")

    def on_Insert(self, expression: Any) -> Node:
        node = self.node(
            expression, Kind.INSERT, "INSERT",
            table=self.sql_of(expression.this, 32),
            from_select=isinstance(expression.expression, exp.Select),
            column_count=len(expression.this.expressions)
            if hasattr(expression.this, "expressions")
            else 0,
        )
        node.extend(self.lower(expression.expression))
        return node

    def on_Update(self, expression: Any) -> Node:
        assignments = [self.sql_of(e, 32) for e in expression.expressions]
        node = self.node(
            expression, Kind.UPDATE, "UPDATE",
            table=self.sql_of(expression.this, 32),
            assignments=assignments,
            assignment_count=len(assignments),
            has_where=bool(_arg(expression, "where")),
        )
        where = _arg(expression, "where")
        if where is not None:
            node.extend(self.lower(where))
        return node

    def on_Delete(self, expression: Any) -> Node:
        node = self.node(
            expression, Kind.DELETE_ROWS, "DELETE",
            table=self.sql_of(expression.this, 32),
            has_where=bool(_arg(expression, "where")),
        )
        where = _arg(expression, "where")
        if where is not None:
            node.extend(self.lower(where))
        return node

    def on_Create(self, expression: Any) -> Node:
        return self.node(
            expression, Kind.CREATE, self.sql_of(expression.this, 32),
            object_kind=(expression.args.get("kind") or "TABLE").upper(),
            replaces=bool(expression.args.get("replace")),
            if_not_exists=bool(expression.args.get("exists")),
        )

    def on_Case(self, expression: Any) -> Node:
        conditions = expression.args.get("ifs") or []
        node = self.node(
            expression, Kind.SWITCH, "CASE",
            subject=self.sql_of(expression.this, 32) if expression.this else "",
            case_count=len(conditions),
            has_default=bool(expression.args.get("default")),
        )
        for condition in conditions:
            node.add(
                Node(
                    kind=Kind.CASE,
                    span=self.span_for(condition),
                    name="WHEN",
                    meta={
                        "pattern": self.sql_of(condition.this, 32),
                        "result": self.sql_of(condition.args.get("true"), 32),
                        "is_default": False,
                        "has_guard": False,
                    },
                )
            )
        return node

    # -- expressions ---------------------------------------------------------------

    def comparison(self, expression: Any) -> Node:
        operators = {
            "EQ": "=", "NEQ": "<>", "GT": ">", "GTE": ">=", "LT": "<", "LTE": "<=",
            "Like": "LIKE", "ILike": "ILIKE",
        }
        operator = operators.get(type(expression).__name__, "=")
        return Node(
            kind=Kind.COMPARE,
            span=self.span_for(expression),
            name=operator,
            meta={
                "op": operator,
                "op_name": _SQL_OP_NAMES.get(operator, "compares"),
                "left": self.sql_of(expression.this, 24),
                "right": self.sql_of(expression.expression, 24),
                "ops": [operator],
            },
        )

    def boolean(self, expression: Any) -> Node:
        operator = "AND" if isinstance(expression, exp.And) else "OR"
        node = Node(
            kind=Kind.BOOLOP,
            span=self.span_for(expression),
            name=operator,
            meta={
                "op": operator.lower(),
                "operand_count": 2,
                "operands": [
                    self.sql_of(expression.this, 24),
                    self.sql_of(expression.expression, 24),
                ],
            },
        )
        node.extend(self.children(expression))
        return node

    def function(self, expression: Any) -> Node:
        name = type(expression).__name__.lower()
        is_aggregate = isinstance(expression, exp.AggFunc) or name in AGGREGATES
        arguments = list(expression.iter_expressions())
        node = Node(
            kind=Kind.AGGREGATE if is_aggregate else Kind.CALL,
            span=self.span_for(expression),
            name=name.upper(),
            meta={
                "callee": name.upper(),
                "arity": len(arguments),
                "args": [self.sql_of(a, 24) for a in arguments],
                "is_builtin": True,
                "is_distinct": bool(expression.args.get("distinct")),
                "collapses_rows": is_aggregate,
                "cost": "n" if is_aggregate else "",
                "receiver": "",
            },
        )
        return node

    def on_Column(self, expression: Any) -> Node:
        return Node(
            kind=Kind.NAME,
            span=self.span_for(expression),
            name=expression.name,
            meta={"table": expression.table, "qualified": self.sql_of(expression, 32),
                  "ctx": "load"},
        )

    def on_Table(self, expression: Any) -> Node:
        return Node(
            kind=Kind.NAME,
            span=self.span_for(expression),
            name=expression.name,
            meta={"alias": expression.alias, "is_table": True, "ctx": "load"},
        )

    def on_Literal(self, expression: Any) -> Node:
        return Node(
            kind=Kind.LITERAL,
            span=self.span_for(expression),
            name=self.sql_of(expression, 24),
            meta={
                "literal_type": "string" if expression.is_string else "number",
                "value": self.sql_of(expression, 32),
                "is_magic_number": False,
            },
        )

    def on_Star(self, expression: Any) -> Node:
        return Node(
            kind=Kind.LITERAL,
            span=self.span_for(expression),
            name="*",
            meta={"literal_type": "star", "value": "*", "selects_everything": True},
        )


_SQL_OP_NAMES = {
    "=": "matches exactly", "<>": "excludes", ">": "keeps values above",
    ">=": "keeps values at or above", "<": "keeps values below",
    "<=": "keeps values at or below", "LIKE": "matches a text pattern",
    "ILIKE": "matches a text pattern, ignoring case",
}


class SqlAdapter:
    language = Language.SQL
    parser_name = "sqlglot"

    def available(self) -> bool:
        return SQLGLOT_AVAILABLE

    def parse(self, source: str) -> ParseResult:
        lines = source.splitlines()
        root = Node(
            kind=Kind.MODULE,
            span=Span(1, 0, max(len(lines), 1), len(lines[-1]) if lines else 0),
            name="script",
            meta={"line_count": len(lines)},
        )
        if not SQLGLOT_AVAILABLE:
            root.meta["unparsed"] = True
            return ParseResult(
                root, Language.SQL, source,
                [Diagnostic("sqlglot is not installed", severity="error")],
                self.parser_name, degraded=True,
            )

        diagnostics: list[Diagnostic] = []
        try:
            statements = sqlglot.parse(source)
        except ParseError as error:
            diagnostics.append(Diagnostic(f"Could not parse SQL: {error}", severity="error"))
            return ParseResult(
                root, Language.SQL, source, diagnostics, self.parser_name, degraded=True
            )

        lowerer = SqlLowerer(source)
        statements = [s for s in statements if s is not None]
        root.meta["statement_count"] = len(statements)
        for statement in statements:
            root.extend(lowerer.lower(statement))
        return ParseResult(root, Language.SQL, source, diagnostics, self.parser_name)


@register(Language.SQL)
def _factory() -> SqlAdapter:
    return SqlAdapter()
