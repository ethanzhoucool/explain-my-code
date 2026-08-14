"""Call graph and recursion detection.

Direct self-calls are easy; mutual recursion (`isEven` -> `isOdd` -> `isEven`) is not,
and it is exactly the case where a naive "does it call itself?" check tells a reader
the wrong thing. Tarjan's SCC algorithm catches both in one pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from explain_my_code.ir import CALLABLE_KINDS, Kind, Node


@dataclass(slots=True)
class CallGraph:
    #: qualified name -> callees referenced in its body
    edges: dict[str, list[str]] = field(default_factory=dict)
    #: qualified name -> the defining node's id
    definitions: dict[str, int] = field(default_factory=dict)
    #: cycles with more than one member, i.e. mutual recursion
    cycles: list[list[str]] = field(default_factory=list)
    #: functions that call themselves directly
    self_recursive: set[str] = field(default_factory=set)
    #: names called but never defined in this snippet
    external: set[str] = field(default_factory=set)

    def is_recursive(self, name: str) -> bool:
        return name in self.self_recursive or any(name in cycle for cycle in self.cycles)

    def to_dict(self) -> dict[str, Any]:
        return {
            "edges": self.edges,
            "cycles": self.cycles,
            "selfRecursive": sorted(self.self_recursive),
            "external": sorted(self.external)[:40],
            "nodes": sorted(self.definitions),
        }


def _short_name(qualified: str) -> str:
    return qualified.rsplit(".", 1)[-1]


def build_call_graph(root: Node) -> CallGraph:
    graph = CallGraph()
    functions = [n for n in root.walk() if n.kind in CALLABLE_KINDS]

    by_short: dict[str, list[str]] = {}
    for function in functions:
        qualified = function.qualified_name or (function.name or "<anonymous>")
        graph.definitions[qualified] = function.id
        by_short.setdefault(_short_name(qualified), []).append(qualified)

    for function in functions:
        qualified = function.qualified_name or (function.name or "<anonymous>")
        callees: list[str] = []
        for call in _calls_within(function):
            callee = str(call.meta.get("callee") or call.name or "")
            if not callee:
                continue
            # Resolve to a definition when the snippet contains one, else record it as
            # external. Short-name matching is deliberate: `self.helper()` and
            # `helper()` should land on the same node in a single-file snippet.
            matches = by_short.get(callee)
            if matches:
                resolved = matches[0] if len(matches) == 1 else _closest(qualified, matches)
                if resolved not in callees:
                    callees.append(resolved)
                if resolved == qualified:
                    graph.self_recursive.add(qualified)
            else:
                graph.external.add(callee)
        graph.edges[qualified] = callees

    graph.cycles = [cycle for cycle in _tarjan(graph.edges) if len(cycle) > 1]
    return graph


def _closest(source: str, candidates: list[str]) -> str:
    """Prefer a sibling in the same class/module over an unrelated same-named function."""
    prefix = source.rsplit(".", 1)[0] if "." in source else ""
    for candidate in candidates:
        if prefix and candidate.startswith(prefix + "."):
            return candidate
    return candidates[0]


def _calls_within(function: Node) -> list[Node]:
    """Calls in this function's own body, not in functions nested inside it."""
    out: list[Node] = []
    stack = list(function.children)
    while stack:
        node = stack.pop()
        if node.kind in CALLABLE_KINDS:
            continue
        if node.kind in {Kind.CALL, Kind.METHOD_CALL, Kind.NEW}:
            out.append(node)
        stack.extend(node.children)
    return out


def _tarjan(edges: dict[str, list[str]]) -> list[list[str]]:
    """Strongly connected components, iteratively (deep graphs must not blow the stack)."""
    index_of: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    result: list[list[str]] = []
    counter = 0

    for start in edges:
        if start in index_of:
            continue
        work: list[tuple[str, int]] = [(start, 0)]
        while work:
            node, child_index = work[-1]
            if child_index == 0:
                index_of[node] = low[node] = counter
                counter += 1
                stack.append(node)
                on_stack.add(node)
            recursed = False
            neighbours = edges.get(node, [])
            while child_index < len(neighbours):
                neighbour = neighbours[child_index]
                child_index += 1
                if neighbour not in edges:
                    continue
                if neighbour not in index_of:
                    work[-1] = (node, child_index)
                    work.append((neighbour, 0))
                    recursed = True
                    break
                if neighbour in on_stack:
                    low[node] = min(low[node], index_of[neighbour])
            if recursed:
                continue
            work[-1] = (node, child_index)
            if child_index >= len(neighbours):
                work.pop()
                if work:
                    parent = work[-1][0]
                    low[parent] = min(low[parent], low[node])
                if low[node] == index_of[node]:
                    component: list[str] = []
                    while True:
                        member = stack.pop()
                        on_stack.discard(member)
                        component.append(member)
                        if member == node:
                            break
                    result.append(sorted(component))
    return result
