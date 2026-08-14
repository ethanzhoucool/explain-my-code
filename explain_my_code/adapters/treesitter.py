"""Shared tree-sitter lowering machinery for JavaScript, Java and C++.

Each language contributes two tables (a node-type -> `Kind` map and a set of meta
extractors) and inherits everything else: span arithmetic, header-span trimming,
transparent pass-through of grammar-internal nodes, and error recovery.

Tree-sitter reports rows 0-based; the IR is 1-based, so every span conversion goes
through `_span`. Getting that wrong shifts every annotation by a line, which is why
it lives in exactly one place.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from explain_my_code.ir import Diagnostic, Kind, Language, Node, ParseResult, Span

try:  # pragma: no cover - exercised only when the wheel is missing
    from tree_sitter import Language as TSLanguage
    from tree_sitter import Node as TSNode
    from tree_sitter import Parser as TSParser

    TREE_SITTER_AVAILABLE = True
except ImportError:  # pragma: no cover
    TSNode = Any  # type: ignore[assignment,misc]
    TSLanguage = None  # type: ignore[assignment]
    TSParser = None  # type: ignore[assignment]
    TREE_SITTER_AVAILABLE = False


MAX_REPR = 64

#: Child node types that mean "the body starts here". Used to trim header spans so a
#: hover targets `if (x > 0)` rather than the whole 30-line block beneath it.
BODY_TYPES = frozenset(
    {
        "statement_block",
        "compound_statement",
        "block",
        "class_body",
        "declaration_list",
        "field_declaration_list",
        "constructor_body",
        "switch_body",
        "switch_block",
        "enum_body",
        "interface_body",
    }
)

BODY_FIELDS = ("body", "consequence", "block")

#: Operators that make a `binary_expression` a comparison rather than arithmetic.
COMPARISON_OPS = frozenset({"==", "!=", "===", "!==", "<", "<=", ">", ">=", "instanceof", "in"})
LOGICAL_OPS = frozenset({"&&", "||", "and", "or", "??"})

OP_NAMES = {
    "+": "adds", "-": "subtracts", "*": "multiplies", "/": "divides",
    "%": "takes the remainder", "**": "raises to a power",
    "==": "checks equality", "===": "checks strict equality",
    "!=": "checks inequality", "!==": "checks strict inequality",
    "<": "checks less-than", "<=": "checks less-than-or-equal",
    ">": "checks greater-than", ">=": "checks greater-than-or-equal",
    "&&": "requires both sides", "||": "accepts either side",
    "??": "falls back when the left side is null",
    "<<": "shifts bits left", ">>": "shifts bits right",
    "&": "combines bits with AND", "|": "combines bits with OR", "^": "combines bits with XOR",
    "instanceof": "checks the runtime type", "in": "checks membership",
}


def _span(ts_node: TSNode) -> Span:
    start_row, start_col = ts_node.start_point
    end_row, end_col = ts_node.end_point
    return Span(start_row + 1, start_col, end_row + 1, end_col)


def _text(ts_node: TSNode | None, limit: int = MAX_REPR) -> str:
    if ts_node is None:
        return ""
    raw = ts_node.text
    if raw is None:
        return ""
    value = " ".join(raw.decode("utf-8", "replace").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _field(ts_node: TSNode, name: str) -> TSNode | None:
    try:
        return ts_node.child_by_field_name(name)
    except Exception:  # pragma: no cover - defensive
        return None


def _field_text(ts_node: TSNode, name: str, limit: int = MAX_REPR) -> str:
    return _text(_field(ts_node, name), limit)


def _find_body(ts_node: TSNode) -> TSNode | None:
    for field_name in BODY_FIELDS:
        child = _field(ts_node, field_name)
        if child is not None:
            return child
    for child in ts_node.named_children:
        if child.type in BODY_TYPES:
            return child
    return None


def _header_span(ts_node: TSNode) -> Span:
    """Span covering the construct's header only."""
    full = _span(ts_node)
    body = _find_body(ts_node)
    if body is not None:
        body_row, body_col = body.start_point
        if body_row + 1 > full.start_line:
            return Span(full.start_line, full.start_col, body_row, 10_000)
        if body_col > full.start_col:
            return Span(full.start_line, full.start_col, body_row + 1, body_col)
    if not full.is_single_line:
        return Span(full.start_line, full.start_col, full.start_line, 10_000)
    return full


def _children_of_type(ts_node: TSNode, *types: str) -> list[TSNode]:
    wanted = set(types)
    return [c for c in ts_node.named_children if c.type in wanted]


def _descendants_of_type(ts_node: TSNode, *types: str, stop: Iterable[str] = ()) -> list[TSNode]:
    """Collect matching descendants without crossing a `stop` boundary."""
    wanted, barriers = set(types), set(stop)
    out: list[TSNode] = []
    stack = list(ts_node.named_children)
    while stack:
        node = stack.pop()
        if node.type in wanted:
            out.append(node)
        if node.type in barriers:
            continue
        stack.extend(node.named_children)
    return out


MetaFn = Callable[[TSNode, str], dict[str, Any]]


class TreeSitterAdapter:
    """Base adapter. Subclasses supply the tables; this class supplies the walk."""

    language: Language
    parser_name: str
    #: node type -> IR kind. Types absent from this map are transparent: the walker
    #: descends through them without emitting a node.
    KINDS: dict[str, Kind] = {}
    #: node types to skip entirely, children included (modifiers, type noise).
    OPAQUE: frozenset[str] = frozenset()
    #: node types treated as leaves: emitted, but not recursed into.
    LEAVES: frozenset[str] = frozenset()
    COMMENT_TYPES: frozenset[str] = frozenset({"comment"})
    LITERAL_TYPES: frozenset[str] = frozenset()
    #: functions the phrasebook may describe as well-known.
    BUILTINS: frozenset[str] = frozenset()
    KNOWN_COSTS: dict[str, str] = {}

    def __init__(self) -> None:
        self._parser: TSParser | None = None
        self._load_error: str | None = None

    # -- grammar plumbing -----------------------------------------------------

    def _grammar(self) -> Any:  # pragma: no cover - overridden
        raise NotImplementedError

    def _get_parser(self) -> TSParser | None:
        if self._parser is not None:
            return self._parser
        if not TREE_SITTER_AVAILABLE:
            self._load_error = "tree-sitter is not installed"
            return None
        try:
            self._parser = TSParser(TSLanguage(self._grammar()))
        except Exception as exc:  # pragma: no cover - wheel/ABI mismatch
            self._load_error = f"grammar failed to load: {exc}"
            return None
        return self._parser

    def available(self) -> bool:
        return self._get_parser() is not None

    # -- entry ----------------------------------------------------------------

    def parse(self, source: str) -> ParseResult:
        parser = self._get_parser()
        lines = source.splitlines()
        if parser is None:
            root = Node(
                kind=Kind.MODULE,
                span=Span(1, 0, max(len(lines), 1), 0),
                name="module",
                meta={"unparsed": True},
            )
            return ParseResult(
                root,
                self.language,
                source,
                [Diagnostic(self._load_error or "parser unavailable", severity="error")],
                self.parser_name,
                degraded=True,
            )

        tree = parser.parse(source.encode("utf-8"))
        diagnostics = self._collect_errors(tree.root_node)
        root = Node(
            kind=Kind.MODULE,
            span=Span(1, 0, max(len(lines), 1), len(lines[-1]) if lines else 0),
            name="module",
            meta={"line_count": len(lines), "statement_count": len(tree.root_node.named_children)},
        )
        for child in tree.root_node.named_children:
            root.extend(self.lower(child))
        return ParseResult(
            root,
            self.language,
            source,
            diagnostics,
            self.parser_name,
            degraded=any(d.severity == "error" for d in diagnostics),
        )

    def _collect_errors(self, ts_root: TSNode, limit: int = 8) -> list[Diagnostic]:
        """Tree-sitter always returns a tree; ERROR nodes mark what it could not read.

        Reported as warnings, not failures. The surrounding code still explains fine.
        """
        if not ts_root.has_error:
            return []
        out: list[Diagnostic] = []
        stack = [ts_root]
        while stack and len(out) < limit:
            node = stack.pop()
            if node.type == "ERROR" or node.is_missing:
                label = "missing " + node.type if node.is_missing else "could not parse"
                out.append(Diagnostic(f"{label} near here", _span(node), "warning"))
                continue
            if node.has_error:
                stack.extend(node.children)
        return out

    # -- the walk --------------------------------------------------------------

    def lower(self, ts_node: TSNode) -> list[Node]:
        node_type = ts_node.type
        if node_type in self.OPAQUE:
            return []
        if node_type in self.COMMENT_TYPES:
            text = _text(ts_node, 200).lstrip("/*# ").rstrip("*/ ")
            return [
                Node(
                    kind=Kind.COMMENT,
                    span=_span(ts_node),
                    name=text[:80],
                    meta={
                        "text": text,
                        "is_todo": text.upper().startswith(("TODO", "FIXME", "HACK", "XXX")),
                    },
                )
            ]

        kind = self.kind_for(ts_node)
        if kind is None:
            out: list[Node] = []
            for child in ts_node.named_children:
                out.extend(self.lower(child))
            return out

        node = Node(
            kind=kind,
            span=self.span_for(ts_node, kind),
            name=self.name_for(ts_node, kind),
            meta=self.meta_for(ts_node, kind),
        )
        node.extend(self.synth_children(ts_node, kind))
        if node_type not in self.LEAVES:
            for child in self.recurse_into(ts_node, kind):
                node.extend(self.lower(child))
        return [node]

    def synth_children(self, ts_node: TSNode, kind: Kind) -> list[Node]:
        """IR children with no 1:1 grammar node: parameters, mostly.

        Grammars disagree wildly on parameter shape (`formal_parameters` holding bare
        identifiers in JS, real `formal_parameter` nodes in Java, `parameter_declaration`
        in C++). Synthesizing PARAM here means the phrasebook sees one shape.
        """
        return []

    def recurse_into(self, ts_node: TSNode, kind: Kind) -> list[TSNode]:
        """Children to descend into.

        The `name` field is dropped: it is already the node's `name`, and emitting it
        again as a NAME child buries every definition under a duplicate of itself.
        """
        name_field = _field(ts_node, "name")
        if name_field is None:
            return list(ts_node.named_children)
        return [c for c in ts_node.named_children if c is not name_field]

    def _param_nodes(self, ts_node: TSNode, owner: str, params: list[dict[str, Any]]) -> list[Node]:
        holder = _field(ts_node, "parameters") or _field(ts_node, "declarator")
        if holder is None:
            return []
        candidates = [
            c
            for c in holder.named_children
            if c.type
            in {
                "identifier", "formal_parameter", "parameter_declaration",
                "required_parameter", "optional_parameter", "assignment_pattern",
                "rest_pattern", "spread_parameter", "object_pattern", "array_pattern",
                "variadic_parameter",
            }
        ]
        out: list[Node] = []
        for ts_param, param in zip(candidates, params, strict=False):
            out.append(
                Node(
                    kind=Kind.PARAM,
                    span=_span(ts_param),
                    name=str(param.get("name") or _text(ts_param, 32)),
                    meta={**param, "owner": owner},
                )
            )
        return out

    def span_for(self, ts_node: TSNode, kind: Kind) -> Span:
        if _find_body(ts_node) is not None or not _span(ts_node).is_single_line:
            return _header_span(ts_node)
        return _span(ts_node)

    def kind_for(self, ts_node: TSNode) -> Kind | None:
        node_type = ts_node.type
        if node_type in self.LITERAL_TYPES:
            return Kind.LITERAL
        kind = self.KINDS.get(node_type)
        if kind is Kind.BINOP:
            return self._binary_kind(ts_node)
        return kind

    def _binary_kind(self, ts_node: TSNode) -> Kind:
        op = _text(_field(ts_node, "operator"), 8)
        if op in COMPARISON_OPS:
            return Kind.COMPARE
        if op in LOGICAL_OPS:
            return Kind.BOOLOP
        return Kind.BINOP

    def name_for(self, ts_node: TSNode, kind: Kind) -> str | None:
        # Control-flow constructs keep their keyword label even when the grammar hangs a
        # `name` field off them (Java's `enhanced_for_statement` names the loop variable).
        if kind in _DEFAULT_NAMES and kind not in {Kind.NEW, Kind.AWAIT}:
            return _DEFAULT_NAMES[kind]
        named = _field_text(ts_node, "name", 48)
        if named:
            return named
        if kind in {Kind.BINOP, Kind.COMPARE, Kind.BOOLOP, Kind.UNOP}:
            return _field_text(ts_node, "operator", 8) or None
        if kind is Kind.NAME:
            return _text(ts_node, 48)
        return _DEFAULT_NAMES.get(kind)

    # -- meta ------------------------------------------------------------------

    def meta_for(self, ts_node: TSNode, kind: Kind) -> dict[str, Any]:
        base = _COMMON_META.get(kind)
        meta = base(self, ts_node) if base else {}
        hook = getattr(self, f"meta_{kind.value}", None)
        if hook is not None:
            meta.update(hook(ts_node))
        return meta

    # -- shared meta builders ---------------------------------------------------

    def _meta_call(self, ts_node: TSNode) -> dict[str, Any]:
        func = _field(ts_node, "function") or _field(ts_node, "constructor")
        args = _field(ts_node, "arguments")
        arg_nodes = list(args.named_children) if args is not None else []
        callee = _text(func, 48)
        receiver = ""
        if func is not None and func.type in {"member_expression", "field_expression"}:
            receiver = _field_text(func, "object", 32)
            callee = _field_text(func, "property", 32) or _field_text(func, "field", 32) or callee
        return {
            "callee": callee,
            "receiver": receiver,
            "arity": len(arg_nodes),
            "args": [_text(a, 24) for a in arg_nodes],
            "is_builtin": callee in self.BUILTINS,
            "cost": self.KNOWN_COSTS.get(callee, ""),
            "qualified": _text(func, 48),
        }

    def _meta_binary(self, ts_node: TSNode) -> dict[str, Any]:
        op = _field_text(ts_node, "operator", 8)
        return {
            "op": op,
            "op_name": OP_NAMES.get(op, "combines"),
            "left": _field_text(ts_node, "left", 24),
            "right": _field_text(ts_node, "right", 24),
            "operands": [_field_text(ts_node, "left", 24), _field_text(ts_node, "right", 24)],
            "operand_count": 2,
        }

    def _meta_unary(self, ts_node: TSNode) -> dict[str, Any]:
        return {
            "op": _field_text(ts_node, "operator", 8),
            "operand": _field_text(ts_node, "argument", 32)
            or _field_text(ts_node, "operand", 32),
        }

    def _meta_assign(self, ts_node: TSNode) -> dict[str, Any]:
        left = _field_text(ts_node, "left", 32)
        right = _field(ts_node, "right")
        from_call = ""
        if right is not None and right.type in {"call_expression", "method_invocation"}:
            from_call = self._meta_call(right)["callee"]
        return {
            "targets": [left],
            "target": left,
            "value": _text(right, 48),
            "value_kind": right.type if right is not None else "",
            "from_call": from_call,
            "is_multiple": False,
        }

    def _meta_branch(self, ts_node: TSNode) -> dict[str, Any]:
        condition = _field_text(ts_node, "condition", 56)
        alternative = _field(ts_node, "alternative")
        body = _field(ts_node, "consequence")
        is_guard = False
        if body is not None and alternative is None:
            statements = list(body.named_children) or [body]
            is_guard = len(statements) == 1 and statements[0].type in {
                "return_statement", "break_statement", "continue_statement", "throw_statement",
            }
        return {
            "condition": condition.strip("()"),
            "has_else": alternative is not None,
            "is_elif": alternative is not None and alternative.type == "if_statement",
            "is_guard": is_guard,
        }

    def _meta_while(self, ts_node: TSNode) -> dict[str, Any]:
        condition = _field_text(ts_node, "condition", 56).strip("()")
        return {
            "condition": condition,
            "is_infinite": condition in {"true", "1"},
            "has_break": bool(
                _descendants_of_type(
                    ts_node, "break_statement",
                    stop=("while_statement", "for_statement", "switch_statement"),
                )
            ),
        }

    def _meta_classic_for(self, ts_node: TSNode) -> dict[str, Any]:
        return {
            "init": _field_text(ts_node, "initializer", 32) or _field_text(ts_node, "init", 32),
            "condition": _field_text(ts_node, "condition", 32).rstrip(";"),
            "update": _field_text(ts_node, "update", 32) or _field_text(ts_node, "increment", 32),
            "counted": True,
        }

    def _meta_foreach(self, ts_node: TSNode) -> dict[str, Any]:
        return {
            "target": _field_text(ts_node, "left", 32) or _field_text(ts_node, "name", 32),
            "iterable": _field_text(ts_node, "right", 40) or _field_text(ts_node, "value", 40),
            "counted": False,
        }

    def _meta_return(self, ts_node: TSNode) -> dict[str, Any]:
        value = list(ts_node.named_children)
        return {
            "value": _text(value[0], 48) if value else "",
            "is_bare": not value,
        }

    def _meta_member(self, ts_node: TSNode) -> dict[str, Any]:
        return {
            "object": _field_text(ts_node, "object", 32),
            "attribute": _field_text(ts_node, "property", 32) or _field_text(ts_node, "field", 32),
        }

    def _meta_index(self, ts_node: TSNode) -> dict[str, Any]:
        return {
            "container": _field_text(ts_node, "object", 32) or _field_text(ts_node, "array", 32),
            "key": _field_text(ts_node, "index", 24) or _field_text(ts_node, "argument", 24),
            "is_slice": False,
        }

    def _meta_ternary(self, ts_node: TSNode) -> dict[str, Any]:
        return {
            "condition": _field_text(ts_node, "condition", 40),
            "when_true": _field_text(ts_node, "consequence", 32),
            "when_false": _field_text(ts_node, "alternative", 32),
        }

    def _meta_throw(self, ts_node: TSNode) -> dict[str, Any]:
        inner = ts_node.named_children[0] if ts_node.named_children else None
        exception = ""
        message = ""
        if inner is not None:
            if inner.type in {"new_expression", "object_creation_expression"}:
                exception = _field_text(inner, "constructor", 32) or _field_text(inner, "type", 32)
                args = _field(inner, "arguments")
                if args is not None and args.named_children:
                    message = _text(args.named_children[0], 40)
            else:
                exception = _text(inner, 32)
        return {"exception": exception, "message": message, "reraises": inner is None}

    def _meta_try(self, ts_node: TSNode) -> dict[str, Any]:
        handlers = _children_of_type(ts_node, "catch_clause")
        return {
            "handler_count": len(handlers),
            "has_finally": bool(_children_of_type(ts_node, "finally_clause")),
            "caught": [self._catch_type(h) or "everything" for h in handlers],
        }

    def _catch_type(self, ts_node: TSNode) -> str:
        param = _field(ts_node, "parameter")
        if param is None:
            return ""
        return _text(param, 40)

    def _meta_catch(self, ts_node: TSNode) -> dict[str, Any]:
        caught = self._catch_type(ts_node)
        return {"exception": caught, "is_bare": not caught, "binds": caught}

    def _meta_literal(self, ts_node: TSNode) -> dict[str, Any]:
        value = _text(ts_node, 32)
        literal_type = _LITERAL_TYPE_HINTS.get(ts_node.type, ts_node.type)
        is_magic = False
        if literal_type in {"number", "int", "float"}:
            try:
                numeric = float(value.rstrip("fFlLuU"))
                is_magic = numeric not in (0, 1, -1, 2, 100)
            except ValueError:
                is_magic = False
        return {"literal_type": literal_type, "value": value, "is_magic_number": is_magic}

    def _meta_switch(self, ts_node: TSNode) -> dict[str, Any]:
        body = _find_body(ts_node)
        cases = (
            _children_of_type(body, "switch_case", "switch_default",
                              "switch_block_statement_group", "case_statement")
            if body is not None
            else []
        )
        return {
            "subject": _field_text(ts_node, "value", 40) or _field_text(ts_node, "condition", 40),
            "case_count": len(cases),
        }

    def _meta_collection(self, ts_node: TSNode) -> dict[str, Any]:
        size = len(ts_node.named_children)
        return {
            "collection_type": _COLLECTION_HINTS.get(ts_node.type, "collection"),
            "size": size,
            "is_empty": size == 0,
            "value": _text(ts_node, 40),
        }

    def _meta_new(self, ts_node: TSNode) -> dict[str, Any]:
        args = _field(ts_node, "arguments")
        return {
            "type": _field_text(ts_node, "constructor", 32) or _field_text(ts_node, "type", 32),
            "arity": len(args.named_children) if args is not None else 0,
        }


_DEFAULT_NAMES: dict[Kind, str] = {
    Kind.BRANCH: "if",
    Kind.ELSE: "else",
    Kind.LOOP_FOR: "for",
    Kind.LOOP_FOREACH: "for-each",
    Kind.LOOP_WHILE: "while",
    Kind.LOOP_DO: "do-while",
    Kind.SWITCH: "switch",
    Kind.CASE: "case",
    Kind.BREAK: "break",
    Kind.CONTINUE: "continue",
    Kind.RETURN: "return",
    Kind.YIELD: "yield",
    Kind.THROW: "throw",
    Kind.TRY: "try",
    Kind.CATCH: "catch",
    Kind.FINALLY: "finally",
    Kind.AWAIT: "await",
    Kind.LAMBDA: "lambda",
    Kind.TERNARY: "conditional",
    Kind.SPREAD: "spread",
    Kind.DELETE: "delete",
    Kind.NEW: "new",
    Kind.WITH: "with",
}

_LITERAL_TYPE_HINTS = {
    "number": "number",
    "number_literal": "number",
    "decimal_integer_literal": "int",
    "decimal_floating_point_literal": "float",
    "hex_integer_literal": "int",
    "string": "string",
    "string_literal": "string",
    "char_literal": "char",
    "character_literal": "char",
    "true": "bool",
    "false": "bool",
    "null": "null",
    "null_literal": "null",
    "nullptr": "null",
    "undefined": "undefined",
    "regex": "regex",
}

_COLLECTION_HINTS = {
    "array": "array",
    "object": "object",
    "array_initializer": "array",
    "initializer_list": "list",
}

#: Kind -> shared meta builder. Language subclasses override with `meta_<kind>` hooks.
_COMMON_META: dict[Kind, Callable[[TreeSitterAdapter, TSNode], dict[str, Any]]] = {
    Kind.CALL: TreeSitterAdapter._meta_call,
    Kind.METHOD_CALL: TreeSitterAdapter._meta_call,
    Kind.BINOP: TreeSitterAdapter._meta_binary,
    Kind.COMPARE: TreeSitterAdapter._meta_binary,
    Kind.BOOLOP: TreeSitterAdapter._meta_binary,
    Kind.UNOP: TreeSitterAdapter._meta_unary,
    Kind.ASSIGN: TreeSitterAdapter._meta_assign,
    Kind.AUG_ASSIGN: TreeSitterAdapter._meta_assign,
    Kind.BRANCH: TreeSitterAdapter._meta_branch,
    Kind.LOOP_WHILE: TreeSitterAdapter._meta_while,
    Kind.LOOP_DO: TreeSitterAdapter._meta_while,
    Kind.LOOP_FOR: TreeSitterAdapter._meta_classic_for,
    Kind.LOOP_FOREACH: TreeSitterAdapter._meta_foreach,
    Kind.RETURN: TreeSitterAdapter._meta_return,
    Kind.ATTRIBUTE: TreeSitterAdapter._meta_member,
    Kind.INDEX: TreeSitterAdapter._meta_index,
    Kind.TERNARY: TreeSitterAdapter._meta_ternary,
    Kind.THROW: TreeSitterAdapter._meta_throw,
    Kind.TRY: TreeSitterAdapter._meta_try,
    Kind.CATCH: TreeSitterAdapter._meta_catch,
    Kind.LITERAL: TreeSitterAdapter._meta_literal,
    Kind.SWITCH: TreeSitterAdapter._meta_switch,
    Kind.COLLECTION: TreeSitterAdapter._meta_collection,
    Kind.NEW: TreeSitterAdapter._meta_new,
}
