"""Scope and symbol resolution over the IR.

Deliberately conservative: it reports "defined and never read again in this snippet",
never "dead code". People paste fragments into an explainer, so anything that assumes
it can see the whole program would be wrong most of the time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from explain_my_code.ir import SCOPE_KINDS, Kind, Node, Span

#: Kinds whose `name`/`meta` introduce a binding.
BINDING_KINDS = frozenset(
    {
        Kind.PARAM, Kind.ASSIGN, Kind.DECL, Kind.FUNCTION, Kind.METHOD, Kind.CONSTRUCTOR,
        Kind.CLASS, Kind.INTERFACE, Kind.IMPORT, Kind.CTE,
    }
)


@dataclass(slots=True)
class Symbol:
    name: str
    kind: str
    scope: str
    defined_at: list[Span] = field(default_factory=list)
    used_at: list[Span] = field(default_factory=list)
    shadows: str | None = None

    @property
    def is_unused(self) -> bool:
        return not self.used_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "scope": self.scope,
            "definedAt": [s.to_dict() for s in self.defined_at[:5]],
            "useCount": len(self.used_at),
            "isUnused": self.is_unused,
            "shadows": self.shadows,
        }


@dataclass(slots=True)
class Scope:
    name: str
    kind: str
    node_id: int
    parent: Scope | None = None
    symbols: dict[str, Symbol] = field(default_factory=dict)
    children: list[Scope] = field(default_factory=list)

    def lookup(self, name: str) -> Symbol | None:
        scope: Scope | None = self
        while scope is not None:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None

    def lookup_outer(self, name: str) -> Symbol | None:
        scope = self.parent
        while scope is not None:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()


@dataclass(slots=True)
class SymbolTable:
    root: Scope

    @property
    def all_symbols(self) -> list[Symbol]:
        return [symbol for scope in self.root.walk() for symbol in scope.symbols.values()]

    @property
    def unused(self) -> list[Symbol]:
        return [
            s
            for s in self.all_symbols
            if s.is_unused
            and s.kind in {"variable", "parameter"}
            and not s.name.startswith("_")
            and s.name not in {"self", "this", "cls"}
        ]

    @property
    def shadowed(self) -> list[Symbol]:
        return [s for s in self.all_symbols if s.shadows]

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbolCount": len(self.all_symbols),
            "unused": [s.to_dict() for s in self.unused[:20]],
            "shadowed": [s.to_dict() for s in self.shadowed[:20]],
            "scopes": _scope_dict(self.root),
        }


def _scope_dict(scope: Scope) -> dict[str, Any]:
    return {
        "name": scope.name,
        "kind": scope.kind,
        "symbols": sorted(scope.symbols),
        "children": [_scope_dict(c) for c in scope.children],
    }


def _bindings_of(node: Node) -> list[tuple[str, str]]:
    """(name, symbol kind) pairs introduced by this node."""
    out: list[tuple[str, str]] = []
    if node.kind is Kind.PARAM and node.name:
        out.append((node.name, "parameter"))
    elif node.kind in {Kind.FUNCTION, Kind.METHOD, Kind.CONSTRUCTOR} and node.name:
        out.append((node.name, "function"))
    elif node.kind in {Kind.CLASS, Kind.INTERFACE} and node.name:
        out.append((node.name, "class"))
    elif node.kind is Kind.CTE and node.name:
        out.append((node.name, "cte"))
    elif node.kind is Kind.IMPORT:
        aliases = node.meta.get("aliases") or []
        names = node.meta.get("names") or []
        for name in aliases or names:
            if name:
                out.append((str(name).split(".")[0], "import"))
    elif node.kind in {Kind.ASSIGN, Kind.DECL}:
        targets = node.meta.get("targets") or ([node.meta["name"]] if node.meta.get("name") else [])
        for target in targets:
            base = str(target).split("[")[0].split(".")[0].strip("()* ")
            # `self.x = 1` binds an attribute, not a local; skip the receiver.
            if base and base.isidentifier() and "." not in str(target):
                out.append((base, "variable"))
    return out


def _loop_bindings(node: Node) -> list[tuple[str, str]]:
    if node.kind not in {Kind.LOOP_FOREACH, Kind.COMPREHENSION}:
        return []
    target = str(node.meta.get("target") or "")
    out: list[tuple[str, str]] = []
    for part in target.replace("(", "").replace(")", "").replace("[", "").replace("]", "").split(","):
        name = part.strip().lstrip("&*").split(":")[0].strip()
        if name and name.isidentifier():
            out.append((name, "variable"))
    return out


def build_symbol_table(root: Node) -> SymbolTable:
    root_scope = Scope(name="module", kind="module", node_id=root.id)

    def scope_for(node: Node, current: Scope) -> Scope:
        child = Scope(
            name=node.name or node.kind.value,
            kind=node.kind.value,
            node_id=node.id,
            parent=current,
        )
        current.children.append(child)
        return child

    def define(scope: Scope, name: str, kind: str, span: Span) -> None:
        existing = scope.symbols.get(name)
        if existing is not None:
            existing.defined_at.append(span)
            return
        outer = scope.lookup_outer(name)
        scope.symbols[name] = Symbol(
            name=name,
            kind=kind,
            scope=scope.name,
            defined_at=[span],
            shadows=outer.scope if outer is not None and outer.kind != "import" else None,
        )

    def visit(node: Node, scope: Scope) -> None:
        for name, kind in _bindings_of(node):
            define(scope, name, kind, node.span)
        for name, kind in _loop_bindings(node):
            define(scope, name, kind, node.span)

        inner = scope
        if node.kind in SCOPE_KINDS and node is not root:
            inner = scope_for(node, scope)

        for child in node.children:
            if child.kind is Kind.NAME and child.meta.get("ctx") != "store":
                symbol = inner.lookup(child.name or "")
                if symbol is not None:
                    symbol.used_at.append(child.span)
            visit(child, inner)

    visit(root, root_scope)
    return SymbolTable(root_scope)
