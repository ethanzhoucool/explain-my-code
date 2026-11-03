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


CHAIN_SHAPES = {
 "loop-if-else": {
  "python": "def f(xs):\n    for x in xs:\n        if x:\n            a()\n        else:\n            b()\n",
  "javascript": "function f(xs) {\n  for (const x of xs) {\n    if (x) {\n      a();\n    } else {\n      b();\n    }\n  }\n}\n",
  "java": "class A {\n  void f(int[] xs) {\n    for (int x : xs) {\n      if (x > 0) {\n        a();\n      } else {\n        b();\n      }\n    }\n  }\n}\n",
  "cpp": "void f(std::vector<int> xs) {\n  for (int x : xs) {\n    if (x) {\n      a();\n    } else {\n      b();\n    }\n  }\n}\n",
 },
 "if-inside-elif": {
  "python": "def f(a, b, c):\n    if a:\n        x()\n    elif b:\n        if c:\n            y()\n",
  "javascript": "function f(a, b, c) {\n  if (a) {\n    x();\n  } else if (b) {\n    if (c) {\n      y();\n    }\n  }\n}\n",
  "java": "class A {\n  void f(boolean a, boolean b, boolean c) {\n    if (a) {\n      x();\n    } else if (b) {\n      if (c) {\n        y();\n      }\n    }\n  }\n}\n",
  "cpp": "void f(bool a, bool b, bool c) {\n  if (a) {\n    x();\n  } else if (b) {\n    if (c) {\n      y();\n    }\n  }\n}\n",
 },
 "five-arm-chain": {
  "python": "def f(n):\n    if n == 1:\n        return 1\n    elif n == 2:\n        return 2\n    elif n == 3:\n        return 3\n    elif n == 4:\n        return 4\n    else:\n        return 5\n",
  "javascript": "function f(n) {\n  if (n === 1) { return 1; }\n  else if (n === 2) { return 2; }\n  else if (n === 3) { return 3; }\n  else if (n === 4) { return 4; }\n  else { return 5; }\n}\n",
  "java": "class A {\n  int f(int n) {\n    if (n == 1) { return 1; }\n    else if (n == 2) { return 2; }\n    else if (n == 3) { return 3; }\n    else if (n == 4) { return 4; }\n    else { return 5; }\n  }\n}\n",
  "cpp": "int f(int n) {\n  if (n == 1) { return 1; }\n  else if (n == 2) { return 2; }\n  else if (n == 3) { return 3; }\n  else if (n == 4) { return 4; }\n  else { return 5; }\n}\n",
 },
 "nested-if-in-else-block": {
  "javascript": "function f(a, c) {\n  if (a) {\n    x();\n  } else {\n    y();\n    if (c) {\n      z();\n    }\n  }\n}\n",
  "java": "class A {\n  void f(boolean a, boolean c) {\n    if (a) {\n      x();\n    } else {\n      y();\n      if (c) {\n        z();\n      }\n    }\n  }\n}\n",
  "cpp": "void f(bool a, bool c) {\n  if (a) {\n    x();\n  } else {\n    y();\n    if (c) {\n      z();\n    }\n  }\n}\n",
  "python": "def f(a, c):\n    if a:\n        x()\n    else:\n        y()\n        if c:\n            z()\n",
 },
}

#: (cyclomatic, cognitive, max nesting), per SonarSource's rules for cognitive: `else`
#: and `else if` add one with no nesting penalty, and their bodies are nested one level.
CHAIN_EXPECTED = {
    "loop-if-else": (3, 4, 2),
    "if-inside-elif": (4, 4, 2),
    "five-arm-chain": (5, 5, 1),
    "nested-if-in-else-block": (3, 4, 2),
}


@pytest.mark.parametrize("shape", list(CHAIN_SHAPES))
@pytest.mark.parametrize("language", ["python", "javascript", "java", "cpp"])
def test_if_else_chains_score_the_same_in_every_language(shape, language):
    """Tree-sitter nests `else` / `else if` under the `if` they continue, so each arm
    used to count as a deeper level: a five-arm JS chain scored cognitive 36 and
    nesting 8 where the same Python scores 5 and 1."""
    measured = function(analyze(CHAIN_SHAPES[shape][language], Language(language)), "f")
    assert (measured.cyclomatic, measured.cognitive, measured.max_nesting) == CHAIN_EXPECTED[shape]


def test_nested_functions_are_scored_on_their_own():
    analysis = analyze("""
def outer(rows):
    def inner(row):
        for cell in row:
            for part in cell:
                if part:
                    return part
    return inner
""")
    outer, inner = function(analysis, "outer"), function(analysis, "inner")
    assert (outer.cyclomatic, outer.max_nesting) == (1, 0)
    assert (inner.cyclomatic, inner.max_nesting) == (4, 3)
    assert analysis.metrics.cyclomatic == 4, "the file total still counts every decision"


@pytest.mark.parametrize(
    "language,source,code_lines",
    [
        (Language.PYTHON, "x = 1  # one\ny = 2  # two\n# a note\n", 2),
        (Language.JAVASCRIPT, "const x = 1; // one\n/* a\n\n   note */\nconst y = 2;\n", 2),
        (Language.CPP, "int x = 1; /* one */\n// a note\nint y = /* two */ 2;\n", 2),
    ],
    ids=["python", "javascript", "cpp"],
)
def test_lines_with_trailing_comments_are_still_code(language, source, code_lines):
    assert analyze(source, language).metrics.code_lines == code_lines


def test_java_else_gets_explained():
    result = explain(CHAIN_SHAPES["nested-if-in-else-block"]["java"], language=Language.JAVA)
    assert any(line.kind.value == "else" and line.line == 5 for line in result.lines)


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


MERGE_SORT = """
def merge_sort(xs):
    if len(xs) <= 1:
        return xs
    mid = len(xs) // 2
    left = merge_sort(xs[:mid])
    right = merge_sort(xs[mid:])
    return merge(left, right)
"""


@pytest.mark.parametrize(
    "language,source,name,expected",
    [
        (Language.PYTHON, MERGE_SORT, "merge_sort", "O(n log n)"),
        (Language.PYTHON, """
def quicksort(xs):
    if len(xs) <= 1:
        return xs
    pivot = xs[0]
    left = [x for x in xs[1:] if x < pivot]
    right = [x for x in xs[1:] if x >= pivot]
    return quicksort(left) + [pivot] + quicksort(right)
""", "quicksort", "O(n log n)"),
        (Language.PYTHON, """
def quicksort(arr, lo, hi):
    if lo < hi:
        p = partition(arr, lo, hi)
        quicksort(arr, lo, p - 1)
        quicksort(arr, p + 1, hi)
""", "quicksort", "O(n log n)"),
        (Language.PYTHON, """
def search(xs, lo, hi, target):
    if lo > hi:
        return -1
    mid = (lo + hi) // 2
    if xs[mid] < target:
        return search(xs, mid + 1, hi, target)
    return search(xs, lo, mid - 1, target)
""", "search", "O(log n)"),
        (Language.PYTHON, """
def height(node):
    if node is None:
        return 0
    return 1 + max(height(node.left), height(node.right))
""", "height", "O(n)"),
        (Language.PYTHON, """
def find(node, key):
    if node is None or node.key == key:
        return node
    if key < node.key:
        return find(node.left, key)
    return find(node.right, key)
""", "find", "O(log n)"),
        (Language.JAVASCRIPT, """
function mergeSort(a) {
  if (a.length <= 1) return a;
  const mid = Math.floor(a.length / 2);
  return merge(mergeSort(a.slice(0, mid)), mergeSort(a.slice(mid)));
}
""", "mergeSort", "O(n log n)"),
        (Language.JAVASCRIPT, """
function size(node) {
  if (!node) return 0;
  return 1 + size(node.left) + size(node.right);
}
""", "size", "O(n)"),
        (Language.CPP, """
int count(Node* n) {
  if (!n) return 0;
  return 1 + count(n->left) + count(n->right);
}
""", "count", "O(n)"),
    ],
    ids=["merge-sort", "quicksort", "quicksort-in-place", "binary-search", "tree-height",
         "bst-find", "js-merge-sort", "js-tree-size", "cpp-tree-count"],
)
def test_divide_and_conquer_and_tree_recursion_are_not_exponential(language, source, name, expected):
    """Two self-calls only blow up when each one shrinks the input by a constant. Halves,
    partitions and tree children each get visited once, and calls in separate `return`s
    never both run."""
    analysis = analyze(source, language)
    assert function(analysis, name).complexity_class == expected
    assert "exponential-recursion" not in rules(analysis)


@pytest.mark.parametrize(
    "language,source,name,expected",
    [
        (Language.PYTHON, """
def hanoi(n, a, b, c):
    if n == 0:
        return
    hanoi(n - 1, a, c, b)
    print(a, c)
    hanoi(n - 1, b, a, c)
""", "hanoi", "O(2^n)"),
        (Language.PYTHON, """
def paths(i, j):
    if i == 0 or j == 0:
        return 1
    return paths(i - 1, j) + paths(i, j - 1)
""", "paths", "O(2^n)"),
        (Language.PYTHON, """
def decode(s):
    if not s:
        return 1
    total = decode(s[1:])
    if len(s) > 1 and s[:2] < "27":
        total += decode(s[2:])
    return total
""", "decode", "O(2^n)"),
        (Language.PYTHON, """
def trib(n):
    if n < 3:
        return 1
    return trib(n - 1) + trib(n - 2) + trib(n - 3)
""", "trib", "O(3^n)"),
        (Language.JAVASCRIPT, "function fib(n) {\n  return n < 2 ? n : fib(n - 1) + fib(n - 2);\n}\n",
         "fib", "O(2^n)"),
    ],
    ids=["hanoi", "grid-paths", "decode-ways", "tribonacci", "js-fib"],
)
def test_constant_step_branching_recursion_stays_exponential(language, source, name, expected):
    analysis = analyze(source, language)
    assert function(analysis, name).complexity_class == expected
    assert "exponential-recursion" in rules(analysis)


@pytest.mark.parametrize(
    "language,source,expected",
    [
        (Language.PYTHON, "def f(xs):\n    total = sum(xs)\n    for x in xs:\n        print(x / total)\n",
         "O(n)"),
        (Language.PYTHON,
         "def f(xs):\n    ys = sorted(xs)\n    for a in ys:\n        for b in ys:\n            print(a, b)\n",
         "O(n²)"),
        (Language.PYTHON, "def f(xs):\n    for x in sorted(xs):\n        print(x)\n", "O(n log n)"),
        (Language.PYTHON, "def f(xs):\n    for x in xs:\n        print(max(xs))\n", "O(n²)"),
        (Language.PYTHON,
         "def f(groups):\n    out = []\n    for g in groups:\n        out.append(sorted(g))\n    return out\n",
         "O(n² log n)"),
        (Language.JAVASCRIPT,
         "function f(xs) {\n  for (const x of xs.filter(Boolean)) {\n    console.log(x);\n  }\n}\n",
         "O(n)"),
    ],
    ids=["linear-call-before-loop", "sort-before-nested-loops", "sorted-iterable",
         "scan-inside-loop", "sort-inside-loop", "js-filtered-iterable"],
)
def test_library_costs_only_multiply_the_loops_they_run_inside(language, source, expected):
    assert function(analyze(source, language), "f").complexity_class == expected


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


@pytest.mark.parametrize(
    "source",
    [
        "def log(msg):\n    logger = get_logger()\n    logger.info(msg)\n",
        "def get(xs, i):\n    return xs[i]\n",
        "def head(xs, n):\n    return xs[:n]\n",
        "def fill(xs, i, v):\n    xs[i] = v\n",
        "def setx(obj, v):\n    obj.x = v\n",
        "def bump(d, k):\n    d[k] += 1\n",
        "def drop(d, k):\n    del d[k]\n",
        "def pair(a, b):\n    return [a, b]\n",
        "def pair(a, b):\n    return a, b\n",
        "def entry(k, v):\n    return {k: v}\n",
        "def copy(xs):\n    return [*xs]\n",
        'def greet(name):\n    return f"hi {name}"\n',
        "def apply(fn, x):\n    return fn(x)\n",
        "def dispatch(handlers, name, x):\n    return handlers[name](x)\n",
        "def check(x, why):\n    assert x > 0, why\n",
        "def fail(err, msg):\n    raise ValueError(msg) from err\n",
        "def gen(x):\n    yield x\n",
        'def route(cmd, verbose):\n    match cmd:\n        case "go" if verbose:\n            return 1\n',
        "LIMIT = 5\n\ndef take(n=LIMIT):\n    return n\n",
        'app = Flask(__name__)\n\n@app.route("/")\ndef index():\n    return "hi"\n',
        "Base = make_base()\n\nclass Model(Base):\n    pass\n",
    ],
    ids=["method-receiver", "index", "slice", "index-store", "attribute-store", "index-augassign",
         "del-index", "list", "tuple", "dict", "starred", "f-string", "callback", "subscript-call",
         "assert", "raise-from", "yield", "match", "default-value", "decorator", "base-class"],
)
def test_python_reads_are_not_reported_as_unused(source):
    """Each of these reads every name it binds. The Python lowering used to drop the
    sub-expression doing the reading, which made the name look assigned-but-unread."""
    assert [symbol.name for symbol in analyze(source).symbols.unused] == []


def test_storing_into_a_container_does_not_shadow_it():
    analysis = analyze("""
memo = {}

def fib(n):
    if n in memo:
        return memo[n]
    memo[n] = fib(n - 1) + fib(n - 2)
    return memo[n]
""")
    assert "shadowed-name" not in rules(analysis)


@pytest.mark.parametrize(
    "source,caller,callee",
    [
        ("def go():\n    return helper().strip()\n\ndef helper():\n    return ''\n", "go", "helper"),
        ("def go(x):\n    return [helper(x)]\n\ndef helper(x):\n    return x\n", "go", "helper"),
        ("def go(xs):\n    while xs:\n        xs.pop()\n    else:\n        helper()\n\n"
         "def helper():\n    return 1\n", "go", "helper"),
        ("def go():\n    raise make_error()\n\ndef make_error():\n    return ValueError()\n",
         "go", "make_error"),
    ],
    ids=["chained-call", "call-in-list", "while-else", "raised-call"],
)
def test_python_call_graph_sees_nested_calls(source, caller, callee):
    graph = analyze(source).call_graph
    assert f"module.{callee}" in graph.edges[f"module.{caller}"]


def test_decorator_calls_belong_to_the_enclosing_scope():
    """`@app.route(...)` runs at definition time, so it is not a call `index` makes."""
    analysis = analyze('app = Flask(__name__)\n\n@app.route("/")\ndef index():\n    return "hi"\n')
    assert analysis.call_graph.edges["module.index"] == []


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


def test_a_long_where_clause_is_one_boolean_run():
    """sqlglot nests `a AND b AND ...` one level per operator; lowered as-is, a
    1,000-term WHERE clause took ~9s and then hit the recursion limit."""
    conditions = " AND ".join(f"c{i} = {i}" for i in range(1_000))
    result = explain(f"SELECT a FROM t WHERE {conditions};", language=Language.SQL)
    assert not result.analysis.degraded
    runs = [n for n in result.analysis.root.walk() if n.kind.value == "boolop"]
    assert [n.meta["operand_count"] for n in runs] == [1_000]


def test_sql_and_python_score_boolean_runs_alike():
    sql = analyze("SELECT 1 FROM t WHERE a = 1 AND (b = 2 OR c = 3) AND d = 4;", Language.SQL)
    python = analyze("x = a == 1 and (b == 2 or c == 3) and d == 4\n")
    assert (sql.metrics.cyclomatic, sql.metrics.cognitive) == (
        python.metrics.cyclomatic, python.metrics.cognitive,
    ) == (4, 2)


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


# -- tree-sitter languages -----------------------------------------------------------


def test_unused_local_is_reported_in_javascript():
    source = "function go() {\n  const used = 1;\n  const unused = 2;\n  return used;\n}\n"
    analysis = analyze(source, Language.JAVASCRIPT)
    assert {symbol.name for symbol in analysis.symbols.unused} == {"unused"}


def test_naive_recursion_is_exponential_in_java_too():
    analysis = analyze(
        "class A {\n  int fib(int n) {\n    if (n < 2) return n;\n"
        "    return fib(n - 1) + fib(n - 2);\n  }\n}\n",
        Language.JAVA,
    )
    assert function(analysis, "fib").complexity_class == "O(2^n)"
    assert "exponential-recursion" in rules(analysis)
