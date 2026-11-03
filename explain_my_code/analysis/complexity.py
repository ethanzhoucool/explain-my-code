"""Asymptotic-cost heuristic.

This is a heuristic and is labelled as one everywhere it surfaces. It reads loop
nesting, recursion shape, and the cost of known library calls: enough to be right on
the code people paste into an explainer (sorts, nested scans, naive fib) and honest
about the cases it cannot see through.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass

from explain_my_code.ir import CALLABLE_KINDS, LOOP_KINDS, Kind, Node

#: Argument shrink patterns that turn linear recursion logarithmic.
HALVING = re.compile(r"(//\s*2|/\s*2|>>\s*1|mid|\bhalf\b|len\(\w+\)\s*//\s*2)", re.IGNORECASE)

#: Memoisation markers. The difference between O(2^n) and O(n) for naive fib.
MEMO_DECORATORS = ("lru_cache", "cache", "memoize", "functools.cache")

#: Child links of a tree node. Recursing on these walks a tree, visiting each node once,
#: rather than growing a call tree that doubles at every level.
TREE_CHILD = re.compile(
    r"(\.|->)\s*(left|right|lhs|rhs|children|child|kids|subtrees?)\b", re.IGNORECASE
)

#: (power of n, power of log n) for each known library cost.
COST_TERMS: dict[str, tuple[int, int]] = {
    "1": (0, 0), "log n": (0, 1), "n": (1, 0), "n log n": (1, 1),
}

SUPERSCRIPT = {2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶"}


@dataclass(slots=True)
class ComplexityEstimate:
    label: str
    reason: str
    confidence: float

    def to_dict(self) -> dict[str, object]:
        return {"label": self.label, "reason": self.reason, "confidence": round(self.confidence, 2)}


def _loop_label(depth: int) -> str:
    if depth <= 0:
        return "1"
    if depth == 1:
        return "n"
    return f"n{SUPERSCRIPT.get(depth, f'^{depth}')}"


def _max_loop_depth(function: Node) -> tuple[int, Node | None]:
    """Deepest loop nest inside this function, ignoring nested function bodies."""
    deepest = 0
    culprit: Node | None = None

    def visit(node: Node, depth: int) -> None:
        nonlocal deepest, culprit
        for child in node.children:
            if child.kind in CALLABLE_KINDS:
                continue
            if child.kind in LOOP_KINDS:
                if depth + 1 > deepest:
                    deepest = depth + 1
                    culprit = child
                visit(child, depth + 1)
            else:
                visit(child, depth)

    visit(function, 0)
    return deepest, culprit


def _own_nodes(function: Node) -> Iterator[Node]:
    """This function's body, pre-order, without descending into nested callables."""
    stack = list(reversed(function.children))
    while stack:
        node = stack.pop()
        if node.kind in CALLABLE_KINDS:
            continue
        yield node
        stack.extend(reversed(node.children))


@dataclass(slots=True)
class _CostlyCall:
    callee: str
    cost: str
    #: Loops of this function the call actually runs inside.
    loops: list[Node]

    @property
    def term(self) -> tuple[int, int]:
        poly, log = COST_TERMS[self.cost]
        return poly + len(self.loops), log


def _costly_calls(function: Node) -> list[_CostlyCall]:
    """Known-cost library calls in this function's own body, with the loops around each.

    A for-each loop evaluates its iterable once, so `for x in sorted(xs)` sorts once:
    a call inside the loop's header span is not counted as running inside the loop.
    """
    out: list[_CostlyCall] = []
    stack: list[tuple[Node, list[Node]]] = [(c, []) for c in reversed(function.children)]
    while stack:
        node, loops = stack.pop()
        if node.kind in CALLABLE_KINDS:
            continue
        if node.kind in {Kind.CALL, Kind.METHOD_CALL}:
            cost = str(node.meta.get("cost") or "")
            if cost in COST_TERMS and cost != "1":
                callee = str(node.meta.get("callee") or node.name or "a call")
                out.append(_CostlyCall(callee, cost, loops))
        for child in reversed(node.children):
            inside = node.kind in LOOP_KINDS and not (
                node.kind is Kind.LOOP_FOREACH and node.span.contains(child.span)
            )
            stack.append((child, [*loops, node] if inside else loops))
    return out


def _label(term: tuple[int, int]) -> str:
    poly, log = term
    if poly == 0:
        return "log n" if log else "1"
    return f"{_loop_label(poly)} log n" if log else _loop_label(poly)


def _loop_phrase(depth: int, loop: Node | None) -> str:
    iterable = "the input"
    if loop is not None:
        iterable = str(loop.meta.get("iterable") or loop.meta.get("condition") or "the input")
    return f"{depth} nested loop(s) over {iterable}" if depth > 1 else f"one loop over {iterable}"


def _is_memoized(function: Node) -> bool:
    decorators = [str(d).lower() for d in function.meta.get("decorators", [])]
    if any(marker in decorator for decorator in decorators for marker in MEMO_DECORATORS):
        return True
    # A cache-lookup guard in the first few statements counts too.
    for child in function.children[:4]:
        if child.kind is Kind.BRANCH:
            condition = str(child.meta.get("condition", "")).lower()
            if "cache" in condition or "memo" in condition or "seen" in condition:
                return True
    return False


def _self_calls(function: Node, name: str) -> list[Node]:
    return [
        node
        for node in _own_nodes(function)
        if node.kind in {Kind.CALL, Kind.METHOD_CALL} and node.meta.get("callee") == name
    ]


def _calls_per_invocation(function: Node, calls: list[Node]) -> int:
    """Self-calls one invocation can make, not how many are written down.

    A call returns through at most one `return`, so calls sitting in different return
    statements are alternatives: recursive binary search has two, and makes one.
    """
    per_return: dict[int, int] = {}
    elsewhere = 0
    for call in calls:
        owner = next(
            (a for a in call.ancestors() if a is function or a.kind is Kind.RETURN), None
        )
        if owner is None or owner is function:
            elsewhere += 1
        else:
            per_return[owner.id] = per_return.get(owner.id, 0) + 1
    return elsewhere + max(per_return.values(), default=0)


def _shrinks_by_a_constant(function: Node, args: str) -> bool:
    """`n - 1`, `i + 1`, `s[1:]`: a parameter stepping by a constant, so the recursion
    is about n deep. With two or more calls per level that is what makes it exponential."""
    params = [re.escape(str(p)) for p in function.meta.get("param_names") or [] if p]
    name = f"(?:{'|'.join(params)})" if params else r"\w+"
    step = rf"\b{name}\s*[-+]\s*\d+\b|\b{name}\s*\[\s*\d+\s*:|\b{name}\s*\[\s*:\s*-\s*\d+\s*\]"
    return bool(re.search(step, args))


def _recursive_estimate(function: Node, name: str) -> tuple[ComplexityEstimate, bool] | None:
    """The recursion's own cost, and whether that already covers the body's loops."""
    calls = _self_calls(function, name)
    if not calls:
        return None
    if _is_memoized(function):
        return (
            ComplexityEstimate(
                "O(n)",
                f"`{name}` recurses but memoises, so each distinct input is computed once.",
                0.6,
            ),
            False,
        )
    branching = _calls_per_invocation(function, calls)
    args = " ".join(" ".join(str(a) for a in call.meta.get("args") or []) for call in calls)
    walks_a_tree = bool(TREE_CHILD.search(args))
    halves = bool(HALVING.search(args))

    if branching >= 2:
        if walks_a_tree:
            return (
                ComplexityEstimate(
                    "O(n)",
                    f"`{name}` recurses into each child of a tree node, so it visits every "
                    "node once.",
                    0.6,
                ),
                True,
            )
        if halves:
            return (
                ComplexityEstimate(
                    "O(n log n)",
                    f"`{name}` splits its input in half and recurses on both halves (divide "
                    "and conquer, like merge sort): log n levels of O(n) work.",
                    0.55,
                ),
                True,
            )
        if _shrinks_by_a_constant(function, args):
            return (
                ComplexityEstimate(
                    f"O({branching}^n)" if branching > 2 else "O(2^n)",
                    f"`{name}` calls itself {branching} times per invocation with no "
                    "memoisation, so the call tree doubles at every level.",
                    0.75,
                ),
                True,
            )
        return (
            ComplexityEstimate(
                "O(n log n)",
                f"`{name}` calls itself {branching} times on separate parts of its input "
                "(divide and conquer, like quicksort): about O(n log n) when the parts are "
                "balanced, O(n²) when they are not.",
                0.4,
            ),
            True,
        )

    if walks_a_tree:
        return (
            ComplexityEstimate(
                "O(log n)",
                f"`{name}` follows one child per call, so it costs the height of the tree: "
                "O(log n) when the tree is balanced, O(n) when it is not.",
                0.5,
            ),
            False,
        )
    if halves:
        return (
            ComplexityEstimate(
                "O(log n)",
                f"`{name}` recurses once per call and halves its input each time.",
                0.7,
            ),
            False,
        )
    return (
        ComplexityEstimate(
            "O(n)", f"`{name}` recurses once per call, shrinking its input by a constant.", 0.65
        ),
        False,
    )


def estimate(function: Node, *, is_recursive: bool = False) -> ComplexityEstimate:
    """Best-effort asymptotic class for one function."""
    name = function.name or ""

    if is_recursive:
        result = _recursive_estimate(function, name)
        if result is None:
            # Recursive per the call graph but with no direct self-call: the cycle runs
            # through another function, so the depth is not visible from this body alone.
            return ComplexityEstimate(
                "O(n)",
                f"`{name}` takes part in a recursive cycle through another function, "
                "so its cost depends on how fast that cycle shrinks its input.",
                0.4,
            )
        recursive, covers_loops = result
        depth, _ = _max_loop_depth(function)
        if covers_loops or depth == 0:
            return recursive
        return ComplexityEstimate(
            f"O({_loop_label(depth)} · recursion)",
            f"{recursive.reason} It also loops {depth} level(s) deep per call.",
            0.5,
        )

    depth, culprit = _max_loop_depth(function)
    costly = max(_costly_calls(function), key=lambda call: call.term, default=None)

    if depth == 0:
        if costly is not None:
            return ComplexityEstimate(
                f"O({costly.cost})",
                f"No loops here, but `{costly.callee}` costs O({costly.cost}) on its own.",
                0.6,
            )
        return ComplexityEstimate(
            "O(1)", "No loops and no recursion. The work does not grow with the input.", 0.8
        )

    loops_only = (depth, 0)
    if costly is None or costly.term <= loops_only:
        return ComplexityEstimate(
            f"O({_label(loops_only)})",
            f"{_loop_phrase(depth, culprit)}.",
            0.7 if depth <= 2 else 0.6,
        )

    label = f"O({_label(costly.term)})"
    if not costly.loops:
        return ComplexityEstimate(
            label,
            f"{_loop_phrase(depth, culprit)}, but `{costly.callee}` costs O({costly.cost}) "
            "on its own, which dominates.",
            0.55,
        )
    where = _loop_phrase(len(costly.loops), costly.loops[-1])
    if costly.cost == "n log n":
        detail = f"`{costly.callee}` sorts inside it at O(n log n)"
    elif costly.cost == "n":
        detail = f"`{costly.callee}` scans the whole collection inside it"
    else:
        detail = f"`{costly.callee}` costs O({costly.cost}) inside it"
    return ComplexityEstimate(label, f"{where}, and {detail}.", 0.55)
