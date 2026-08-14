"""Templates that turn IR nodes into sentences, one phrasing per audience level.

The whole point of lowering five languages into one IR is that this file exists once.
A template is `(Kind, Level) -> str`, filled from `node.meta`, so `for x in xs`,
`for (String s : xs)` and `for (const auto& x : xs)` all reach the same sentence.

Rules for writing templates:
  * ELI5 uses an everyday image and no jargon. It may be loose, never wrong.
  * BEGINNER names the construct and says what it does with these specific values.
  * DEVELOPER assumes the construct is known and says what is worth noticing —
    cost, edge cases, why this shape over another.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from explain_my_code.ir import Kind, Level, Node

Template = str | Callable[[Node], str]

#: Filled by `_slots`, so a template can say "{iterable}" and get a sane fallback.
FALLBACKS = {
    "iterable": "the collection",
    "condition": "the condition",
    "target": "each item",
    "callee": "the function",
    "value": "a value",
    "name": "it",
    "op": "an operator",
    "op_name": "combines",
    "exception": "an error",
    "module": "a module",
    "container": "the collection",
    "key": "a key",
    "receiver": "the object",
    "table": "the table",
    "left": "the left side",
    "right": "the right side",
    "attribute": "a property",
    "object": "the object",
}


def _slots(node: Node) -> dict[str, Any]:
    values: dict[str, Any] = {"name": node.name or "", "kind": node.kind.value}
    for key, value in node.meta.items():
        if isinstance(value, (str, int, float, bool)):
            values[key] = value
        elif isinstance(value, list):
            values[key] = ", ".join(str(v) for v in value[:4]) if value else ""
            values[f"{key}_count"] = len(value)
    for key, fallback in FALLBACKS.items():
        if not values.get(key):
            values[key] = fallback
    return values


def _plural(count: int, singular: str, plural: str | None = None) -> str:
    return singular if count == 1 else (plural or singular + "s")


def _params_phrase(node: Node) -> str:
    params = node.meta.get("params") or []
    names = [str(p.get("name")) for p in params if p.get("name")]
    if not names:
        return "takes nothing"
    if len(names) == 1:
        return f"takes one input, `{names[0]}`"
    return f"takes {len(names)} inputs: " + ", ".join(f"`{n}`" for n in names)


def _typed_params(node: Node) -> str:
    params = node.meta.get("params") or []
    parts = []
    for param in params:
        annotation = param.get("annotation")
        default = param.get("default")
        text = str(param.get("name", ""))
        if annotation:
            text += f": {annotation}"
        if default:
            text += f" = {default}"
        parts.append(text)
    return ", ".join(parts) if parts else "no parameters"


# -- per-kind templates ---------------------------------------------------------------
# Callables get `node`; everything else is `str.format`-ed against `_slots`.

TEMPLATES: dict[Kind, dict[Level, Template]] = {
    Kind.MODULE: {
        Level.ELI5: "This is the whole file — everything below happens here.",
        Level.BEGINNER: "The top level of the file: {statement_count} statements run in order when it loads.",
        Level.DEVELOPER: "Module scope. Anything at this level executes on import.",
    },
    Kind.FUNCTION: {
        Level.ELI5: lambda n: f"`{n.name}` is a set of instructions with a name. It {_params_phrase(n)} and can be used over and over.",
        Level.BEGINNER: lambda n: f"Defines `{n.name}`, which {_params_phrase(n)}"
        + (f" and returns {n.meta['returns']}" if n.meta.get("returns") else "")
        + ".",
        Level.DEVELOPER: lambda n: f"`{n.name}({_typed_params(n)})`"
        + (f" -> {n.meta['returns']}" if n.meta.get("returns") else "")
        + _callable_notes(n),
    },
    Kind.METHOD: {
        Level.ELI5: lambda n: f"`{n.name}` is something this object knows how to do. It {_params_phrase(n)}.",
        Level.BEGINNER: lambda n: f"A method on the class: `{n.name}` {_params_phrase(n)} and runs on one instance at a time.",
        Level.DEVELOPER: lambda n: f"`{n.name}({_typed_params(n)})`"
        + (f" -> {n.meta['returns']}" if n.meta.get("returns") else "")
        + _callable_notes(n),
    },
    Kind.CONSTRUCTOR: {
        Level.ELI5: "This runs once when a new object is made, to set it up.",
        Level.BEGINNER: lambda n: f"The constructor: called when a new instance is created, and {_params_phrase(n)} to set the starting state.",
        Level.DEVELOPER: lambda n: f"Constructor `({_typed_params(n)})`. Establishes the object's invariants; anything not set here is not guaranteed to exist later.",
    },
    Kind.LAMBDA: {
        Level.ELI5: "A tiny throwaway function written right where it is needed.",
        Level.BEGINNER: lambda n: f"An anonymous function taking {n.meta.get('param_count', 0)} {_plural(int(n.meta.get('param_count', 0)), 'input')}, defined inline instead of given a name.",
        Level.DEVELOPER: lambda n: f"Anonymous function `({', '.join(str(p.get('name')) for p in n.meta.get('params', []))})`."
        + (" Captures by reference — check the lifetime of what it holds." if n.meta.get("captures_by_reference") else ""),
    },
    Kind.CLASS: {
        Level.ELI5: lambda n: f"`{n.name}` is a blueprint. You use it to make objects that all work the same way.",
        Level.BEGINNER: lambda n: f"Defines the class `{n.name}`"
        + (f", built on top of {n.meta.get('bases')}" if n.meta.get("is_subclass") else "")
        + f", with {n.meta.get('method_count', 0)} {_plural(int(n.meta.get('method_count', 0)), 'method')}.",
        Level.DEVELOPER: lambda n: f"`class {n.name}`"
        + (f"({', '.join(n.meta.get('bases', []))})" if n.meta.get("bases") else "")
        + (f" implements {', '.join(n.meta.get('interfaces', []))}" if n.meta.get("interfaces") else "")
        + f" — {n.meta.get('method_count', 0)} members.",
    },
    Kind.INTERFACE: {
        Level.ELI5: "A promise about what something can do, without saying how it does it.",
        Level.BEGINNER: "Declares the methods a class must provide, with no implementations of its own.",
        Level.DEVELOPER: "Interface — a contract for callers. Implementers supply the bodies.",
    },
    Kind.PARAM: {
        Level.ELI5: "A blank the function fills in when someone calls it.",
        Level.BEGINNER: lambda n: f"`{n.name}` is an input to `{n.meta.get('owner', 'the function')}`"
        + (f", defaulting to {n.meta['default']} when not supplied" if n.meta.get("default") else "")
        + ".",
        Level.DEVELOPER: lambda n: f"Parameter `{n.name}`"
        + (f": {n.meta['annotation']}" if n.meta.get("annotation") else "")
        + (f" = {n.meta['default']}" if n.meta.get("default") else "")
        + (" (variadic)" if n.meta.get("variadic") else ""),
    },
    Kind.BRANCH: {
        Level.ELI5: "A fork in the road: if this is true, do the next bit; otherwise skip it.",
        Level.BEGINNER: "Checks whether `{condition}` holds. The indented block below runs only when it does{else_note}.",
        Level.DEVELOPER: "Branch on `{condition}`.{guard_note}",
    },
    Kind.ELSE: {
        Level.ELI5: "What to do when the check above was not true.",
        Level.BEGINNER: "Runs only when the condition above was false.",
        Level.DEVELOPER: "Fallback path for the preceding branch.",
    },
    Kind.LOOP_FOREACH: {
        Level.ELI5: "Goes through `{iterable}` one at a time, doing the same thing to each.",
        Level.BEGINNER: "Repeats the block once for every item in `{iterable}`, calling it `{target}` each time round.",
        Level.DEVELOPER: "Iterates `{iterable}`, binding `{target}`.",
    },
    Kind.LOOP_FOR: {
        Level.ELI5: "Counts through a range of numbers, running the block each time.",
        Level.BEGINNER: "A counting loop: starts at `{init}`, keeps going while `{condition}`, and does `{update}` after each pass.",
        Level.DEVELOPER: "Counted loop — init `{init}`, guard `{condition}`, step `{update}`.",
    },
    Kind.LOOP_WHILE: {
        Level.ELI5: "Keeps repeating for as long as `{condition}` stays true.",
        Level.BEGINNER: "Repeats the block while `{condition}` is true. The condition is rechecked before every pass.",
        Level.DEVELOPER: "Pre-test loop on `{condition}`.{termination_note}",
    },
    Kind.LOOP_DO: {
        Level.ELI5: "Does the block once, then keeps going while `{condition}` is true.",
        Level.BEGINNER: "Runs the block first and checks `{condition}` afterwards, so the body always executes at least once.",
        Level.DEVELOPER: "Post-test loop on `{condition}` — body runs at least once.",
    },
    Kind.COMPREHENSION: {
        Level.ELI5: "Builds a whole new {comp_type} in one line by going through `{iterable}`.",
        Level.BEGINNER: "Creates a {comp_type} from `{iterable}`{comprehension_filter}, in a single expression instead of a loop that appends.",
        Level.DEVELOPER: "{comp_type} comprehension over `{iterable}`{comprehension_filter}.",
    },
    Kind.SWITCH: {
        Level.ELI5: "Picks one path out of several, based on `{subject}`.",
        Level.BEGINNER: "Compares `{subject}` against {case_count} cases and runs the matching one.",
        Level.DEVELOPER: "Multi-way dispatch on `{subject}` across {case_count} arms.",
    },
    Kind.CASE: {
        Level.ELI5: "One of the choices — this runs if it matches.",
        Level.BEGINNER: "Handles the case where the value is `{pattern}`.",
        Level.DEVELOPER: "Arm for `{pattern}`.",
    },
    Kind.RETURN: {
        Level.ELI5: "Sends an answer back and stops here.",
        Level.BEGINNER: "Hands `{value}` back to whoever called this function and exits immediately.",
        Level.DEVELOPER: "Returns `{value}`; nothing after this line in the same block runs.",
    },
    Kind.YIELD: {
        Level.ELI5: "Hands over one value, then waits right here until asked for the next.",
        Level.BEGINNER: "Produces `{value}` and pauses. Execution resumes on the next request, with local state intact.",
        Level.DEVELOPER: "Suspension point yielding `{value}`; the frame is retained between resumptions.",
    },
    Kind.BREAK: {
        Level.ELI5: "Stops the loop right now.",
        Level.BEGINNER: "Exits the loop immediately, skipping any remaining items.",
        Level.DEVELOPER: "Unconditional loop exit.",
    },
    Kind.CONTINUE: {
        Level.ELI5: "Skips the rest of this go-round and starts the next one.",
        Level.BEGINNER: "Jumps straight to the next iteration without running the rest of the body.",
        Level.DEVELOPER: "Advances to the next iteration.",
    },
    Kind.TRY: {
        Level.ELI5: "Tries something risky, with a plan for when it goes wrong.",
        Level.BEGINNER: "Runs this block, and if it fails, control jumps to the handler instead of crashing.",
        Level.DEVELOPER: "Protected region with {handler_count} handler(s){finally_note}.",
    },
    Kind.CATCH: {
        Level.ELI5: "What to do when it goes wrong.",
        Level.BEGINNER: "Handles `{exception}` if the block above raises it.",
        Level.DEVELOPER: "Handler for `{exception}`.{catch_note}",
    },
    Kind.FINALLY: {
        Level.ELI5: "This always happens at the end, no matter what.",
        Level.BEGINNER: "Runs whether or not the block succeeded — used for cleanup.",
        Level.DEVELOPER: "Runs on every exit path, including exceptions and returns.",
    },
    Kind.THROW: {
        Level.ELI5: "Stops and shouts that something is wrong.",
        Level.BEGINNER: "Raises `{exception}`, which stops normal flow until something catches it.",
        Level.DEVELOPER: "Raises `{exception}`; unwinds to the nearest matching handler.",
    },
    Kind.WITH: {
        Level.ELI5: "Borrows something and always gives it back when finished.",
        Level.BEGINNER: "Sets up `{managers}` and guarantees it is cleaned up when the block ends, even on failure.",
        Level.DEVELOPER: "Scoped resource on `{managers}` — cleanup runs on every exit path.",
    },
    Kind.ASSIGN: {
        Level.ELI5: "Puts `{value}` into a box called `{name}`.",
        Level.BEGINNER: "Stores `{value}` in `{name}` so later lines can use it.",
        Level.DEVELOPER: "`{name}` <- `{value}`.{rebind_note}",
    },
    Kind.DECL: {
        Level.ELI5: "Makes a new box named `{name}` to keep something in.",
        Level.BEGINNER: "Declares `{name}`{decl_type} and sets it to `{value}`.",
        Level.DEVELOPER: "Declares `{name}`{decl_type}{const_note}.",
    },
    Kind.AUG_ASSIGN: {
        Level.ELI5: "Changes `{target}` by {op}-ing `{value}` onto what is already there.",
        Level.BEGINNER: "Updates `{target}` in place: takes its current value, applies `{op}` with `{value}`, stores it back.",
        Level.DEVELOPER: "In-place `{op}` on `{target}`.",
    },
    Kind.CALL: {
        Level.ELI5: "Uses `{callee}` to do a job.",
        Level.BEGINNER: "Calls `{callee}` with {arity} {arity_word}{args_note}.",
        Level.DEVELOPER: "`{callee}({args})`{cost_note}",
    },
    Kind.METHOD_CALL: {
        Level.ELI5: "Asks `{receiver}` to do `{callee}`.",
        Level.BEGINNER: "Calls `{callee}` on `{receiver}` with {arity} {arity_word}.",
        Level.DEVELOPER: "`{receiver}.{callee}({args})`{cost_note}",
    },
    Kind.NEW: {
        Level.ELI5: "Makes a brand new `{type}`.",
        Level.BEGINNER: "Creates a new `{type}` instance, passing {arity} {arity_word} to its constructor.",
        Level.DEVELOPER: "Allocates `{type}`.{allocation_note}",
    },
    Kind.DELETE: {
        Level.ELI5: "Gives back the space that was borrowed.",
        Level.BEGINNER: "Frees the memory held by `{target}`. Using it after this point is a bug.",
        Level.DEVELOPER: "Frees `{target}`. Every path out of the scope must reach exactly one delete.",
    },
    Kind.AWAIT: {
        Level.ELI5: "Waits politely for `{awaited}` to finish, letting other work happen meanwhile.",
        Level.BEGINNER: "Pauses here until `{awaited}` completes, freeing the thread to run other tasks in the meantime.",
        Level.DEVELOPER: "Suspension point on `{awaited}`; state is preserved across the await.",
    },
    Kind.IMPORT: {
        Level.ELI5: "Borrows some ready-made code from `{module}`.",
        Level.BEGINNER: "Brings in `{names}` from `{module}` so this file can use it.",
        Level.DEVELOPER: "Imports `{names}` from `{module}`.{stdlib_note}",
    },
    Kind.EXPORT: {
        Level.ELI5: "Shares this with other files.",
        Level.BEGINNER: "Makes `{value}` available to other modules that import this file.",
        Level.DEVELOPER: "Public export of `{value}`.",
    },
    Kind.DECORATOR: {
        Level.ELI5: "A sticker on `{target}` that gives it an extra power.",
        Level.BEGINNER: "Wraps `{target}` with `{name}`, which changes how it behaves without touching its body.",
        Level.DEVELOPER: "`{name}` applied to `{target}` at definition time.",
    },
    Kind.ANNOTATION: {
        Level.ELI5: "A label with extra information about this.",
        Level.BEGINNER: "`{name}` marks `{target}` with metadata the compiler or a framework reads.",
        Level.DEVELOPER: "Annotation `{name}` on `{target}`.",
    },
    Kind.NAMESPACE: {
        Level.ELI5: "Says which family this code belongs to.",
        Level.BEGINNER: "Groups this code under `{name}` so names do not clash with other files.",
        Level.DEVELOPER: "Namespace `{name}`.",
    },
    Kind.TERNARY: {
        Level.ELI5: "Picks `{when_true}` if the check passes, otherwise `{when_false}`.",
        Level.BEGINNER: "A one-line choice: evaluates to `{when_true}` when `{condition}` is true, and `{when_false}` when it is not.",
        Level.DEVELOPER: "Conditional expression on `{condition}`.",
    },
    Kind.COMPARE: {
        Level.ELI5: "Checks whether `{left}` and `{right}` line up.",
        Level.BEGINNER: "{op_name} `{left}` against `{right}` and produces true or false.",
        Level.DEVELOPER: "`{left} {op} {right}`.{identity_note}",
    },
    Kind.BOOLOP: {
        Level.ELI5: "Joins two checks together.",
        Level.BEGINNER: "Combines the conditions with `{op}` — it stops as soon as the answer is decided.",
        Level.DEVELOPER: "Short-circuiting `{op}` over {operand_count} operands.",
    },
    Kind.BINOP: {
        Level.ELI5: "Works out `{left}` {op} `{right}`.",
        Level.BEGINNER: "{op_name} `{left}` and `{right}`.",
        Level.DEVELOPER: "`{left} {op} {right}`.",
    },
    Kind.UNOP: {
        Level.ELI5: "Flips or changes `{operand}`.",
        Level.BEGINNER: "Applies `{op}` to `{operand}`.",
        Level.DEVELOPER: "Unary `{op}` on `{operand}`.",
    },
    Kind.INDEX: {
        Level.ELI5: "Reaches into `{container}` and grabs the item at `{key}`.",
        Level.BEGINNER: "Reads the element of `{container}` at position or key `{key}`.",
        Level.DEVELOPER: "`{container}[{key}]`.{index_note}",
    },
    Kind.SLICE: {
        Level.ELI5: "Takes a chunk out of `{container}`.",
        Level.BEGINNER: "Copies a section of `{container}` given by `{key}` into a new collection.",
        Level.DEVELOPER: "Slice `{container}[{key}]` — allocates a copy.",
    },
    Kind.ATTRIBUTE: {
        Level.ELI5: "Looks at the `{attribute}` part of `{object}`.",
        Level.BEGINNER: "Reads the `{attribute}` property of `{object}`.",
        Level.DEVELOPER: "Attribute access `{object}.{attribute}`.{pointer_note}",
    },
    Kind.COLLECTION: {
        Level.ELI5: "A container holding {size} {size_word}.",
        Level.BEGINNER: "Builds a {collection_type} with {size} {size_word}.",
        Level.DEVELOPER: "{collection_type} literal, {size} element(s).",
    },
    Kind.FSTRING: {
        Level.ELI5: "A sentence with values dropped into the gaps.",
        Level.BEGINNER: "Builds a string with {slot_count} value(s) slotted in, instead of gluing pieces together.",
        Level.DEVELOPER: "Interpolated literal with {slot_count} slot(s). Never build queries or shell commands this way.",
    },
    Kind.DESTRUCTURE: {
        Level.ELI5: "Unpacks a bundle into separate named pieces.",
        Level.BEGINNER: "Pulls `{names}` out of the value on the right in one statement.",
        Level.DEVELOPER: "Destructuring bind of `{names}`.",
    },
    Kind.SPREAD: {
        Level.ELI5: "Tips all the items out into this spot.",
        Level.BEGINNER: "Spreads the contents of `{value}` into place, item by item.",
        Level.DEVELOPER: "Spread of `{value}`.",
    },
    Kind.CAST: {
        Level.ELI5: "Treats `{value}` as a different kind of thing.",
        Level.BEGINNER: "Converts `{value}` to `{target_type}`.",
        Level.DEVELOPER: "Cast of `{value}` to `{target_type}`{cast_note}.",
    },
    Kind.LITERAL: {
        Level.ELI5: "A fixed value written straight into the code: `{value}`.",
        Level.BEGINNER: "The literal {literal_type} `{value}`.",
        Level.DEVELOPER: "{literal_type} literal `{value}`.{magic_note}",
    },
    Kind.COMMENT: {
        Level.ELI5: "A note from the author. The computer ignores it.",
        Level.BEGINNER: "A comment — documentation for humans, not executed.",
        Level.DEVELOPER: "Comment.",
    },
    # -- SQL -----------------------------------------------------------------
    Kind.SELECT: {
        Level.ELI5: "Asks the database for {projection_count} piece(s) of information.",
        Level.BEGINNER: "Reads {projections} from {tables}{select_filters}.",
        Level.DEVELOPER: "Projection of {projection_count} column(s) over {table_count} relation(s){select_shape}.",
    },
    Kind.PROJECTION: {
        Level.ELI5: "One of the things being asked for.",
        Level.BEGINNER: "Returns `{expression}`{alias_note} as a column.",
        Level.DEVELOPER: "`{expression}`{alias_note}.",
    },
    Kind.FROM: {
        Level.ELI5: "Says which table to look in.",
        Level.BEGINNER: "Reads rows from {tables}.",
        Level.DEVELOPER: "Source relation: {tables}.",
    },
    Kind.JOIN: {
        Level.ELI5: "Sticks another table on, matching rows that belong together.",
        Level.BEGINNER: "Attaches `{table}` where `{on}` matches — {note}.",
        Level.DEVELOPER: "{name} on `{on}`. {note}.",
    },
    Kind.WHERE: {
        Level.ELI5: "Throws away the rows that do not fit.",
        Level.BEGINNER: "Keeps only rows where `{condition}` is true.",
        Level.DEVELOPER: "Filter `{condition}`.{sargable_note}",
    },
    Kind.GROUP_BY: {
        Level.ELI5: "Puts rows into piles that share the same {keys}.",
        Level.BEGINNER: "Collapses rows into one row per distinct {keys}, so the aggregates apply per group.",
        Level.DEVELOPER: "Grouping set: {keys}.",
    },
    Kind.HAVING: {
        Level.ELI5: "Throws away whole piles that do not fit.",
        Level.BEGINNER: "Filters the grouped rows by `{condition}` — this runs after grouping, unlike WHERE.",
        Level.DEVELOPER: "Post-aggregation filter `{condition}`.",
    },
    Kind.ORDER_BY: {
        Level.ELI5: "Puts the answers in order.",
        Level.BEGINNER: "Sorts the result by {keys}.",
        Level.DEVELOPER: "Sort on {keys} — O(n log n) unless an index already provides the order.",
    },
    Kind.LIMIT: {
        Level.ELI5: "Only keeps the first {count}.",
        Level.BEGINNER: "Returns at most {count} rows.",
        Level.DEVELOPER: "Caps the result at {count} rows.",
    },
    Kind.CTE: {
        Level.ELI5: "Names a smaller question so the big one can use its answer.",
        Level.BEGINNER: "Defines `{name}` as a named intermediate result the main query can read from.",
        Level.DEVELOPER: "CTE `{name}`.{cte_note}",
    },
    Kind.WINDOW: {
        Level.ELI5: "Works out a number for each row while still seeing its neighbours.",
        Level.BEGINNER: "Runs `{function}` across related rows{partition_note}, without collapsing them into one.",
        Level.DEVELOPER: "Window `{function}`{partition_note} — row count preserved.",
    },
    Kind.SUBQUERY: {
        Level.ELI5: "A question inside the question.",
        Level.BEGINNER: "A nested query whose result is used by the query around it.",
        Level.DEVELOPER: "Subquery `{alias}`.",
    },
    Kind.AGGREGATE: {
        Level.ELI5: "Squashes many rows into one number.",
        Level.BEGINNER: "`{callee}` combines all the rows in each group into a single value.",
        Level.DEVELOPER: "Aggregate `{callee}({args})`{distinct_note}.",
    },
    Kind.SET_OP: {
        Level.ELI5: "Stacks the results of two questions together.",
        Level.BEGINNER: "Combines the rows of both queries{dedup_note}.",
        Level.DEVELOPER: "{operation} of two result sets{dedup_note}.",
    },
    Kind.INSERT: {
        Level.ELI5: "Adds new rows to {table}.",
        Level.BEGINNER: "Writes new rows into `{table}`.",
        Level.DEVELOPER: "Insert into `{table}`.",
    },
    Kind.UPDATE: {
        Level.ELI5: "Changes rows that are already in {table}.",
        Level.BEGINNER: "Modifies {assignment_count} column(s) on rows of `{table}`{where_note}.",
        Level.DEVELOPER: "Update `{table}` setting {assignments}{where_note}.",
    },
    Kind.DELETE_ROWS: {
        Level.ELI5: "Removes rows from {table}.",
        Level.BEGINNER: "Deletes rows from `{table}`{where_note}.",
        Level.DEVELOPER: "Delete from `{table}`{where_note}.",
    },
    Kind.CREATE: {
        Level.ELI5: "Makes a new place to store data.",
        Level.BEGINNER: "Creates the {object_kind} `{name}`.",
        Level.DEVELOPER: "DDL: create {object_kind} `{name}`.",
    },
}


def _callable_notes(node: Node) -> str:
    notes = []
    if node.meta.get("is_async"):
        notes.append("async — returns a promise/coroutine, not the value itself")
    if node.meta.get("is_generator"):
        notes.append("generator — produces values lazily")
    if node.meta.get("is_static"):
        notes.append("static — no instance state")
    if node.meta.get("is_abstract"):
        notes.append("abstract — subclasses supply the body")
    if node.meta.get("is_const"):
        notes.append("const — does not mutate the receiver")
    if node.meta.get("throws"):
        notes.append(f"declares throws {node.meta['throws']}")
    return (" " + "; ".join(notes).capitalize() + ".") if notes else ""


def _derived_slots(node: Node, level: Level) -> dict[str, str]:
    """Conditional fragments that would be unreadable inline in a template."""
    meta = node.meta
    out: dict[str, str] = {}

    out["else_note"] = ", otherwise the else block runs" if meta.get("has_else") else ""
    out["guard_note"] = (
        " Guard clause — it leaves early so the rest of the function reads unindented."
        if meta.get("is_guard")
        else ""
    )
    out["finally_note"] = " and a finally block" if meta.get("has_finally") else ""
    out["catch_note"] = (
        " Catches everything, including errors this code cannot handle."
        if meta.get("is_bare")
        else ""
    )
    out["termination_note"] = (
        " No break in the body — this only ends when the condition changes."
        if meta.get("is_infinite") and not meta.get("has_break")
        else ""
    )
    out["comprehension_filter"] = (
        f", keeping only items where `{meta['condition']}`" if meta.get("has_condition") else ""
    )
    arity = int(meta.get("arity", 0) or 0)
    out["arity_word"] = _plural(arity, "argument")
    args = meta.get("args") or []
    out["args_note"] = f" ({', '.join(str(a) for a in args[:3])})" if args and arity <= 3 else ""
    cost = meta.get("cost")
    out["cost_note"] = f" — costs about O({cost})." if cost else ""
    out["allocation_note"] = (
        " Heap-allocated; something must free it." if meta.get("is_array") is not None else ""
    )
    out["stdlib_note"] = " Standard library." if meta.get("is_stdlib") else ""
    out["rebind_note"] = (
        f" Result of `{meta['from_call']}()`." if meta.get("from_call") else ""
    )
    annotation = meta.get("annotation")
    out["decl_type"] = f" as a {annotation}" if annotation else ""
    out["const_note"] = " (constant — cannot be reassigned)" if meta.get("is_const") else ""
    out["identity_note"] = (
        " Identity comparison, not equality — true only for the same object."
        if meta.get("is_identity")
        else ""
    )
    out["index_note"] = " Negative index counts from the end." if meta.get("negative") else ""
    out["pointer_note"] = " Dereferences a pointer." if meta.get("via_pointer") else ""
    out["magic_note"] = (
        " Unexplained constant — a named value would document the intent."
        if meta.get("is_magic_number")
        else ""
    )
    out["cast_note"] = (
        " (C-style cast — unchecked)" if meta.get("style") == "c-style" else ""
    )
    size = int(meta.get("size", 0) or 0)
    out["size_word"] = _plural(size, "item")

    # SQL fragments
    filters = []
    if meta.get("has_where"):
        filters.append("with a filter")
    if meta.get("has_group"):
        filters.append("grouped")
    if meta.get("has_order"):
        filters.append("sorted")
    out["select_filters"] = (", " + " and ".join(filters)) if filters else ""
    shape = []
    if meta.get("join_count"):
        shape.append(f"{meta['join_count']} join(s)")
    if meta.get("aggregates"):
        shape.append("aggregation")
    out["select_shape"] = (", " + ", ".join(shape)) if shape else ""
    out["alias_note"] = f" as `{meta['alias']}`" if meta.get("alias") else ""
    out["sargable_note"] = (
        " Wrapping the column in a function usually stops an index being used."
        if meta.get("is_sargable") is False
        else ""
    )
    out["partition_note"] = (
        f", partitioned by {meta['partition_by']}" if meta.get("partition_by") else ""
    )
    out["dedup_note"] = " and removes duplicates" if meta.get("deduplicates") else ""
    out["distinct_note"] = " over distinct values" if meta.get("is_distinct") else ""
    out["where_note"] = (
        "" if meta.get("has_where") else " — with no WHERE clause, this hits every row"
    )
    out["cte_note"] = " Recursive." if meta.get("is_recursive") else ""
    return out


def phrase(node: Node, level: Level) -> str | None:
    """One sentence explaining `node` at `level`, or None when it needs no words."""
    templates = TEMPLATES.get(node.kind)
    if not templates:
        return None
    template = templates.get(level)
    if template is None:
        return None
    if callable(template):
        try:
            return template(node)
        except Exception:  # pragma: no cover - a template bug must not break a request
            return None
    slots = _slots(node)
    slots.update(_derived_slots(node, level))
    try:
        return template.format(**slots)
    except (KeyError, IndexError, ValueError):
        return None


def explains(kind: Kind) -> bool:
    return kind in TEMPLATES
