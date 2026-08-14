"""Asymptotic-cost heuristic.

This is a heuristic and is labelled as one everywhere it surfaces. It reads loop
nesting, recursion shape, and the cost of known library calls — enough to be right on
the code people paste into an explainer (sorts, nested scans, naive fib) and honest
about the cases it cannot see through.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from explain_my_code.ir import CALLABLE_KINDS, LOOP_KINDS, Kind, Node

#: Argument shrink patterns that turn linear recursion logarithmic.
HALVING = re.compile(r"(//\s*2|/\s*2|>>\s*1|mid|\bhalf\b|len\(\w+\)\s*//\s*2)", re.IGNORECASE)

#: Memoisation markers — the difference between O(2^n) and O(n) for naive fib.
MEMO_DECORATORS = ("lru_cache", "cache", "memoize", "functools.cache")

COST_ORDER = ["1", "log n", "n", "n log n", "n²", "n³", "2^n"]

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


def _costly_call_in_loop(function: Node) -> tuple[str, str] | None:
    """A known super-linear library call executed inside a loop."""
    best: tuple[str, str] | None = None
    for node in function.walk():
        if node.kind not in {Kind.CALL, Kind.METHOD_CALL}:
            continue
        cost = str(node.meta.get("cost") or "")
        if not cost or cost == "1":
            continue
        if node.loop_depth == 0 and cost not in {"n log n", "n"}:
            continue
        callee = str(node.meta.get("callee") or node.name or "a call")
        if best is None or COST_ORDER.index(cost) > COST_ORDER.index(best[0]):
            best = (cost, callee)
    return best


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


def _self_call_count(function: Node, name: str) -> int:
    count = 0
    for node in function.walk():
        if node.kind in {Kind.CALL, Kind.METHOD_CALL} and node.meta.get("callee") == name:
            count += 1
    return count


def _recursive_estimate(function: Node, name: str) -> ComplexityEstimate | None:
    calls = _self_call_count(function, name)
    if calls == 0:
        return None
    if _is_memoized(function):
        return ComplexityEstimate(
            "O(n)",
            f"`{name}` recurses but memoises, so each distinct input is computed once.",
            0.6,
        )
    if calls >= 2:
        return ComplexityEstimate(
            f"O({calls}^n)" if calls > 2 else "O(2^n)",
            f"`{name}` calls itself {calls} times per invocation with no memoisation, "
            "so the call tree doubles at every level.",
            0.75,
        )
    body = " ".join(
        str(node.meta.get("args", "")) + str(node.meta.get("value", ""))
        for node in function.walk()
        if node.kind in {Kind.CALL, Kind.METHOD_CALL}
    )
    if HALVING.search(body):
        return ComplexityEstimate(
            "O(log n)",
            f"`{name}` recurses once per call and halves its input each time.",
            0.7,
        )
    return ComplexityEstimate(
        "O(n)", f"`{name}` recurses once per call, shrinking its input by a constant.", 0.65
    )


def estimate(function: Node, *, is_recursive: bool = False) -> ComplexityEstimate:
    """Best-effort asymptotic class for one function."""
    name = function.name or ""

    if is_recursive:
        recursive = _recursive_estimate(function, name)
        if recursive is None:
            # Recursive per the call graph but with no direct self-call: the cycle runs
            # through another function, so the depth is not visible from this body alone.
            return ComplexityEstimate(
                "O(n)",
                f"`{name}` takes part in a recursive cycle through another function, "
                "so its cost depends on how fast that cycle shrinks its input.",
                0.4,
            )
        depth, _ = _max_loop_depth(function)
        if depth > 0 and recursive.label.startswith("O(2^n"):
            return recursive
        if depth > 0:
            return ComplexityEstimate(
                f"O({_loop_label(depth)} · recursion)",
                f"{recursive.reason} It also loops {depth} level(s) deep per call.",
                0.5,
            )
        return recursive

    depth, culprit = _max_loop_depth(function)
    costly = _costly_call_in_loop(function)

    if depth == 0:
        if costly is not None:
            return ComplexityEstimate(
                f"O({costly[0]})",
                f"No loops here, but `{costly[1]}` costs O({costly[0]}) on its own.",
                0.6,
            )
        return ComplexityEstimate(
            "O(1)", "No loops and no recursion — the work does not grow with the input.", 0.8
        )

    label = _loop_label(depth)
    iterable = str(culprit.meta.get("iterable") or culprit.meta.get("condition") or "the input") if culprit else "the input"
    reason = (
        f"{depth} nested loop(s) over {iterable}"
        if depth > 1
        else f"one loop over {iterable}"
    )

    if costly is not None and costly[0] == "n log n":
        combined = f"O({label} log n)" if depth >= 1 else "O(n log n)"
        return ComplexityEstimate(
            combined,
            f"{reason}, and `{costly[1]}` sorts inside it at O(n log n).",
            0.55,
        )
    if costly is not None and costly[0] == "n":
        return ComplexityEstimate(
            f"O({_loop_label(depth + 1)})",
            f"{reason}, and `{costly[1]}` scans the whole collection inside it.",
            0.55,
        )

    return ComplexityEstimate(f"O({label})", f"{reason}.", 0.7 if depth <= 2 else 0.6)
