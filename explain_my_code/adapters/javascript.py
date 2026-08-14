"""JavaScript / JSX -> IR."""

from __future__ import annotations

from typing import Any

from explain_my_code.adapters.base import register
from explain_my_code.adapters.treesitter import (
    TreeSitterAdapter,
    _field,
    _field_text,
    _span,
    _text,
)
from explain_my_code.ir import Kind, Language

BUILTINS = frozenset(
    {
        "log", "warn", "error", "parseInt", "parseFloat", "fetch", "map", "filter",
        "reduce", "forEach", "push", "pop", "shift", "unshift", "slice", "splice",
        "join", "split", "includes", "indexOf", "find", "findIndex", "some", "every",
        "sort", "reverse", "concat", "keys", "values", "entries", "stringify", "parse",
        "setTimeout", "setInterval", "addEventListener", "querySelector", "then", "catch",
    }
)

KNOWN_COSTS = {
    "sort": "n log n", "map": "n", "filter": "n", "reduce": "n", "forEach": "n",
    "find": "n", "findIndex": "n", "some": "n", "every": "n", "includes": "n",
    "indexOf": "n", "join": "n", "reverse": "n", "concat": "n", "slice": "n",
}


class JavaScriptAdapter(TreeSitterAdapter):
    language = Language.JAVASCRIPT
    parser_name = "tree-sitter-javascript"
    BUILTINS = BUILTINS
    KNOWN_COSTS = KNOWN_COSTS

    KINDS = {
        "class_declaration": Kind.CLASS,
        "class": Kind.CLASS,
        "method_definition": Kind.METHOD,
        "field_definition": Kind.DECL,
        "function_declaration": Kind.FUNCTION,
        "function_expression": Kind.FUNCTION,
        "function": Kind.FUNCTION,
        "generator_function_declaration": Kind.FUNCTION,
        "generator_function": Kind.FUNCTION,
        "arrow_function": Kind.LAMBDA,
        "if_statement": Kind.BRANCH,
        "else_clause": Kind.ELSE,
        "for_statement": Kind.LOOP_FOR,
        "for_in_statement": Kind.LOOP_FOREACH,
        "while_statement": Kind.LOOP_WHILE,
        "do_statement": Kind.LOOP_DO,
        "switch_statement": Kind.SWITCH,
        "switch_case": Kind.CASE,
        "switch_default": Kind.CASE,
        "break_statement": Kind.BREAK,
        "continue_statement": Kind.CONTINUE,
        "return_statement": Kind.RETURN,
        "throw_statement": Kind.THROW,
        "try_statement": Kind.TRY,
        "catch_clause": Kind.CATCH,
        "finally_clause": Kind.FINALLY,
        "variable_declarator": Kind.DECL,
        "assignment_expression": Kind.ASSIGN,
        "augmented_assignment_expression": Kind.AUG_ASSIGN,
        "update_expression": Kind.AUG_ASSIGN,
        "call_expression": Kind.CALL,
        "new_expression": Kind.NEW,
        "member_expression": Kind.ATTRIBUTE,
        "subscript_expression": Kind.INDEX,
        "array": Kind.COLLECTION,
        "object": Kind.COLLECTION,
        "object_pattern": Kind.DESTRUCTURE,
        "array_pattern": Kind.DESTRUCTURE,
        "template_string": Kind.FSTRING,
        "await_expression": Kind.AWAIT,
        "yield_expression": Kind.YIELD,
        "spread_element": Kind.SPREAD,
        "rest_pattern": Kind.SPREAD,
        "ternary_expression": Kind.TERNARY,
        "import_statement": Kind.IMPORT,
        "export_statement": Kind.EXPORT,
        "binary_expression": Kind.BINOP,
        "unary_expression": Kind.UNOP,
        "identifier": Kind.NAME,
        "labeled_statement": Kind.BLOCK,
    }

    LITERAL_TYPES = frozenset(
        {"number", "string", "true", "false", "null", "undefined", "regex"}
    )
    LEAVES = frozenset({"template_string", "object_pattern", "array_pattern", "identifier"})
    OPAQUE = frozenset(
        {
            "property_identifier", "private_property_identifier", "statement_identifier",
            "shorthand_property_identifier_pattern", "shorthand_property_identifier",
            "string_fragment", "import_clause", "named_imports", "import_specifier",
            "formal_parameters", "type_annotation", "type_identifier", "comment_block",
        }
    )
    COMMENT_TYPES = frozenset({"comment"})

    def _grammar(self) -> Any:
        import tree_sitter_javascript

        return tree_sitter_javascript.language()

    # -- kind refinement ------------------------------------------------------

    def kind_for(self, ts_node):  # type: ignore[override]
        node_type = ts_node.type
        if node_type == "call_expression":
            func = _field(ts_node, "function")
            if func is not None and func.type in {"member_expression", "subscript_expression"}:
                return Kind.METHOD_CALL
            return Kind.CALL
        if node_type == "method_definition":
            name = _field_text(ts_node, "name", 32)
            if name == "constructor":
                return Kind.CONSTRUCTOR
            return Kind.METHOD
        return super().kind_for(ts_node)

    def name_for(self, ts_node, kind):  # type: ignore[override]
        if kind is Kind.LAMBDA:
            parent = ts_node.parent
            if parent is not None and parent.type == "variable_declarator":
                return _field_text(parent, "name", 32) or "arrow function"
            return "arrow function"
        if kind is Kind.IMPORT:
            return _field_text(ts_node, "source", 48).strip("\"'`")
        return super().name_for(ts_node, kind)

    def recurse_into(self, ts_node, kind):  # type: ignore[override]
        children = super().recurse_into(ts_node, kind)
        if kind in {Kind.FUNCTION, Kind.METHOD, Kind.CONSTRUCTOR, Kind.LAMBDA}:
            params = _field(ts_node, "parameters")
            children = [c for c in children if c is not params]
        return children

    def synth_children(self, ts_node, kind):  # type: ignore[override]
        if kind not in {Kind.FUNCTION, Kind.METHOD, Kind.CONSTRUCTOR, Kind.LAMBDA}:
            return []
        owner = _field_text(ts_node, "name", 32) or "function"
        return self._param_nodes(ts_node, owner, _js_params(ts_node))

    # -- meta -----------------------------------------------------------------

    def _callable_meta(self, ts_node) -> dict[str, Any]:
        params = _js_params(ts_node)
        source = _text(ts_node, 4096)
        return {
            "params": params,
            "param_count": len(params),
            "param_names": [p["name"] for p in params],
            "is_async": "async" in _leading_tokens(ts_node),
            "is_generator": ts_node.type.startswith("generator") or "*" in _leading_tokens(ts_node),
            "is_static": "static" in _leading_tokens(ts_node),
            "returns": "",
            "decorators": [],
            "docstring": "",
            "full_span": _span(ts_node).to_dict(),
            "body_lines": _span(ts_node).line_count,
            "is_dunder": False,
            "is_private": _field_text(ts_node, "name", 32).startswith("#"),
            "has_await": "await " in source,
        }

    meta_function = _callable_meta
    meta_method = _callable_meta
    meta_constructor = _callable_meta

    def meta_lambda(self, ts_node) -> dict[str, Any]:
        meta = self._callable_meta(ts_node)
        body = _field(ts_node, "body")
        meta["body"] = _text(body, 48)
        meta["is_expression_body"] = body is not None and body.type != "statement_block"
        return meta

    def meta_class(self, ts_node) -> dict[str, Any]:
        body = _field(ts_node, "body")
        methods = (
            [_field_text(c, "name", 32) for c in body.named_children if c.type == "method_definition"]
            if body is not None
            else []
        )
        heritage = [c for c in ts_node.named_children if c.type == "class_heritage"]
        bases = [_text(h, 32).removeprefix("extends ").strip() for h in heritage]
        return {
            "bases": bases,
            "is_subclass": bool(bases),
            "method_names": methods,
            "method_count": len(methods),
            "decorators": [],
            "docstring": "",
            "full_span": _span(ts_node).to_dict(),
        }

    def meta_loop_foreach(self, ts_node) -> dict[str, Any]:
        operator = _field_text(ts_node, "operator", 4)
        return {
            "target": _field_text(ts_node, "left", 32),
            "iterable": _field_text(ts_node, "right", 40),
            "over_keys": operator == "in",
            "counted": False,
            "declaration_kind": _field_text(ts_node, "kind", 8),
        }

    def meta_decl(self, ts_node) -> dict[str, Any]:
        parent = ts_node.parent
        declaration_kind = _field_text(parent, "kind", 8) if parent is not None else ""
        value = _field(ts_node, "value")
        name_node = _field(ts_node, "name")
        return {
            "name": _text(name_node, 32),
            "value": _text(value, 48),
            "has_value": value is not None,
            "declaration_kind": declaration_kind,
            "is_const": declaration_kind == "const",
            "destructures": name_node is not None
            and name_node.type in {"object_pattern", "array_pattern"},
            "from_call": _field_text(value, "function", 32) if value is not None else "",
            "annotation": "",
            "targets": [_text(name_node, 32)],
        }

    def meta_import(self, ts_node) -> dict[str, Any]:
        clause = next((c for c in ts_node.named_children if c.type == "import_clause"), None)
        names = []
        if clause is not None:
            names = [_text(c, 24) for c in clause.named_children]
        module = _field_text(ts_node, "source", 48).strip("\"'`")
        return {
            "module": module,
            "names": names,
            "is_from": True,
            "is_relative": module.startswith("."),
            "is_stdlib": False,
        }

    def meta_export(self, ts_node) -> dict[str, Any]:
        return {
            "value": _field_text(ts_node, "value", 40),
            "is_default": "default" in _leading_tokens(ts_node),
        }

    def meta_fstring(self, ts_node) -> dict[str, Any]:
        slots = [c for c in ts_node.named_children if c.type == "template_substitution"]
        return {"slot_count": len(slots), "slots": [_text(s, 24).strip("${}") for s in slots]}

    def meta_aug_assign(self, ts_node) -> dict[str, Any]:
        if ts_node.type == "update_expression":
            op = _field_text(ts_node, "operator", 4)
            target = _field_text(ts_node, "argument", 32)
            return {
                "target": target, "targets": [target], "op": op[0] if op else "+",
                "value": "1", "is_accumulator": True, "is_increment": op == "++",
            }
        return {
            "op": _field_text(ts_node, "operator", 4).rstrip("="),
            "is_accumulator": _field_text(ts_node, "operator", 4) in {"+=", "-="},
        }

    def meta_destructure(self, ts_node) -> dict[str, Any]:
        return {
            "names": [_text(c, 24) for c in ts_node.named_children],
            "shape": "object" if ts_node.type == "object_pattern" else "array",
        }

    def meta_case(self, ts_node) -> dict[str, Any]:
        return {
            "pattern": _field_text(ts_node, "value", 32),
            "is_default": ts_node.type == "switch_default",
            "has_guard": False,
        }

    def meta_yield(self, ts_node) -> dict[str, Any]:
        children = ts_node.named_children
        return {
            "value": _text(children[0], 40) if children else "",
            "delegated": "*" in _leading_tokens(ts_node),
        }

    def meta_await(self, ts_node) -> dict[str, Any]:
        children = ts_node.named_children
        return {"awaited": _text(children[0], 40) if children else ""}

    def meta_spread(self, ts_node) -> dict[str, Any]:
        children = ts_node.named_children
        return {"value": _text(children[0], 32) if children else ""}


def _leading_tokens(ts_node) -> set[str]:
    """Anonymous keyword tokens before the first named child (`async`, `static`, `*`)."""
    out: set[str] = set()
    for child in ts_node.children:
        if child.is_named:
            break
        text = child.text
        if text:
            out.add(text.decode("utf-8", "replace"))
    return out


def _js_params(ts_node) -> list[dict[str, Any]]:
    holder = _field(ts_node, "parameters")
    if holder is None:
        # `x => x * 2` has a bare identifier where the parameter list would be.
        single = _field(ts_node, "parameter")
        if single is not None:
            return [{"name": _text(single, 24), "annotation": "", "default": "", "variadic": None}]
        return []
    out: list[dict[str, Any]] = []
    for child in holder.named_children:
        if child.type == "assignment_pattern":
            out.append(
                {
                    "name": _field_text(child, "left", 24),
                    "annotation": "",
                    "default": _field_text(child, "right", 24),
                    "variadic": None,
                }
            )
        elif child.type == "rest_pattern":
            out.append(
                {"name": _text(child, 24).lstrip("."), "annotation": "", "default": "",
                 "variadic": "args"}
            )
        elif child.type in {"object_pattern", "array_pattern"}:
            out.append(
                {"name": _text(child, 32), "annotation": "", "default": "",
                 "variadic": None, "destructured": True}
            )
        else:
            out.append(
                {"name": _text(child, 24), "annotation": "", "default": "", "variadic": None}
            )
    return out


@register(Language.JAVASCRIPT)
def _factory() -> JavaScriptAdapter:
    return JavaScriptAdapter()
