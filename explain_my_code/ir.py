"""The universal IR every language lowers into.

Five languages, five very different grammars, one explanation phrasebook. That only
works if `python_rules.py` and `java_rules.py` stop being separate universes and agree
on a shared vocabulary of node kinds. A Python `for`, a C++ range-for and a JS
`for...of` are all `Kind.LOOP_FOR` here, carrying the same `meta` slots, so a single
phrase template explains all three.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
from itertools import count
from typing import Any


class Level(str, Enum):
    """Audience the explanation is pitched at."""

    ELI5 = "eli5"
    BEGINNER = "beginner"
    DEVELOPER = "developer"

    @property
    def rank(self) -> int:
        return {"eli5": 0, "beginner": 1, "developer": 2}[self.value]


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    SQL = "sql"


class Kind(str, Enum):
    """Language-neutral node vocabulary.

    Deliberately coarse. Two constructs share a Kind when the same sentence would
    explain both; they differ in `meta`, not in Kind. Adding a language means mapping
    its grammar onto these, never extending this enum for one language's convenience.
    """

    # --- structure -------------------------------------------------------
    MODULE = "module"
    CLASS = "class"
    INTERFACE = "interface"
    FUNCTION = "function"
    METHOD = "method"
    CONSTRUCTOR = "constructor"
    LAMBDA = "lambda"
    PARAM = "param"
    BLOCK = "block"

    # --- control flow ----------------------------------------------------
    BRANCH = "branch"  # if / else-if
    ELSE = "else"
    LOOP_FOR = "loop_for"
    LOOP_FOREACH = "loop_foreach"
    LOOP_WHILE = "loop_while"
    LOOP_DO = "loop_do"
    SWITCH = "switch"
    CASE = "case"
    BREAK = "break"
    CONTINUE = "continue"
    RETURN = "return"
    YIELD = "yield"
    THROW = "throw"
    TRY = "try"
    CATCH = "catch"
    FINALLY = "finally"
    WITH = "with"
    TERNARY = "ternary"
    MATCH = "match"

    # --- data & expressions ----------------------------------------------
    ASSIGN = "assign"
    AUG_ASSIGN = "aug_assign"
    DECL = "decl"
    CALL = "call"
    METHOD_CALL = "method_call"
    ATTRIBUTE = "attribute"
    INDEX = "index"
    SLICE = "slice"
    LITERAL = "literal"
    NAME = "name"
    BINOP = "binop"
    UNOP = "unop"
    COMPARE = "compare"
    BOOLOP = "boolop"
    COMPREHENSION = "comprehension"
    COLLECTION = "collection"
    AWAIT = "await"
    SPREAD = "spread"
    DESTRUCTURE = "destructure"
    NEW = "new"
    DELETE = "delete"
    CAST = "cast"
    POINTER = "pointer"
    REFERENCE = "reference"
    FSTRING = "fstring"

    # --- module system ----------------------------------------------------
    IMPORT = "import"
    EXPORT = "export"
    NAMESPACE = "namespace"
    DECORATOR = "decorator"
    ANNOTATION = "annotation"
    TYPE_PARAM = "type_param"

    # --- sql ---------------------------------------------------------------
    SELECT = "select"
    PROJECTION = "projection"
    FROM = "from"
    JOIN = "join"
    WHERE = "where"
    GROUP_BY = "group_by"
    ORDER_BY = "order_by"
    HAVING = "having"
    LIMIT = "limit"
    INSERT = "insert"
    UPDATE = "update"
    DELETE_ROWS = "delete_rows"
    CREATE = "create"
    CTE = "cte"
    WINDOW = "window"
    SUBQUERY = "subquery"
    SET_OP = "set_op"
    AGGREGATE = "aggregate"

    # --- misc ---------------------------------------------------------------
    COMMENT = "comment"
    UNKNOWN = "unknown"


#: Kinds that introduce a new lexical scope.
SCOPE_KINDS: frozenset[Kind] = frozenset(
    {
        Kind.MODULE,
        Kind.CLASS,
        Kind.FUNCTION,
        Kind.METHOD,
        Kind.CONSTRUCTOR,
        Kind.LAMBDA,
        Kind.COMPREHENSION,
        Kind.NAMESPACE,
    }
)

#: Kinds that are callable definitions.
CALLABLE_KINDS: frozenset[Kind] = frozenset(
    {Kind.FUNCTION, Kind.METHOD, Kind.CONSTRUCTOR, Kind.LAMBDA}
)

#: Kinds that repeat their body. Drives the big-O heuristic and nesting depth.
LOOP_KINDS: frozenset[Kind] = frozenset(
    {Kind.LOOP_FOR, Kind.LOOP_FOREACH, Kind.LOOP_WHILE, Kind.LOOP_DO, Kind.COMPREHENSION}
)

#: Kinds that add a decision point. Drives cyclomatic complexity.
DECISION_KINDS: frozenset[Kind] = frozenset(
    {
        Kind.BRANCH,
        Kind.LOOP_FOR,
        Kind.LOOP_FOREACH,
        Kind.LOOP_WHILE,
        Kind.LOOP_DO,
        Kind.CASE,
        Kind.CATCH,
        Kind.TERNARY,
        Kind.BOOLOP,
        Kind.COMPREHENSION,
    }
)

#: Kinds that increase perceived nesting cost in cognitive complexity.
NESTING_KINDS: frozenset[Kind] = frozenset(
    {
        Kind.BRANCH,
        Kind.ELSE,
        Kind.LOOP_FOR,
        Kind.LOOP_FOREACH,
        Kind.LOOP_WHILE,
        Kind.LOOP_DO,
        Kind.SWITCH,
        Kind.CATCH,
        Kind.TRY,
    }
)


@dataclass(frozen=True, slots=True, order=True)
class Span:
    """A source range. Lines are 1-based, columns 0-based. Editor convention."""

    start_line: int
    start_col: int
    end_line: int
    end_col: int

    @property
    def is_single_line(self) -> bool:
        return self.start_line == self.end_line

    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1

    def contains(self, other: Span) -> bool:
        starts_before = (self.start_line, self.start_col) <= (other.start_line, other.start_col)
        ends_after = (self.end_line, self.end_col) >= (other.end_line, other.end_col)
        return starts_before and ends_after

    def overlaps(self, other: Span) -> bool:
        return (self.start_line, self.start_col) < (other.end_line, other.end_col) and (
            other.start_line,
            other.start_col,
        ) < (self.end_line, self.end_col)

    @property
    def width(self) -> int:
        """Rough size, used to prefer the innermost annotation when spans nest."""
        if self.is_single_line:
            return self.end_col - self.start_col
        return (self.end_line - self.start_line) * 1000 + self.end_col

    def to_dict(self) -> dict[str, int]:
        return {
            "startLine": self.start_line,
            "startCol": self.start_col,
            "endLine": self.end_line,
            "endCol": self.end_col,
        }


_node_ids = count(1)


@dataclass(slots=True)
class Node:
    """One IR node.

    `meta` is the escape hatch that keeps `Kind` small: a loop records its iteration
    variable and iterable there, a call records its callee and arity. Phrase templates
    read `meta` by name, so a template can say "repeat once for every {iterable}"
    without knowing which language produced the node.
    """

    kind: Kind
    span: Span
    name: str | None = None
    text: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    children: list[Node] = field(default_factory=list)
    parent: Node | None = field(default=None, repr=False, compare=False)
    id: int = field(default_factory=lambda: next(_node_ids))

    def add(self, child: Node | None) -> Node:
        if child is not None:
            child.parent = self
            self.children.append(child)
        return self

    def extend(self, children: list[Node]) -> Node:
        for child in children:
            self.add(child)
        return self

    def walk(self) -> Iterator[Node]:
        """Pre-order traversal, self first."""
        yield self
        for child in self.children:
            yield from child.walk()

    def find(self, *kinds: Kind) -> Iterator[Node]:
        wanted = set(kinds)
        for node in self.walk():
            if node.kind in wanted:
                yield node

    def ancestors(self) -> Iterator[Node]:
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    @property
    def enclosing_callable(self) -> Node | None:
        for ancestor in self.ancestors():
            if ancestor.kind in CALLABLE_KINDS:
                return ancestor
        return None

    @property
    def depth(self) -> int:
        return sum(1 for _ in self.ancestors())

    @property
    def loop_depth(self) -> int:
        """How many loops enclose this node. The big-O heuristic's main input."""
        return sum(1 for a in self.ancestors() if a.kind in LOOP_KINDS)

    @property
    def qualified_name(self) -> str:
        parts = [
            a.name for a in reversed(list(self.ancestors())) if a.name and a.kind in SCOPE_KINDS
        ]
        if self.name:
            parts.append(self.name)
        return ".".join(parts)

    def to_dict(self, *, include_children: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "kind": self.kind.value,
            "span": self.span.to_dict(),
        }
        if self.name:
            out["name"] = self.name
        if self.meta:
            out["meta"] = _jsonable(self.meta)
        if include_children and self.children:
            out["children"] = [c.to_dict() for c in self.children]
        return out


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class Source(str, Enum):
    """Where an explanation came from. Surfaced in the UI so AI text is never
    mistaken for a fact derived from the tree."""

    STATIC = "static"  # synthesized from the IR: deterministic
    HEURISTIC = "heuristic"  # pattern match, may be wrong
    LLM = "llm"  # model-generated, grounded in the IR


@dataclass(slots=True)
class Annotation:
    """An explanation attached to a source range, phrased per level."""

    span: Span
    kind: Kind
    texts: dict[Level, str]
    source: Source = Source.STATIC
    confidence: float = 1.0
    node_id: int | None = None
    concepts: list[str] = field(default_factory=list)
    detail: str | None = None

    def text(self, level: Level) -> str:
        if level in self.texts:
            return self.texts[level]
        # Fall back down the ladder: a developer-level phrase beats nothing at all.
        for candidate in sorted(self.texts, key=lambda lv: abs(lv.rank - level.rank)):
            return self.texts[candidate]
        return ""

    def to_dict(self, level: Level | None = None) -> dict[str, Any]:
        out: dict[str, Any] = {
            "span": self.span.to_dict(),
            "kind": self.kind.value,
            "source": self.source.value,
            "confidence": round(self.confidence, 3),
        }
        if level is not None:
            out["text"] = self.text(level)
        else:
            out["texts"] = {lv.value: t for lv, t in self.texts.items()}
        if self.node_id is not None:
            out["nodeId"] = self.node_id
        if self.concepts:
            out["concepts"] = self.concepts
        if self.detail:
            out["detail"] = self.detail
        return out


@dataclass(slots=True)
class Diagnostic:
    """A parse problem. Never fatal. A partial tree still explains most of a file."""

    message: str
    span: Span | None = None
    severity: str = "warning"

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"message": self.message, "severity": self.severity}
        if self.span:
            out["span"] = self.span.to_dict()
        return out


@dataclass(slots=True)
class ParseResult:
    """What a language adapter hands back."""

    root: Node
    language: Language
    source: str
    diagnostics: list[Diagnostic] = field(default_factory=list)
    parser: str = "unknown"
    degraded: bool = False

    @property
    def lines(self) -> list[str]:
        return self.source.splitlines()

    def slice(self, span: Span) -> str:
        lines = self.lines
        if not lines or span.start_line > len(lines):
            return ""
        if span.is_single_line:
            return lines[span.start_line - 1][span.start_col : span.end_col]
        first = lines[span.start_line - 1][span.start_col :]
        middle = lines[span.start_line : span.end_line - 1]
        last = lines[span.end_line - 1][: span.end_col] if span.end_line <= len(lines) else ""
        return "\n".join([first, *middle, last])


def span_of_line(line_no: int, text: str) -> Span:
    return Span(line_no, 0, line_no, len(text))


def reset_node_ids() -> None:
    """Test helper: make node ids deterministic across runs."""
    global _node_ids
    _node_ids = count(1)
