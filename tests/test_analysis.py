"""Analysis passes: metrics, call graph, complexity heuristic, findings, symbols."""

from __future__ import annotations

import pytest

from explain_my_code.analysis.metrics import maintainability_index
from explain_my_code.core import explain
from explain_my_code.ir import Language, Level


def analyze(source: str, language: Language = Language.PYTHON):
    return explain(source, language=language).analysis


def function(analysis, name: str):
    return next(f for f in analysis.functions if f.name == name)


# -- complexity ------------------------------------------------------------------


def test_cyclomatic_counts_each_decision_point():
    analysis = analyze("""
def classify(n):
    if n < 0:
        return "negative"
    elif n == 0:
        return "zero"
    for _ in range(n):
        pass
    return "positive"
""")
    # 1 baseline + 2 branches + 1 loop
    assert function(analysis, "classify").cyclomatic == 4


def test_boolean_operators_add_a_path_each():
    analysis = analyze("def check(a, b, c):\n    return a and b and c\n")
    assert function(analysis, "check").cyclomatic == 3


def test_cognitive_complexity_punishes_nesting_over_sequence():
    sequential = analyze("""
def flat(a, b, c):
    if a: pass
    if b: pass
    if c: pass
""")
    nested = analyze("""
def deep(a, b, c):
    if a:
        if b:
            if c:
                pass
""")
    assert function(sequential, "flat").cognitive == 3
    assert function(nested, "deep").cognitive == 6
    # Same cyclomatic score, different readability — that is the whole point.
    assert function(sequential, "flat").cyclomatic == function(nested, "deep").cyclomatic


def test_max_nesting_is_measured_per_function():
    analysis = analyze("""
def outer(rows):
    for row in rows:
        for cell in row:
            if cell:
                return cell

def shallow(x):
    return x
""")
    assert function(analysis, "outer").max_nesting == 3
    assert function(analysis, "shallow").max_nesting == 0


def test_maintainability_index_is_bounded():
    assert maintainability_index(0, 1, 0) == 100.0
    assert 0.0 <= maintainability_index(90_000, 400, 5000) <= 100.0


# -- asymptotic heuristic ---------------------------------------------------------


def test_no_loops_is_constant():
    analysis = analyze("def add(a, b):\n    return a + b\n")
    assert function(analysis, "add").complexity_class == "O(1)"


def test_one_loop_is_linear():
    analysis = analyze("def total(xs):\n    out = 0\n    for x in xs:\n        out += x\n    return out\n")
    assert function(analysis, "total").complexity_class == "O(n)"


def test_nested_loops_are_quadratic():
    analysis = analyze("""
def pairs(xs, ys):
    out = []
    for a in xs:
        for b in ys:
            out.append((a, b))
    return out
""")
    assert function(analysis, "pairs").complexity_class == "O(n²)"


def test_naive_recursion_is_exponential():
    analysis = analyze("""
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
""")
    fib = function(analysis, "fib")
    assert fib.is_recursive
    assert fib.complexity_class == "O(2^n)"


def test_memoisation_changes_the_asymptotic_answer():
    analysis = analyze("""
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
""")
    fib = function(analysis, "fib")
    assert fib.is_recursive
    assert fib.complexity_class == "O(n)", "the decorator must be taken into account"


def test_a_sort_inside_a_loop_is_reported():
    analysis = analyze("""
def process(groups):
    out = []
    for group in groups:
        out.append(sorted(group))
    return out
""")
    assert "log n" in function(analysis, "process").complexity_class


# -- call graph --------------------------------------------------------------------


def test_direct_recursion_is_detected():
    analysis = analyze("def countdown(n):\n    if n:\n        countdown(n - 1)\n")
    assert analysis.call_graph.is_recursive("module.countdown")


def test_mutual_recursion_is_detected_through_the_cycle():
    analysis = analyze("""
def is_even(n):
    return True if n == 0 else is_odd(n - 1)

def is_odd(n):
    return False if n == 0 else is_even(n - 1)
""")
    cycles = analysis.call_graph.cycles
    assert cycles, "Tarjan found no cycle"
    assert set(cycles[0]) == {"module.is_even", "module.is_odd"}
    assert function(analysis, "is_even").is_recursive


def test_undefined_callees_are_recorded_as_external():
    analysis = analyze("def go():\n    requests.get('https://example.com')\n")
    assert "get" in analysis.call_graph.external


def test_call_graph_terminates_on_a_long_chain():
    """The SCC pass is iterative; a deep chain must not blow the stack."""
    source = "\n".join(f"def f{i}():\n    return f{i + 1}()\n" for i in range(400))
    analysis = analyze(source + "def f400():\n    return 0\n")
    assert len(analysis.functions) == 401


# -- findings ----------------------------------------------------------------------


def rules(analysis) -> set[str]:
    return {finding.rule for finding in analysis.findings}


def test_bare_except_and_swallowed_error():
    analysis = analyze("def risky():\n    try:\n        go()\n    except:\n        pass\n")
    assert {"bare-except", "swallowed-exception"} <= rules(analysis)


def test_mutable_default_argument():
    analysis = analyze("def add(item, bucket=[]):\n    bucket.append(item)\n    return bucket\n")
    assert "mutable-default" in rules(analysis)


def test_infinite_loop_without_a_break():
    analysis = analyze("def spin():\n    while True:\n        pass\n")
    assert "infinite-loop" in rules(analysis)


def test_a_loop_with_a_break_is_not_flagged():
    analysis = analyze("def spin():\n    while True:\n        break\n")
    assert "infinite-loop" not in rules(analysis)


def test_deep_nesting_is_flagged():
    analysis = analyze("""
def deep(a):
    for x in a:
        for y in x:
            for z in y:
                if z:
                    return z
""")
    assert "deep-nesting" in rules(analysis)


def test_exponential_recursion_is_high_severity():
    analysis = analyze("def fib(n):\n    return n if n <= 1 else fib(n-1) + fib(n-2)\n")
    finding = next(f for f in analysis.findings if f.rule == "exponential-recursion")
    assert finding.severity == "high"


def test_sql_write_without_a_where_clause():
    analysis = analyze("DELETE FROM users;", Language.SQL)
    assert "unfiltered-write" in rules(analysis)
    assert next(f for f in analysis.findings if f.rule == "unfiltered-write").severity == "high"


def test_sql_cross_join_is_flagged():
    analysis = analyze("SELECT * FROM a CROSS JOIN b;", Language.SQL)
    assert "cross-join" in rules(analysis)
    assert "select-star" in rules(analysis)


def test_clean_code_produces_no_findings():
    analysis = analyze("def double(x):\n    return x * 2\n")
    assert analysis.findings == []


# -- symbols ------------------------------------------------------------------------


def test_unused_local_is_reported():
    analysis = analyze("def go():\n    used = 1\n    unused = 2\n    return used\n")
    assert "unused" in {symbol.name for symbol in analysis.symbols.unused}


def test_underscore_prefixed_names_are_left_alone():
    analysis = analyze("def go():\n    _ignored = 1\n    return 2\n")
    assert "_ignored" not in {symbol.name for symbol in analysis.symbols.unused}


# -- concepts -----------------------------------------------------------------------


def concept_ids(analysis) -> set[str]:
    return {hit.concept_id for hit in analysis.concepts}


def test_concepts_are_detected():
    analysis = analyze("""
async def load(urls):
    results = [await fetch(u) for u in urls]
    try:
        return {r.id: r for r in results}
    except KeyError:
        raise
""")
    assert {"comprehension", "async-await", "error-handling"} <= concept_ids(analysis)


def test_sql_concepts_are_language_scoped():
    python = analyze("def f():\n    return 1\n")
    assert not {c for c in concept_ids(python) if c.startswith("sql-")}
    sql = analyze("SELECT a FROM t JOIN u ON u.id = t.id GROUP BY a;", Language.SQL)
    assert "sql-join" in concept_ids(sql)


def test_every_concept_has_text_at_every_level():
    from explain_my_code.analysis.concepts import CONCEPTS

    for concept in CONCEPTS:
        for level in Level:
            text = concept.texts()[level]
            assert text and len(text) > 20, f"{concept.concept_id} is thin at {level.value}"


@pytest.mark.parametrize("size", [1, 50, 200])
def test_analysis_scales_without_blowing_up(size):
    source = "\n".join(f"def f{i}(x):\n    return x + {i}\n" for i in range(size))
    analysis = analyze(source)
    assert len(analysis.functions) == size
