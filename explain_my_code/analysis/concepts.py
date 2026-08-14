"""Concept detection: the named ideas a reader needs in order to follow the code.

This is the feature the v1 keyword tooltips could not express. "This line uses a
comprehension" is a fact about a token; "this file leans on recursion, memoisation and
closures" is a fact about the program, and it is what someone learning the code
actually wants to be told up front.

Every concept carries text at all three levels, so the sidebar re-pitches with the
rest of the page instead of staying at one reading age.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from explain_my_code.ir import (
    CALLABLE_KINDS,
    LOOP_KINDS,
    Kind,
    Language,
    Level,
    Node,
    Span,
)


@dataclass(slots=True)
class ConceptHit:
    concept_id: str
    label: str
    texts: dict[Level, str]
    spans: list[Span] = field(default_factory=list)
    node_ids: list[int] = field(default_factory=list)
    category: str = "general"

    @property
    def count(self) -> int:
        return len(self.spans)

    def to_dict(self, level: Level | None = None) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.concept_id,
            "label": self.label,
            "category": self.category,
            "count": self.count,
            "lines": sorted({s.start_line for s in self.spans})[:20],
            "nodeIds": self.node_ids[:20],
        }
        if level is not None:
            out["text"] = self.texts.get(level, self.texts.get(Level.BEGINNER, ""))
        else:
            out["texts"] = {lv.value: t for lv, t in self.texts.items()}
        return out


Detector = Callable[[Node, Language], list[Node]]


@dataclass(slots=True)
class Concept:
    concept_id: str
    label: str
    category: str
    eli5: str
    beginner: str
    developer: str
    detect: Detector
    languages: frozenset[Language] | None = None

    def texts(self) -> dict[Level, str]:
        return {Level.ELI5: self.eli5, Level.BEGINNER: self.beginner, Level.DEVELOPER: self.developer}


# -- detector helpers -------------------------------------------------------------


def of_kind(*kinds: Kind) -> Detector:
    wanted = set(kinds)

    def detect(root: Node, _language: Language) -> list[Node]:
        return [n for n in root.walk() if n.kind in wanted]

    return detect


def where(kind: Kind, **conditions: Any) -> Detector:
    def detect(root: Node, _language: Language) -> list[Node]:
        return [
            n
            for n in root.walk()
            if n.kind is kind and all(n.meta.get(k) == v for k, v in conditions.items())
        ]

    return detect


def meta_truthy(kind: Kind, key: str) -> Detector:
    def detect(root: Node, _language: Language) -> list[Node]:
        return [n for n in root.walk() if n.kind is kind and n.meta.get(key)]

    return detect


def _nested_callables(root: Node, _language: Language) -> list[Node]:
    return [
        n
        for n in root.walk()
        if n.kind in CALLABLE_KINDS and n.enclosing_callable is not None and n.kind is not Kind.METHOD
    ]


def _higher_order(root: Node, _language: Language) -> list[Node]:
    out: list[Node] = []
    for node in root.walk():
        if node.kind not in {Kind.CALL, Kind.METHOD_CALL}:
            continue
        if any(child.kind is Kind.LAMBDA for child in node.children):
            out.append(node)
    return out


def _nested_loops(root: Node, _language: Language) -> list[Node]:
    return [n for n in root.walk() if n.kind in LOOP_KINDS and n.loop_depth >= 1]


def _accumulator(root: Node, _language: Language) -> list[Node]:
    return [
        n
        for n in root.walk()
        if n.kind is Kind.AUG_ASSIGN and n.loop_depth >= 1 and n.meta.get("is_accumulator")
    ]


def _guard_clauses(root: Node, _language: Language) -> list[Node]:
    return [n for n in root.walk() if n.kind is Kind.BRANCH and n.meta.get("is_guard")]


def _dunder_methods(root: Node, _language: Language) -> list[Node]:
    return [
        n
        for n in root.walk()
        if n.kind in {Kind.METHOD, Kind.CONSTRUCTOR}
        and n.meta.get("is_dunder")
        and n.name not in {"__init__", "__new__"}
    ]


def _inheritance(root: Node, _language: Language) -> list[Node]:
    return [n for n in root.walk() if n.kind is Kind.CLASS and n.meta.get("is_subclass")]


def _overrides(root: Node, _language: Language) -> list[Node]:
    return [n for n in root.walk() if n.kind is Kind.METHOD and n.meta.get("is_override")]


def _bitwise(root: Node, _language: Language) -> list[Node]:
    return [
        n for n in root.walk() if n.kind is Kind.BINOP and n.meta.get("op") in {"&", "|", "^", "<<", ">>", "~"}
    ]


def _sorting(root: Node, _language: Language) -> list[Node]:
    return [
        n
        for n in root.walk()
        if n.kind in {Kind.CALL, Kind.METHOD_CALL}
        and str(n.meta.get("callee", "")).lower() in {"sort", "sorted", "sort_values", "stable_sort", "order_by"}
    ]


def _hash_lookup(root: Node, _language: Language) -> list[Node]:
    return [
        n
        for n in root.walk()
        if (n.kind is Kind.COMPARE and n.meta.get("is_membership"))
        or (n.kind is Kind.COLLECTION and n.meta.get("collection_type") in {"dict", "set", "object"})
    ]


def _manual_memory(root: Node, _language: Language) -> list[Node]:
    return [n for n in root.walk() if n.kind in {Kind.NEW, Kind.DELETE}]


def _pointers(root: Node, _language: Language) -> list[Node]:
    return [
        n
        for n in root.walk()
        if n.meta.get("is_pointer") or n.meta.get("via_pointer")
    ]


def _templates(root: Node, _language: Language) -> list[Node]:
    return [n for n in root.walk() if n.meta.get("is_template") or n.meta.get("is_generic")]


def _memoization(root: Node, _language: Language) -> list[Node]:
    out: list[Node] = []
    for node in root.walk():
        if node.kind not in CALLABLE_KINDS:
            continue
        decorators = " ".join(str(d) for d in node.meta.get("decorators", [])).lower()
        if "cache" in decorators or "memo" in decorators:
            out.append(node)
    return out


def _full_table_scan(root: Node, _language: Language) -> list[Node]:
    return [n for n in root.walk() if n.kind is Kind.SELECT and not n.meta.get("has_where")]


# -- the catalogue -----------------------------------------------------------------

CONCEPTS: list[Concept] = [
    Concept(
        "recursion", "Recursion", "control-flow",
        "A function that calls itself, like a mirror facing a mirror. Each copy solves a smaller piece until one is tiny enough to answer straight away.",
        "A function calls itself on a smaller input. It needs a base case that returns without recursing, or it never stops.",
        "Self-referential call. Watch the stack depth and whether overlapping subproblems justify memoisation.",
        lambda root, lang: [],  # filled in by the pipeline, which owns the call graph
    ),
    Concept(
        "closure", "Closure", "functions",
        "A little function that remembers the things around it, even after the bigger function has finished.",
        "A function defined inside another captures the outer function's variables and keeps them alive after the outer call returns.",
        "Inner function capturing enclosing scope. The captured binding is by reference, which bites in loops.",
        _nested_callables,
    ),
    Concept(
        "higher-order-function", "Higher-order function", "functions",
        "A function handed to another function as if it were a toy being passed along.",
        "A function taken as an argument, so the caller decides part of the behaviour.",
        "Function passed as a value. The usual map/filter/reduce and callback shapes.",
        _higher_order,
    ),
    Concept(
        "comprehension", "Comprehension", "data",
        "A shortcut for building a whole list in one line instead of adding items one at a time.",
        "Builds a collection in a single expression, replacing a loop that appends.",
        "Comprehension. Usually faster than the equivalent append loop and evaluates eagerly unless it is a generator expression.",
        of_kind(Kind.COMPREHENSION),
    ),
    Concept(
        "generator", "Generator", "control-flow",
        "A function that hands you one thing at a time instead of a whole basket at once.",
        "Yields values lazily, one per request, so the whole sequence never has to exist in memory.",
        "Lazy iterator protocol. Constant memory over the sequence; the function's frame is suspended between yields.",
        of_kind(Kind.YIELD),
    ),
    Concept(
        "async-await", "Async / await", "concurrency",
        "Code that can pause politely while it waits, letting other work happen instead of everyone standing still.",
        "Marks work that waits on something slow (network, disk) so the program can run other tasks meanwhile.",
        "Coroutine suspension points. Concurrency, not parallelism — one thread interleaves at each await.",
        of_kind(Kind.AWAIT),
    ),
    Concept(
        "error-handling", "Error handling", "robustness",
        "A safety net. If something goes wrong, the code catches the problem instead of crashing.",
        "Wraps risky work so failures are handled deliberately rather than stopping the program.",
        "Exception boundary. Check that the caught type is narrow enough and that the handler does not swallow the failure.",
        of_kind(Kind.TRY),
    ),
    Concept(
        "context-manager", "Context manager", "robustness",
        "Something that tidies up after itself, like a door that always closes behind you.",
        "Guarantees cleanup (closing a file, releasing a lock) even if the body raises.",
        "RAII-style scoped resource management via the enter/exit protocol.",
        of_kind(Kind.WITH),
    ),
    Concept(
        "decorator", "Decorator", "functions",
        "A sticker put on a function that gives it an extra power without changing what is inside.",
        "Wraps a function to add behaviour — caching, logging, access checks — without editing its body.",
        "Higher-order wrapper applied at definition time. Preserve metadata with functools.wraps.",
        of_kind(Kind.DECORATOR),
    ),
    Concept(
        "inheritance", "Inheritance", "objects",
        "A new kind of thing that borrows everything an older thing could do, then adds its own tricks.",
        "A class builds on another, reusing its methods and adding or replacing some.",
        "Subtyping. Watch for deep hierarchies and prefer composition when the relationship is not genuinely is-a.",
        _inheritance,
    ),
    Concept(
        "polymorphism", "Method override", "objects",
        "A child doing the same job as its parent, but in its own way.",
        "A subclass replaces a method it inherited, so the same call does something different per type.",
        "Dynamic dispatch on the runtime type. Keep the override's contract compatible with the base.",
        _overrides,
    ),
    Concept(
        "operator-overloading", "Operator overloading", "objects",
        "Teaching your own thing how to respond to symbols like + or ==.",
        "Special methods let a custom type work with built-in operators and functions.",
        "Protocol methods hooking into the language's operator dispatch.",
        _dunder_methods,
    ),
    Concept(
        "memoization", "Memoisation", "performance",
        "Remembering answers you already worked out so you never do the same sum twice.",
        "Caches results by input, turning repeated expensive calls into lookups.",
        "Result cache keyed on arguments. Turns exponential recursion linear when subproblems overlap.",
        _memoization,
    ),
    Concept(
        "guard-clause", "Guard clause", "control-flow",
        "Checking for the easy or broken cases first and leaving early, so the rest reads cleanly.",
        "An early return for edge cases, which keeps the main logic un-nested.",
        "Early exit that flattens nesting. Generally preferable to a trailing else.",
        _guard_clauses,
    ),
    Concept(
        "accumulator", "Accumulator pattern", "data",
        "Keeping a running total in a box and dropping something into it each time round.",
        "A variable outside the loop collects results as the loop runs.",
        "Fold over the sequence. Often expressible as sum/reduce or a comprehension.",
        _accumulator,
    ),
    Concept(
        "nested-loops", "Nested loops", "performance",
        "A loop inside a loop — for every item in the first, it goes through all of the second.",
        "Each level multiplies the work, so two nested loops over n items do n × n steps.",
        "Quadratic or worse. The usual fix is a hash index over the inner collection.",
        _nested_loops,
    ),
    Concept(
        "sorting", "Sorting", "algorithms",
        "Putting things in order, smallest to biggest.",
        "Reorders a collection by a key. Costs about n log n, more than a single pass.",
        "Comparison sort at O(n log n). Hoist it out of loops and sort once where possible.",
        _sorting,
    ),
    Concept(
        "hash-lookup", "Hash lookup", "performance",
        "A magic index that finds the thing you want instantly instead of checking every item.",
        "Dictionaries and sets find items in roughly one step, no matter how many there are.",
        "Amortised O(1) membership and retrieval. The standard replacement for a linear scan in a loop.",
        _hash_lookup,
    ),
    Concept(
        "destructuring", "Destructuring", "data",
        "Unpacking a bundle into separate named pieces in one go.",
        "Pulls several values out of a collection or object in one statement.",
        "Pattern-based binding. Fails loudly on arity mismatch, which is usually what you want.",
        of_kind(Kind.DESTRUCTURE),
    ),
    Concept(
        "string-interpolation", "String interpolation", "data",
        "Slotting values straight into a sentence instead of gluing pieces together.",
        "Embeds expressions inside a string literal rather than concatenating.",
        "Formatted literal, evaluated at runtime. Never build SQL or shell commands this way.",
        of_kind(Kind.FSTRING),
    ),
    Concept(
        "short-circuit", "Short-circuit evaluation", "control-flow",
        "Stopping as soon as the answer is obvious, without checking the rest.",
        "`and` stops at the first false, `or` stops at the first true — the rest is never evaluated.",
        "Lazy boolean evaluation. Relied on for null guards; also why side effects in conditions are risky.",
        of_kind(Kind.BOOLOP),
    ),
    Concept(
        "bitwise", "Bitwise operations", "low-level",
        "Working with the tiny on/off switches that numbers are made of.",
        "Manipulates individual bits — used for flags, masks, and fast multiply/divide by powers of two.",
        "Bit-level ops. Cheap, but check signedness and shift-width assumptions.",
        _bitwise,
    ),
    Concept(
        "manual-memory", "Manual memory management", "low-level",
        "Asking for space to store things, and remembering to give it back when done.",
        "Memory is allocated explicitly and must be released explicitly, or it leaks.",
        "Raw new/delete. Prefer RAII containers and smart pointers; every path out must free.",
        _manual_memory,
        languages=frozenset({Language.CPP}),
    ),
    Concept(
        "pointers", "Pointers and references", "low-level",
        "A note that says where something lives, instead of the thing itself.",
        "Holds an address rather than a value, so several places can share and modify one object.",
        "Indirection. Watch lifetime, nullability and aliasing.",
        _pointers,
        languages=frozenset({Language.CPP}),
    ),
    Concept(
        "generics", "Generics / templates", "types",
        "One recipe that works for any ingredient, instead of a separate recipe per ingredient.",
        "Code parameterised by type, so the same class or function serves many types safely.",
        "Parametric polymorphism. In C++ it is compile-time instantiation; in Java it is erasure.",
        _templates,
    ),
    # -- SQL ------------------------------------------------------------------
    Concept(
        "sql-join", "Join", "sql",
        "Sticking two tables together so rows about the same thing line up side by side.",
        "Combines rows from two tables where a key matches. The join type decides what happens to non-matching rows.",
        "Relational join. Cardinality and index coverage on the join key drive the plan.",
        of_kind(Kind.JOIN),
        languages=frozenset({Language.SQL}),
    ),
    Concept(
        "sql-aggregation", "Aggregation", "sql",
        "Squashing lots of rows into one summary number, like counting or totalling.",
        "Collapses groups of rows into a single value per group — count, sum, average.",
        "Aggregate over a grouping set. Non-aggregated projections must appear in GROUP BY.",
        of_kind(Kind.AGGREGATE),
        languages=frozenset({Language.SQL}),
    ),
    Concept(
        "sql-cte", "Common table expression", "sql",
        "Naming a sub-question so you can use its answer in the big question.",
        "A named temporary result you can reference later, which keeps long queries readable.",
        "WITH clause. Materialisation is engine-dependent; recursive CTEs need a termination branch.",
        of_kind(Kind.CTE),
        languages=frozenset({Language.SQL}),
    ),
    Concept(
        "sql-window", "Window function", "sql",
        "Working out a number for each row while still being able to peek at its neighbours.",
        "Computes across a set of related rows without collapsing them, so every row survives.",
        "Windowed aggregate over PARTITION/ORDER. Unlike GROUP BY, row count is preserved.",
        of_kind(Kind.WINDOW),
        languages=frozenset({Language.SQL}),
    ),
    Concept(
        "sql-subquery", "Subquery", "sql",
        "A question tucked inside another question.",
        "A query nested inside another, used as a value, a filter, or a table.",
        "Nested query. Correlated subqueries re-execute per outer row; consider a join or window instead.",
        of_kind(Kind.SUBQUERY),
        languages=frozenset({Language.SQL}),
    ),
    Concept(
        "sql-full-scan", "Unfiltered read", "sql",
        "Looking at every single row in the table, because nothing narrows it down.",
        "No WHERE clause, so the database reads the whole table.",
        "Full scan. Fine on small tables, expensive at scale — add a predicate or a limit.",
        _full_table_scan,
        languages=frozenset({Language.SQL}),
    ),
]

CONCEPTS_BY_ID = {c.concept_id: c for c in CONCEPTS}


def detect_concepts(root: Node, language: Language) -> list[ConceptHit]:
    hits: list[ConceptHit] = []
    for concept in CONCEPTS:
        if concept.languages is not None and language not in concept.languages:
            continue
        nodes = concept.detect(root, language)
        if not nodes:
            continue
        hits.append(
            ConceptHit(
                concept_id=concept.concept_id,
                label=concept.label,
                texts=concept.texts(),
                spans=[n.span for n in nodes],
                node_ids=[n.id for n in nodes],
                category=concept.category,
            )
        )
    hits.sort(key=lambda hit: (-hit.count, hit.label))
    return hits


def concept_hit(concept_id: str, nodes: list[Node]) -> ConceptHit | None:
    """Build a hit for a concept the pipeline detects itself (recursion, say)."""
    concept = CONCEPTS_BY_ID.get(concept_id)
    if concept is None or not nodes:
        return None
    return ConceptHit(
        concept_id=concept.concept_id,
        label=concept.label,
        texts=concept.texts(),
        spans=[n.span for n in nodes],
        node_ids=[n.id for n in nodes],
        category=concept.category,
    )
