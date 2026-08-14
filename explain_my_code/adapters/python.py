"""Python -> IR, via the standard library `ast` module.

The stdlib parser is the whole point: it gives exact spans, real scoping, and it is
never fooled by a keyword inside a string literal the way the v1 regex rules were.
Comments are recovered separately through `tokenize`, since `ast` discards them.
"""

from __future__ import annotations

import ast
import io
import tokenize

from explain_my_code.adapters.base import register
from explain_my_code.ir import (
    Diagnostic,
    Kind,
    Language,
    Node,
    ParseResult,
    Span,
)

MAX_REPR = 64

#: Builtins worth calling out by name in explanations.
NOTABLE_BUILTINS = {
    "print", "len", "range", "enumerate", "zip", "map", "filter", "sorted", "sum",
    "min", "max", "abs", "round", "open", "input", "int", "str", "float", "bool",
    "list", "dict", "set", "tuple", "any", "all", "reversed", "isinstance", "type",
    "super", "getattr", "setattr", "hasattr", "format", "repr", "iter", "next",
}

#: Calls whose cost dominates a loop body, used by the complexity heuristic.
KNOWN_COSTS = {
    "sorted": "n log n",
    "sort": "n log n",
    "min": "n",
    "max": "n",
    "sum": "n",
    "len": "1",
    "index": "n",
    "count": "n",
    "reverse": "n",
    "copy": "n",
    "deepcopy": "n",
}


def _span(node: ast.AST) -> Span:
    start_line = getattr(node, "lineno", 1)
    start_col = getattr(node, "col_offset", 0)
    end_line = getattr(node, "end_lineno", None) or start_line
    end_col = getattr(node, "end_col_offset", None)
    if end_col is None:
        end_col = start_col + 1
    return Span(start_line, start_col, end_line, end_col)


def _header_span(node: ast.AST, body_attr: str = "body") -> Span:
    """Span covering just the header line(s) of a compound statement.

    Highlighting a 40-line function body as one blob is useless; highlighting `def
    solve(grid):` is the thing a reader actually hovers.
    """
    full = _span(node)
    body = getattr(node, body_attr, None)
    if isinstance(body, list) and body:
        first_stmt_line = getattr(body[0], "lineno", full.start_line)
        if first_stmt_line > full.start_line:
            return Span(full.start_line, full.start_col, first_stmt_line - 1, 10_000)
    return Span(full.start_line, full.start_col, full.start_line, 10_000)


def _repr(node: ast.AST | None, limit: int = MAX_REPR) -> str:
    if node is None:
        return ""
    try:
        text = ast.unparse(node)
    except Exception:
        return ""
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _callee_name(func: ast.expr) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Subscript):
        return _callee_name(func.value)
    if isinstance(func, ast.Call):
        return _callee_name(func.func)
    return _repr(func, 32)


def _params(args: ast.arguments) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    positional = [*getattr(args, "posonlyargs", []), *args.args]
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(args.defaults))
    defaults += list(args.defaults)
    for arg, default in zip(positional, defaults, strict=False):
        out.append(
            {
                "name": arg.arg,
                "annotation": _repr(arg.annotation, 32),
                "default": _repr(default, 24),
                "variadic": None,
            }
        )
    if args.vararg:
        out.append(
            {"name": args.vararg.arg, "annotation": _repr(args.vararg.annotation, 32),
             "default": "", "variadic": "args"}
        )
    for arg, kwdefault in zip(args.kwonlyargs, args.kw_defaults, strict=False):
        out.append(
            {"name": arg.arg, "annotation": _repr(arg.annotation, 32),
             "default": _repr(kwdefault, 24), "variadic": None}
        )
    if args.kwarg:
        out.append(
            {"name": args.kwarg.arg, "annotation": _repr(args.kwarg.annotation, 32),
             "default": "", "variadic": "kwargs"}
        )
    return out


_FUNC_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def _is_generator(fn: ast.AST) -> bool:
    """True when the body yields.

    Stops at nested function boundaries — a `yield` inside an inner generator does not
    make the outer function a generator.
    """
    stack: list[ast.AST] = list(ast.iter_child_nodes(fn))
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.Yield, ast.YieldFrom)):
            return True
        if isinstance(node, _FUNC_NODES):
            continue
        stack.extend(ast.iter_child_nodes(node))
    return False


def _docstring(node: ast.AST) -> str:
    try:
        doc = ast.get_docstring(node)  # type: ignore[arg-type]
    except TypeError:
        return ""
    if not doc:
        return ""
    first = doc.strip().split("\n")[0]
    return first if len(first) <= 120 else first[:119] + "…"


class PythonLowerer:
    """Walks the CPython AST and emits IR nodes.

    One `visit_*` per construct that deserves its own explanation. Everything else
    falls through to `generic`, which keeps children flowing without inventing a node.
    """

    def __init__(self, source: str) -> None:
        self.source = source
        self.lines = source.splitlines()

    # -- entry ---------------------------------------------------------------

    def lower(self, tree: ast.Module) -> Node:
        end_line = max(len(self.lines), 1)
        root = Node(
            kind=Kind.MODULE,
            span=Span(1, 0, end_line, len(self.lines[-1]) if self.lines else 0),
            name="module",
            meta={
                "docstring": _docstring(tree),
                "statement_count": len(tree.body),
                "line_count": len(self.lines),
            },
        )
        root.extend(self.visit_body(tree.body, owns_docstring=True))
        return root

    def visit_body(self, body: list[ast.stmt], *, owns_docstring: bool = False) -> list[Node]:
        if owns_docstring and body and _is_docstring_stmt(body[0]):
            body[0]._emc_is_docstring = True  # type: ignore[attr-defined]
        out: list[Node] = []
        for stmt in body:
            out.extend(self.visit(stmt))
        return out

    def visit(self, node: ast.AST) -> list[Node]:
        handler = getattr(self, f"visit_{type(node).__name__}", None)
        if handler is not None:
            result = handler(node)
            if result is None:
                return []
            return result if isinstance(result, list) else [result]
        return self.generic(node)

    def generic(self, node: ast.AST) -> list[Node]:
        out: list[Node] = []
        for child in ast.iter_child_nodes(node):
            out.extend(self.visit(child))
        return out

    def children_of(self, node: ast.AST) -> list[Node]:
        return self.generic(node)

    # -- definitions ----------------------------------------------------------

    def _function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> list[Node]:
        parent_is_class = getattr(node, "_emc_in_class", False)
        kind = Kind.METHOD if parent_is_class else Kind.FUNCTION
        if parent_is_class and node.name in {"__init__", "__new__"}:
            kind = Kind.CONSTRUCTOR
        params = _params(node.args)
        decorators = [_repr(d, 32) for d in node.decorator_list]
        fn = Node(
            kind=kind,
            span=_header_span(node),
            name=node.name,
            meta={
                "params": params,
                "param_count": len(params),
                "param_names": [p["name"] for p in params],
                "is_async": is_async,
                "is_generator": _is_generator(node),
                "decorators": decorators,
                "returns": _repr(node.returns, 32),
                "docstring": _docstring(node),
                "full_span": _span(node).to_dict(),
                "body_lines": _span(node).line_count,
                "is_dunder": node.name.startswith("__") and node.name.endswith("__"),
                "is_private": node.name.startswith("_") and not node.name.startswith("__"),
            },
        )
        for deco, text in zip(node.decorator_list, decorators, strict=False):
            fn.add(
                Node(
                    kind=Kind.DECORATOR,
                    span=_span(deco),
                    name=text,
                    meta={"target": node.name, "target_kind": kind.value},
                )
            )
        # Ragged on purpose: `params` also carries *args/**kwargs, which have no
        # matching `ast.arg` in this list, so the shorter side wins.
        for arg, param in zip(
            [*getattr(node.args, "posonlyargs", []), *node.args.args, *node.args.kwonlyargs],
            [p for p in params if p["variadic"] is None],
            strict=False,
        ):
            fn.add(
                Node(
                    kind=Kind.PARAM,
                    span=_span(arg),
                    name=arg.arg,
                    meta={**param, "owner": node.name},
                )
            )
        fn.extend(self.visit_body(node.body, owns_docstring=True))
        return [fn]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> list[Node]:
        return self._function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> list[Node]:
        return self._function(node, is_async=True)

    def visit_ClassDef(self, node: ast.ClassDef) -> list[Node]:
        bases = [_repr(b, 32) for b in node.bases]
        decorators = [_repr(d, 32) for d in node.decorator_list]
        methods = [
            s.name
            for s in node.body
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        cls = Node(
            kind=Kind.CLASS,
            span=_header_span(node),
            name=node.name,
            meta={
                "bases": bases,
                "decorators": decorators,
                "docstring": _docstring(node),
                "method_names": methods,
                "method_count": len(methods),
                "is_dataclass": any("dataclass" in d for d in decorators),
                "is_subclass": bool(bases),
                "full_span": _span(node).to_dict(),
            },
        )
        for deco, text in zip(node.decorator_list, decorators, strict=False):
            cls.add(
                Node(
                    kind=Kind.DECORATOR,
                    span=_span(deco),
                    name=text,
                    meta={"target": node.name, "target_kind": "class"},
                )
            )
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stmt._emc_in_class = True  # type: ignore[attr-defined]
        cls.extend(self.visit_body(node.body, owns_docstring=True))
        return [cls]

    def visit_Lambda(self, node: ast.Lambda) -> list[Node]:
        params = _params(node.args)
        lam = Node(
            kind=Kind.LAMBDA,
            span=_span(node),
            name="lambda",
            meta={
                "params": params,
                "param_names": [p["name"] for p in params],
                "param_count": len(params),
                "body": _repr(node.body, 48),
            },
        )
        lam.extend(self.visit(node.body))
        return [lam]

    # -- control flow ----------------------------------------------------------

    def visit_If(self, node: ast.If) -> list[Node]:
        is_elif = getattr(node, "_emc_is_elif", False)
        branch = Node(
            kind=Kind.BRANCH,
            span=_header_span(node),
            name="if",
            meta={
                "condition": _repr(node.test),
                "has_else": bool(node.orelse),
                "is_elif": is_elif,
                "is_guard": _is_guard_clause(node),
                "body_statements": len(node.body),
            },
        )
        branch.extend(self.visit(node.test))
        branch.extend(self.visit_body(node.body))
        out = [branch]
        if node.orelse:
            only = node.orelse[0]
            if len(node.orelse) == 1 and isinstance(only, ast.If):
                only._emc_is_elif = True  # type: ignore[attr-defined]
                out.extend(self.visit(only))
            else:
                else_node = Node(
                    kind=Kind.ELSE,
                    span=Span(
                        _span(node.orelse[0]).start_line - 1,
                        0,
                        _span(node.orelse[0]).start_line - 1,
                        10_000,
                    ),
                    name="else",
                    meta={"body_statements": len(node.orelse), "of": _repr(node.test, 40)},
                )
                else_node.extend(self.visit_body(node.orelse))
                out.append(else_node)
        return out

    def visit_IfExp(self, node: ast.IfExp) -> list[Node]:
        ternary = Node(
            kind=Kind.TERNARY,
            span=_span(node),
            name="conditional",
            meta={
                "condition": _repr(node.test, 40),
                "when_true": _repr(node.body, 32),
                "when_false": _repr(node.orelse, 32),
            },
        )
        ternary.extend(self.children_of(node))
        return [ternary]

    def _for(self, node: ast.For | ast.AsyncFor, is_async: bool) -> list[Node]:
        iterable = _repr(node.iter)
        call_name = _callee_name(node.iter.func) if isinstance(node.iter, ast.Call) else ""
        loop = Node(
            kind=Kind.LOOP_FOREACH,
            span=_header_span(node),
            name="for",
            meta={
                "target": _repr(node.target, 32),
                "iterable": iterable,
                "iterable_call": call_name,
                "counted": call_name == "range",
                "is_async": is_async,
                "has_else": bool(node.orelse),
                "unpacks": isinstance(node.target, (ast.Tuple, ast.List)),
                "enumerated": call_name == "enumerate",
                "zipped": call_name == "zip",
                "body_statements": len(node.body),
            },
        )
        loop.extend(self.visit(node.iter))
        loop.extend(self.visit_body(node.body))
        if node.orelse:
            loop.extend(self.visit_body(node.orelse))
        return [loop]

    def visit_For(self, node: ast.For) -> list[Node]:
        return self._for(node, is_async=False)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> list[Node]:
        return self._for(node, is_async=True)

    def visit_While(self, node: ast.While) -> list[Node]:
        is_infinite = isinstance(node.test, ast.Constant) and bool(node.test.value)
        loop = Node(
            kind=Kind.LOOP_WHILE,
            span=_header_span(node),
            name="while",
            meta={
                "condition": _repr(node.test),
                "is_infinite": is_infinite,
                "has_else": bool(node.orelse),
                "has_break": any(isinstance(n, ast.Break) for n in ast.walk(node)),
                "body_statements": len(node.body),
            },
        )
        loop.extend(self.visit(node.test))
        loop.extend(self.visit_body(node.body))
        return [loop]

    def visit_Break(self, node: ast.Break) -> list[Node]:
        return [Node(kind=Kind.BREAK, span=_span(node), name="break")]

    def visit_Continue(self, node: ast.Continue) -> list[Node]:
        return [Node(kind=Kind.CONTINUE, span=_span(node), name="continue")]

    def visit_Return(self, node: ast.Return) -> list[Node]:
        ret = Node(
            kind=Kind.RETURN,
            span=_span(node),
            name="return",
            meta={
                "value": _repr(node.value),
                "is_bare": node.value is None,
                "returns_tuple": isinstance(node.value, ast.Tuple),
            },
        )
        ret.extend(self.children_of(node))
        return [ret]

    def _yield(self, node: ast.Yield | ast.YieldFrom, delegated: bool) -> list[Node]:
        return [
            Node(
                kind=Kind.YIELD,
                span=_span(node),
                name="yield",
                meta={"value": _repr(node.value), "delegated": delegated},
            )
        ]

    def visit_Yield(self, node: ast.Yield) -> list[Node]:
        return self._yield(node, delegated=False)

    def visit_YieldFrom(self, node: ast.YieldFrom) -> list[Node]:
        return self._yield(node, delegated=True)

    def visit_Raise(self, node: ast.Raise) -> list[Node]:
        exc = _callee_name(node.exc.func) if isinstance(node.exc, ast.Call) else _repr(node.exc, 32)
        return [
            Node(
                kind=Kind.THROW,
                span=_span(node),
                name="raise",
                meta={"exception": exc, "reraises": node.exc is None,
                      "message": _repr(node.exc.args[0], 48)
                      if isinstance(node.exc, ast.Call) and node.exc.args else ""},
            )
        ]

    def visit_Try(self, node: ast.Try) -> list[Node]:
        try_node = Node(
            kind=Kind.TRY,
            span=Span(_span(node).start_line, _span(node).start_col, _span(node).start_line, 10_000),
            name="try",
            meta={
                "handler_count": len(node.handlers),
                "has_finally": bool(node.finalbody),
                "has_else": bool(node.orelse),
                "caught": [
                    _repr(h.type, 32) or "everything" for h in node.handlers
                ],
            },
        )
        try_node.extend(self.visit_body(node.body))
        for handler in node.handlers:
            exc_type = _repr(handler.type, 40)
            catch = Node(
                kind=Kind.CATCH,
                span=_header_span(handler),
                name=handler.name or exc_type or "except",
                meta={
                    "exception": exc_type,
                    "is_bare": handler.type is None,
                    "binds": handler.name or "",
                    "swallows": len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass),
                },
            )
            catch.extend(self.visit_body(handler.body))
            try_node.add(catch)
        if node.orelse:
            try_node.extend(self.visit_body(node.orelse))
        if node.finalbody:
            finally_node = Node(
                kind=Kind.FINALLY,
                span=Span(
                    _span(node.finalbody[0]).start_line - 1, 0,
                    _span(node.finalbody[0]).start_line - 1, 10_000,
                ),
                name="finally",
                meta={"body_statements": len(node.finalbody)},
            )
            finally_node.extend(self.visit_body(node.finalbody))
            try_node.add(finally_node)
        return [try_node]

    def _with(self, node: ast.With | ast.AsyncWith, is_async: bool) -> list[Node]:
        managers = [_repr(item.context_expr, 40) for item in node.items]
        with_node = Node(
            kind=Kind.WITH,
            span=_header_span(node),
            name="with",
            meta={
                "managers": managers,
                "is_async": is_async,
                "binds": [_repr(item.optional_vars, 24) for item in node.items if item.optional_vars],
                "is_file": any("open" in m for m in managers),
            },
        )
        for item in node.items:
            with_node.extend(self.visit(item.context_expr))
        with_node.extend(self.visit_body(node.body))
        return [with_node]

    def visit_With(self, node: ast.With) -> list[Node]:
        return self._with(node, is_async=False)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> list[Node]:
        return self._with(node, is_async=True)

    def visit_Match(self, node: ast.Match) -> list[Node]:
        match_node = Node(
            kind=Kind.MATCH,
            span=_header_span(node, "cases"),
            name="match",
            meta={"subject": _repr(node.subject, 40), "case_count": len(node.cases)},
        )
        for case in node.cases:
            case_node = Node(
                kind=Kind.CASE,
                span=_header_span(case),
                name="case",
                meta={
                    "pattern": _repr(case.pattern, 40) if hasattr(case, "pattern") else "",
                    "has_guard": case.guard is not None,
                },
            )
            case_node.extend(self.visit_body(case.body))
            match_node.add(case_node)
        return [match_node]

    # -- data -------------------------------------------------------------------

    def visit_Assign(self, node: ast.Assign) -> list[Node]:
        targets = [_repr(t, 32) for t in node.targets]
        assign = Node(
            kind=Kind.ASSIGN,
            span=_span(node),
            name=targets[0] if targets else None,
            meta={
                "targets": targets,
                "value": _repr(node.value),
                "value_kind": type(node.value).__name__,
                "is_multiple": len(targets) > 1,
                "unpacks": isinstance(node.targets[0], (ast.Tuple, ast.List)),
                "from_call": _callee_name(node.value.func)
                if isinstance(node.value, ast.Call)
                else "",
                "is_constant": isinstance(node.value, ast.Constant),
                "literal_type": type(node.value.value).__name__
                if isinstance(node.value, ast.Constant)
                else "",
            },
        )
        assign.extend(self.visit(node.value))
        return [assign]

    def visit_AnnAssign(self, node: ast.AnnAssign) -> list[Node]:
        decl = Node(
            kind=Kind.DECL,
            span=_span(node),
            name=_repr(node.target, 32),
            meta={
                "annotation": _repr(node.annotation, 32),
                "value": _repr(node.value),
                "has_value": node.value is not None,
            },
        )
        if node.value is not None:
            decl.extend(self.visit(node.value))
        return [decl]

    def visit_AugAssign(self, node: ast.AugAssign) -> list[Node]:
        op = _OPS.get(type(node.op).__name__, type(node.op).__name__)
        aug = Node(
            kind=Kind.AUG_ASSIGN,
            span=_span(node),
            name=_repr(node.target, 32),
            meta={
                "target": _repr(node.target, 32),
                "op": op,
                "value": _repr(node.value, 40),
                "is_accumulator": op in {"+", "-"},
            },
        )
        aug.extend(self.visit(node.value))
        return [aug]

    def visit_Call(self, node: ast.Call) -> list[Node]:
        is_method = isinstance(node.func, ast.Attribute)
        name = _callee_name(node.func)
        call = Node(
            kind=Kind.METHOD_CALL if is_method else Kind.CALL,
            span=_span(node),
            name=name,
            meta={
                "callee": name,
                "receiver": _repr(node.func.value, 32) if is_method else "",
                "arity": len(node.args) + len(node.keywords),
                "args": [_repr(a, 24) for a in node.args],
                "kwargs": [k.arg for k in node.keywords if k.arg],
                "is_builtin": (not is_method) and name in NOTABLE_BUILTINS,
                "cost": KNOWN_COSTS.get(name, ""),
                "qualified": _repr(node.func, 48),
            },
        )
        for arg in [*node.args, *[k.value for k in node.keywords]]:
            call.extend(self.visit(arg))
        return [call]

    def visit_Await(self, node: ast.Await) -> list[Node]:
        await_node = Node(
            kind=Kind.AWAIT,
            span=_span(node),
            name="await",
            meta={"awaited": _repr(node.value, 40)},
        )
        await_node.extend(self.visit(node.value))
        return [await_node]

    def _comprehension(self, node: ast.AST, comp_type: str) -> list[Node]:
        generators = node.generators  # type: ignore[attr-defined]
        first = generators[0]
        comp = Node(
            kind=Kind.COMPREHENSION,
            span=_span(node),
            name=comp_type,
            meta={
                "comp_type": comp_type,
                "target": _repr(first.target, 24),
                "iterable": _repr(first.iter, 32),
                "has_condition": bool(first.ifs),
                "condition": _repr(first.ifs[0], 32) if first.ifs else "",
                "nested_loops": len(generators),
                "is_async": any(getattr(g, "is_async", 0) for g in generators),
                "output": _repr(getattr(node, "elt", None) or getattr(node, "key", None), 32),
            },
        )
        for gen in generators:
            comp.extend(self.visit(gen.iter))
            for condition in gen.ifs:
                comp.extend(self.visit(condition))
        # The output expression is where the real work happens — `[await f(x) for x in xs]`
        # has its call and its await here, not in the iterable.
        for attribute in ("elt", "key", "value"):
            output = getattr(node, attribute, None)
            if output is not None:
                comp.extend(self.visit(output))
        return [comp]

    def visit_ListComp(self, node: ast.ListComp) -> list[Node]:
        return self._comprehension(node, "list")

    def visit_SetComp(self, node: ast.SetComp) -> list[Node]:
        return self._comprehension(node, "set")

    def visit_DictComp(self, node: ast.DictComp) -> list[Node]:
        return self._comprehension(node, "dict")

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> list[Node]:
        return self._comprehension(node, "generator")

    def visit_Subscript(self, node: ast.Subscript) -> list[Node]:
        is_slice = isinstance(node.slice, ast.Slice)
        sub = Node(
            kind=Kind.SLICE if is_slice else Kind.INDEX,
            span=_span(node),
            name=_repr(node.value, 24),
            meta={
                "container": _repr(node.value, 32),
                "key": _repr(node.slice, 32),
                "is_slice": is_slice,
                "negative": isinstance(node.slice, ast.UnaryOp)
                and isinstance(node.slice.op, ast.USub),
            },
        )
        sub.extend(self.visit(node.value))
        return [sub]

    def visit_Attribute(self, node: ast.Attribute) -> list[Node]:
        attr = Node(
            kind=Kind.ATTRIBUTE,
            span=_span(node),
            name=node.attr,
            meta={"object": _repr(node.value, 32), "attribute": node.attr},
        )
        attr.extend(self.visit(node.value))
        return [attr]

    def visit_BinOp(self, node: ast.BinOp) -> list[Node]:
        op = _OPS.get(type(node.op).__name__, type(node.op).__name__)
        binop = Node(
            kind=Kind.BINOP,
            span=_span(node),
            name=op,
            meta={
                "op": op,
                "op_name": _OP_NAMES.get(op, "combines"),
                "left": _repr(node.left, 24),
                "right": _repr(node.right, 24),
            },
        )
        binop.extend(self.visit(node.left))
        binop.extend(self.visit(node.right))
        return [binop]

    def visit_BoolOp(self, node: ast.BoolOp) -> list[Node]:
        op = "and" if isinstance(node.op, ast.And) else "or"
        boolop = Node(
            kind=Kind.BOOLOP,
            span=_span(node),
            name=op,
            meta={"op": op, "operand_count": len(node.values),
                  "operands": [_repr(v, 24) for v in node.values]},
        )
        for value in node.values:
            boolop.extend(self.visit(value))
        return [boolop]

    def visit_Compare(self, node: ast.Compare) -> list[Node]:
        ops = [_OPS.get(type(o).__name__, type(o).__name__) for o in node.ops]
        compare = Node(
            kind=Kind.COMPARE,
            span=_span(node),
            name=ops[0] if ops else "compare",
            meta={
                "ops": ops,
                "op_name": _OP_NAMES.get(ops[0], "compares") if ops else "compares",
                "left": _repr(node.left, 24),
                "right": _repr(node.comparators[0], 24) if node.comparators else "",
                "is_chained": len(ops) > 1,
                "is_membership": any(o in {"in", "not in"} for o in ops),
                "is_identity": any(o in {"is", "is not"} for o in ops),
            },
        )
        compare.extend(self.visit(node.left))
        for comparator in node.comparators:
            compare.extend(self.visit(comparator))
        return [compare]

    def visit_UnaryOp(self, node: ast.UnaryOp) -> list[Node]:
        op = _OPS.get(type(node.op).__name__, type(node.op).__name__)
        unop = Node(
            kind=Kind.UNOP,
            span=_span(node),
            name=op,
            meta={"op": op, "operand": _repr(node.operand, 32)},
        )
        unop.extend(self.visit(node.operand))
        return [unop]

    def _collection(self, node: ast.AST, coll_type: str, size: int) -> list[Node]:
        return [
            Node(
                kind=Kind.COLLECTION,
                span=_span(node),
                name=coll_type,
                meta={"collection_type": coll_type, "size": size,
                      "is_empty": size == 0, "value": _repr(node, 40)},
            )
        ]

    def visit_List(self, node: ast.List) -> list[Node]:
        return self._collection(node, "list", len(node.elts))

    def visit_Tuple(self, node: ast.Tuple) -> list[Node]:
        return self._collection(node, "tuple", len(node.elts))

    def visit_Set(self, node: ast.Set) -> list[Node]:
        return self._collection(node, "set", len(node.elts))

    def visit_Dict(self, node: ast.Dict) -> list[Node]:
        return self._collection(node, "dict", len(node.keys))

    def visit_JoinedStr(self, node: ast.JoinedStr) -> list[Node]:
        slots = [f for f in node.values if isinstance(f, ast.FormattedValue)]
        return [
            Node(
                kind=Kind.FSTRING,
                span=_span(node),
                name="f-string",
                meta={"slot_count": len(slots),
                      "slots": [_repr(s.value, 24) for s in slots]},
            )
        ]

    def visit_Starred(self, node: ast.Starred) -> list[Node]:
        return [
            Node(kind=Kind.SPREAD, span=_span(node), name="*",
                 meta={"value": _repr(node.value, 32)})
        ]

    def visit_Delete(self, node: ast.Delete) -> list[Node]:
        return [
            Node(kind=Kind.DELETE, span=_span(node), name="del",
                 meta={"targets": [_repr(t, 24) for t in node.targets]})
        ]

    def visit_Global(self, node: ast.Global) -> list[Node]:
        return [
            Node(kind=Kind.DECL, span=_span(node), name="global",
                 meta={"scope": "global", "names": list(node.names)})
        ]

    def visit_Nonlocal(self, node: ast.Nonlocal) -> list[Node]:
        return [
            Node(kind=Kind.DECL, span=_span(node), name="nonlocal",
                 meta={"scope": "nonlocal", "names": list(node.names)})
        ]

    def visit_Assert(self, node: ast.Assert) -> list[Node]:
        return [
            Node(kind=Kind.THROW, span=_span(node), name="assert",
                 meta={"exception": "AssertionError", "is_assert": True,
                       "condition": _repr(node.test, 40),
                       "message": _repr(node.msg, 40)})
        ]

    # -- module system -----------------------------------------------------------

    def visit_Import(self, node: ast.Import) -> list[Node]:
        names = [a.name for a in node.names]
        return [
            Node(
                kind=Kind.IMPORT,
                span=_span(node),
                name=names[0] if names else None,
                meta={
                    "module": names[0] if names else "",
                    "names": names,
                    "aliases": [a.asname for a in node.names if a.asname],
                    "is_from": False,
                    "is_stdlib": _is_stdlib(names[0]) if names else False,
                },
            )
        ]

    def visit_ImportFrom(self, node: ast.ImportFrom) -> list[Node]:
        names = [a.name for a in node.names]
        module = node.module or ("." * (node.level or 0))
        return [
            Node(
                kind=Kind.IMPORT,
                span=_span(node),
                name=module,
                meta={
                    "module": module,
                    "names": names,
                    "aliases": [a.asname for a in node.names if a.asname],
                    "is_from": True,
                    "is_relative": bool(node.level),
                    "is_stdlib": _is_stdlib(module),
                },
            )
        ]

    def visit_Name(self, node: ast.Name) -> list[Node]:
        return [
            Node(
                kind=Kind.NAME,
                span=_span(node),
                name=node.id,
                meta={"ctx": type(node.ctx).__name__.lower()},
            )
        ]

    def visit_Constant(self, node: ast.Constant) -> list[Node]:
        return [
            Node(
                kind=Kind.LITERAL,
                span=_span(node),
                name=_repr(node, 24),
                meta={
                    "literal_type": type(node.value).__name__,
                    "value": _repr(node, 32),
                    "is_magic_number": isinstance(node.value, (int, float))
                    and not isinstance(node.value, bool)
                    and node.value not in (0, 1, -1, 2, 100),
                },
            )
        ]

    def visit_Pass(self, node: ast.Pass) -> list[Node]:
        return [Node(kind=Kind.BLOCK, span=_span(node), name="pass",
                     meta={"is_placeholder": True})]

    def visit_Expr(self, node: ast.Expr) -> list[Node]:
        # A docstring is already captured in its owner's meta; emitting it again as a
        # bare string literal just adds a line that explains nothing.
        if getattr(node, "_emc_is_docstring", False):
            return []
        return self.visit(node.value)


def _is_docstring_stmt(stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    )


def _is_guard_clause(node: ast.If) -> bool:
    """`if not x: return` — worth naming, since it reads differently from a real branch."""
    return (
        not node.orelse
        and len(node.body) == 1
        and isinstance(node.body[0], (ast.Return, ast.Continue, ast.Break, ast.Raise))
    )


_STDLIB_HINT = {
    "os", "sys", "re", "json", "math", "time", "datetime", "collections", "itertools",
    "functools", "typing", "pathlib", "random", "subprocess", "threading", "asyncio",
    "dataclasses", "enum", "abc", "io", "csv", "sqlite3", "logging", "unittest",
    "argparse", "hashlib", "base64", "urllib", "http", "socket", "struct", "copy",
    "heapq", "bisect", "string", "textwrap", "traceback", "warnings", "contextlib",
}


def _is_stdlib(module: str) -> bool:
    return module.split(".")[0] in _STDLIB_HINT


_OPS = {
    "Add": "+", "Sub": "-", "Mult": "*", "Div": "/", "FloorDiv": "//", "Mod": "%",
    "Pow": "**", "LShift": "<<", "RShift": ">>", "BitOr": "|", "BitXor": "^",
    "BitAnd": "&", "MatMult": "@", "Eq": "==", "NotEq": "!=", "Lt": "<", "LtE": "<=",
    "Gt": ">", "GtE": ">=", "Is": "is", "IsNot": "is not", "In": "in", "NotIn": "not in",
    "Not": "not", "USub": "-", "UAdd": "+", "Invert": "~",
}

_OP_NAMES = {
    "+": "adds", "-": "subtracts", "*": "multiplies", "/": "divides",
    "//": "divides and drops the remainder", "%": "takes the remainder",
    "**": "raises to a power", "==": "checks equality", "!=": "checks inequality",
    "<": "checks less-than", "<=": "checks less-than-or-equal",
    ">": "checks greater-than", ">=": "checks greater-than-or-equal",
    "is": "checks identity", "is not": "checks non-identity",
    "in": "checks membership", "not in": "checks absence",
    "<<": "shifts bits left", ">>": "shifts bits right",
    "&": "combines bits with AND", "|": "combines bits with OR", "^": "combines bits with XOR",
}


def _collect_comments(source: str) -> list[Node]:
    out: list[Node] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                text = tok.string.lstrip("#").strip()
                out.append(
                    Node(
                        kind=Kind.COMMENT,
                        span=Span(tok.start[0], tok.start[1], tok.end[0], tok.end[1]),
                        name=text[:80],
                        meta={"text": text, "is_todo": text.upper().startswith(("TODO", "FIXME", "HACK", "XXX"))},
                    )
                )
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass  # A partial comment list is fine; the AST is what matters.
    return out


class PythonAdapter:
    language = Language.PYTHON
    parser_name = "cpython-ast"

    def available(self) -> bool:
        return True

    def parse(self, source: str) -> ParseResult:
        diagnostics: list[Diagnostic] = []
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            line = exc.lineno or 1
            col = (exc.offset or 1) - 1
            diagnostics.append(
                Diagnostic(
                    message=f"Syntax error: {exc.msg}",
                    span=Span(line, max(col, 0), line, max(col + 1, 1)),
                    severity="error",
                )
            )
            partial = _parse_longest_prefix(source)
            if partial is None:
                lines = source.splitlines()
                root = Node(
                    kind=Kind.MODULE,
                    span=Span(1, 0, max(len(lines), 1), 0),
                    name="module",
                    meta={"unparsed": True},
                )
                return ParseResult(root, Language.PYTHON, source, diagnostics,
                                   self.parser_name, degraded=True)
            tree = partial
            diagnostics.append(
                Diagnostic(message="Explained the portion above the error.", severity="info")
            )

        lowerer = PythonLowerer(source)
        root = lowerer.lower(tree)
        for comment in _collect_comments(source):
            root.add(comment)
        return ParseResult(
            root,
            Language.PYTHON,
            source,
            diagnostics,
            self.parser_name,
            degraded=bool(diagnostics and diagnostics[0].severity == "error"),
        )


def _parse_longest_prefix(source: str) -> ast.Module | None:
    """Salvage a partial tree from broken input.

    Someone pasting a snippet mid-edit should still get an explanation of the lines
    that do parse, rather than a blank page.
    """
    lines = source.splitlines()
    for end in range(len(lines) - 1, 0, -1):
        try:
            return ast.parse("\n".join(lines[:end]))
        except SyntaxError:
            continue
    return None


@register(Language.PYTHON)
def _factory() -> PythonAdapter:
    return PythonAdapter()
