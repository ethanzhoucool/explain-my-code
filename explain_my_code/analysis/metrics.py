"""Complexity and volume metrics computed over the IR.

Because these run on the IR rather than on per-language source, a Java method and a
Python function are scored by exactly the same rules: which is the only way the
numbers are comparable in a tool that accepts five languages.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from explain_my_code.ir import (
    CALLABLE_KINDS,
    DECISION_KINDS,
    LOOP_KINDS,
    NESTING_KINDS,
    Kind,
    Node,
)

#: Kinds counted as Halstead operators.
OPERATOR_KINDS = frozenset(
    {
        Kind.BINOP, Kind.UNOP, Kind.COMPARE, Kind.BOOLOP, Kind.ASSIGN, Kind.AUG_ASSIGN,
        Kind.CALL, Kind.METHOD_CALL, Kind.INDEX, Kind.SLICE, Kind.ATTRIBUTE, Kind.NEW,
        Kind.DELETE, Kind.CAST, Kind.AWAIT, Kind.YIELD, Kind.RETURN, Kind.THROW,
        Kind.BRANCH, Kind.LOOP_FOR, Kind.LOOP_FOREACH, Kind.LOOP_WHILE, Kind.LOOP_DO,
        Kind.TERNARY, Kind.SWITCH, Kind.TRY, Kind.CATCH, Kind.AGGREGATE, Kind.JOIN,
    }
)

OPERAND_KINDS = frozenset({Kind.NAME, Kind.LITERAL, Kind.PARAM, Kind.COLLECTION})


@dataclass(slots=True)
class Halstead:
    distinct_operators: int = 0
    distinct_operands: int = 0
    total_operators: int = 0
    total_operands: int = 0

    @property
    def vocabulary(self) -> int:
        return self.distinct_operators + self.distinct_operands

    @property
    def length(self) -> int:
        return self.total_operators + self.total_operands

    @property
    def volume(self) -> float:
        if self.vocabulary <= 1:
            return 0.0
        return self.length * math.log2(self.vocabulary)

    @property
    def difficulty(self) -> float:
        if self.distinct_operands == 0:
            return 0.0
        return (self.distinct_operators / 2) * (self.total_operands / self.distinct_operands)

    @property
    def effort(self) -> float:
        return self.difficulty * self.volume

    def to_dict(self) -> dict[str, Any]:
        return {
            "vocabulary": self.vocabulary,
            "length": self.length,
            "volume": round(self.volume, 1),
            "difficulty": round(self.difficulty, 1),
            "effort": round(self.effort, 1),
            # Halstead's own estimate: effort / 18 seconds.
            "estimatedMinutes": round(self.effort / 18 / 60, 1),
        }


def halstead_of(node: Node) -> Halstead:
    operators: dict[str, int] = {}
    operands: dict[str, int] = {}
    for current in node.walk():
        if current.kind in OPERATOR_KINDS:
            token = str(current.meta.get("op") or current.meta.get("callee") or current.kind.value)
            operators[token] = operators.get(token, 0) + 1
        elif current.kind in OPERAND_KINDS:
            token = str(current.name or current.meta.get("value") or "?")
            operands[token] = operands.get(token, 0) + 1
    return Halstead(
        distinct_operators=len(operators),
        distinct_operands=len(operands),
        total_operators=sum(operators.values()),
        total_operands=sum(operands.values()),
    )


def cyclomatic_of(node: Node) -> int:
    """McCabe: one path, plus one per decision point.

    A short-circuiting `a and b and c` contributes two, not one. Each operand after the
    first is its own branch at runtime.
    """
    total = 1
    for current in node.walk():
        if current is not node and current.kind in CALLABLE_KINDS:
            continue  # nested functions are scored separately
        if current.kind is Kind.BOOLOP:
            total += max(1, int(current.meta.get("operand_count", 2)) - 1)
        elif current.kind in DECISION_KINDS:
            total += 1
    return total


def cognitive_of(node: Node) -> int:
    """SonarSource cognitive complexity: how hard the flow is to hold in your head.

    Differs from McCabe in the part that matters for explanation. Nesting is punished.
    Three sequential `if`s score 3; three nested `if`s score 6.
    """
    total = 0

    def visit(current: Node, nesting: int) -> None:
        nonlocal total
        for child in current.children:
            if child.kind in CALLABLE_KINDS:
                visit(child, 0)
                continue
            increment = 0
            deeper = nesting
            if child.kind in NESTING_KINDS:
                # `else if` is a continuation of one decision, not a fresh nesting level.
                if child.meta.get("is_elif"):
                    increment = 1
                else:
                    increment = 1 + nesting
                    deeper = nesting + 1
            elif child.kind is Kind.BOOLOP or (child.kind in {Kind.BREAK, Kind.CONTINUE} and child.meta.get("labeled")):
                increment = 1
            total += increment
            visit(child, deeper)

    visit(node, 0)
    return total


def max_nesting_of(node: Node) -> int:
    deepest = 0

    def visit(current: Node, depth: int) -> None:
        nonlocal deepest
        deepest = max(deepest, depth)
        for child in current.children:
            if child.kind in CALLABLE_KINDS:
                visit(child, 0)
            elif child.kind in NESTING_KINDS:
                visit(child, depth + 1)
            else:
                visit(child, depth)

    visit(node, 0)
    return deepest


def maintainability_index(volume: float, cyclomatic: int, lines: int) -> float:
    """Classic MI, normalised to 0-100.

    Reported as a band rather than a bare number in the UI, because the absolute value
    means little without the formula in front of you.
    """
    if lines <= 0:
        return 100.0
    raw = (
        171
        - 5.2 * math.log(max(volume, 1.0))
        - 0.23 * cyclomatic
        - 16.2 * math.log(max(lines, 1))
    )
    return round(max(0.0, min(100.0, raw * 100 / 171)), 1)


def rating(maintainability: float) -> str:
    if maintainability >= 85:
        return "A"
    if maintainability >= 70:
        return "B"
    if maintainability >= 55:
        return "C"
    if maintainability >= 40:
        return "D"
    return "F"


@dataclass(slots=True)
class FunctionMetrics:
    name: str
    qualified_name: str
    node_id: int
    line: int
    end_line: int
    kind: str
    param_count: int
    lines: int
    cyclomatic: int
    cognitive: int
    max_nesting: int
    halstead: Halstead
    calls: list[str] = field(default_factory=list)
    is_recursive: bool = False
    complexity_class: str = "O(1)"
    complexity_reason: str = ""
    is_async: bool = False
    is_generator: bool = False

    @property
    def maintainability(self) -> float:
        return maintainability_index(self.halstead.volume, self.cyclomatic, self.lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "qualifiedName": self.qualified_name,
            "nodeId": self.node_id,
            "line": self.line,
            "endLine": self.end_line,
            "kind": self.kind,
            "paramCount": self.param_count,
            "lines": self.lines,
            "cyclomatic": self.cyclomatic,
            "cognitive": self.cognitive,
            "maxNesting": self.max_nesting,
            "isRecursive": self.is_recursive,
            "isAsync": self.is_async,
            "isGenerator": self.is_generator,
            "calls": self.calls,
            "complexityClass": self.complexity_class,
            "complexityReason": self.complexity_reason,
            "halstead": self.halstead.to_dict(),
            "maintainability": self.maintainability,
            "rating": rating(self.maintainability),
        }


@dataclass(slots=True)
class FileMetrics:
    lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    cyclomatic: int
    cognitive: int
    max_nesting: int
    halstead: Halstead
    function_count: int
    class_count: int
    max_function_complexity: int
    loop_count: int
    branch_count: int
    call_count: int

    @property
    def maintainability(self) -> float:
        return maintainability_index(self.halstead.volume, self.cyclomatic, self.code_lines)

    @property
    def comment_ratio(self) -> float:
        total = self.code_lines + self.comment_lines
        return round(self.comment_lines / total, 3) if total else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "lines": self.lines,
            "codeLines": self.code_lines,
            "commentLines": self.comment_lines,
            "blankLines": self.blank_lines,
            "commentRatio": self.comment_ratio,
            "cyclomatic": self.cyclomatic,
            "cognitive": self.cognitive,
            "maxNesting": self.max_nesting,
            "functionCount": self.function_count,
            "classCount": self.class_count,
            "loopCount": self.loop_count,
            "branchCount": self.branch_count,
            "callCount": self.call_count,
            "maxFunctionComplexity": self.max_function_complexity,
            "halstead": self.halstead.to_dict(),
            "maintainability": self.maintainability,
            "rating": rating(self.maintainability),
        }


def file_metrics(root: Node, source: str) -> FileMetrics:
    raw_lines = source.splitlines()
    blank = sum(1 for line in raw_lines if not line.strip())
    comment_lines = {
        line
        for node in root.find(Kind.COMMENT)
        for line in range(node.span.start_line, node.span.end_line + 1)
    }
    functions = [n for n in root.walk() if n.kind in CALLABLE_KINDS]
    return FileMetrics(
        lines=len(raw_lines),
        code_lines=max(len(raw_lines) - blank - len(comment_lines), 0),
        comment_lines=len(comment_lines),
        blank_lines=blank,
        cyclomatic=cyclomatic_of(root),
        cognitive=cognitive_of(root),
        max_nesting=max_nesting_of(root),
        halstead=halstead_of(root),
        function_count=len(functions),
        class_count=sum(1 for _ in root.find(Kind.CLASS, Kind.INTERFACE)),
        max_function_complexity=max((cyclomatic_of(f) for f in functions), default=1),
        loop_count=sum(1 for n in root.walk() if n.kind in LOOP_KINDS),
        branch_count=sum(1 for _ in root.find(Kind.BRANCH, Kind.SWITCH)),
        call_count=sum(1 for _ in root.find(Kind.CALL, Kind.METHOD_CALL)),
    )
