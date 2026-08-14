"""Java -> IR."""

from __future__ import annotations

from typing import Any

from explain_my_code.adapters.base import register
from explain_my_code.adapters.treesitter import (
    TreeSitterAdapter,
    _children_of_type,
    _field,
    _field_text,
    _span,
    _text,
)
from explain_my_code.ir import Kind, Language

BUILTINS = frozenset(
    {
        "println", "print", "printf", "format", "valueOf", "toString", "equals",
        "hashCode", "length", "size", "get", "put", "add", "remove", "contains",
        "containsKey", "isEmpty", "stream", "collect", "forEach", "map", "filter",
        "sort", "asList", "of", "parseInt", "parseDouble", "charAt", "substring",
        "split", "trim", "join", "compareTo", "getOrDefault", "keySet", "values",
    }
)

KNOWN_COSTS = {
    "sort": "n log n", "contains": "n", "indexOf": "n", "remove": "n",
    "stream": "n", "collect": "n", "forEach": "n", "map": "n", "filter": "n",
    "toArray": "n", "addAll": "n", "asList": "n",
}

VISIBILITY = ("public", "private", "protected")


class JavaAdapter(TreeSitterAdapter):
    language = Language.JAVA
    parser_name = "tree-sitter-java"
    BUILTINS = BUILTINS
    KNOWN_COSTS = KNOWN_COSTS

    KINDS = {
        "class_declaration": Kind.CLASS,
        "interface_declaration": Kind.INTERFACE,
        "enum_declaration": Kind.CLASS,
        "record_declaration": Kind.CLASS,
        "method_declaration": Kind.METHOD,
        "constructor_declaration": Kind.CONSTRUCTOR,
        "formal_parameter": Kind.PARAM,
        "spread_parameter": Kind.PARAM,
        "if_statement": Kind.BRANCH,
        "for_statement": Kind.LOOP_FOR,
        "enhanced_for_statement": Kind.LOOP_FOREACH,
        "while_statement": Kind.LOOP_WHILE,
        "do_statement": Kind.LOOP_DO,
        "switch_expression": Kind.SWITCH,
        "switch_block_statement_group": Kind.CASE,
        "switch_rule": Kind.CASE,
        "break_statement": Kind.BREAK,
        "continue_statement": Kind.CONTINUE,
        "return_statement": Kind.RETURN,
        "throw_statement": Kind.THROW,
        "try_statement": Kind.TRY,
        "try_with_resources_statement": Kind.TRY,
        "catch_clause": Kind.CATCH,
        "finally_clause": Kind.FINALLY,
        "local_variable_declaration": Kind.DECL,
        "field_declaration": Kind.DECL,
        "assignment_expression": Kind.ASSIGN,
        "update_expression": Kind.AUG_ASSIGN,
        "method_invocation": Kind.METHOD_CALL,
        "object_creation_expression": Kind.NEW,
        "field_access": Kind.ATTRIBUTE,
        "array_access": Kind.INDEX,
        "array_initializer": Kind.COLLECTION,
        "lambda_expression": Kind.LAMBDA,
        "cast_expression": Kind.CAST,
        "instanceof_expression": Kind.COMPARE,
        "ternary_expression": Kind.TERNARY,
        "import_declaration": Kind.IMPORT,
        "package_declaration": Kind.NAMESPACE,
        "marker_annotation": Kind.ANNOTATION,
        "annotation": Kind.ANNOTATION,
        "binary_expression": Kind.BINOP,
        "unary_expression": Kind.UNOP,
        "identifier": Kind.NAME,
        "synchronized_statement": Kind.WITH,
    }

    LITERAL_TYPES = frozenset(
        {
            "decimal_integer_literal", "hex_integer_literal", "octal_integer_literal",
            "binary_integer_literal", "decimal_floating_point_literal",
            "hex_floating_point_literal", "string_literal", "character_literal",
            "true", "false", "null_literal", "text_block",
        }
    )
    LEAVES = frozenset({"identifier", "formal_parameter", "spread_parameter"})
    OPAQUE = frozenset(
        {
            "modifiers", "type_identifier", "integral_type", "floating_point_type",
            "void_type", "boolean_type", "generic_type", "type_arguments", "dimensions",
            "array_type", "type_parameters", "type_parameter", "type_bound",
            "super_interfaces", "type_list", "superclass", "asterisk", "scoped_identifier",
            "scoped_type_identifier", "wildcard", "throws", "catch_type", "string_fragment",
            "annotation_argument_list", "element_value_pair",
            "type_annotation", "switch_label", "dimensions_expr", "extends_interfaces",
        }
    )
    COMMENT_TYPES = frozenset({"line_comment", "block_comment", "comment"})

    def _grammar(self) -> Any:
        import tree_sitter_java

        return tree_sitter_java.language()

    # -- overrides ------------------------------------------------------------

    def name_for(self, ts_node, kind):  # type: ignore[override]
        if kind is Kind.IMPORT:
            return _text(ts_node, 64).removeprefix("import ").removeprefix("static ").rstrip(";")
        if kind is Kind.NAMESPACE:
            return _text(ts_node, 48).removeprefix("package ").rstrip(";")
        if kind is Kind.LAMBDA:
            return "lambda"
        if kind is Kind.DECL:
            declarator = _field(ts_node, "declarator")
            if declarator is not None:
                return _field_text(declarator, "name", 32)
        if kind is Kind.ANNOTATION:
            return "@" + _field_text(ts_node, "name", 32)
        return super().name_for(ts_node, kind)

    def synth_children(self, ts_node, kind):  # type: ignore[override]
        return []

    def recurse_into(self, ts_node, kind):  # type: ignore[override]
        if kind is Kind.DECL:
            # Descend only into initializer expressions; the declared name is already
            # this node's `name`, and its type is grammar noise.
            return [
                value
                for declarator in _children_of_type(ts_node, "variable_declarator")
                if (value := _field(declarator, "value")) is not None
            ]
        return super().recurse_into(ts_node, kind)

    def _catch_type(self, ts_node) -> str:  # type: ignore[override]
        param = next(
            (c for c in ts_node.named_children if c.type == "catch_formal_parameter"), None
        )
        if param is None:
            return ""
        catch_type = next((c for c in param.named_children if c.type == "catch_type"), None)
        return _text(catch_type, 40)

    def _meta_call(self, ts_node) -> dict[str, Any]:  # type: ignore[override]
        """Java puts the receiver in `object` and the name in `name` — no `function` field."""
        args = _field(ts_node, "arguments")
        arg_nodes = list(args.named_children) if args is not None else []
        callee = _field_text(ts_node, "name", 32)
        receiver = _field_text(ts_node, "object", 32)
        return {
            "callee": callee,
            "receiver": receiver,
            "arity": len(arg_nodes),
            "args": [_text(a, 24) for a in arg_nodes],
            "is_builtin": callee in self.BUILTINS,
            "cost": self.KNOWN_COSTS.get(callee, ""),
            "qualified": f"{receiver}.{callee}" if receiver else callee,
        }

    # -- meta ------------------------------------------------------------------

    def _callable_meta(self, ts_node) -> dict[str, Any]:
        params = _java_params(ts_node)
        modifiers = _modifiers(ts_node)
        annotations = [m for m in modifiers if m.startswith("@")]
        body = _field(ts_node, "body")
        return {
            "params": params,
            "param_count": len(params),
            "param_names": [p["name"] for p in params],
            "is_async": False,
            "is_generator": False,
            "is_static": "static" in modifiers,
            "is_abstract": "abstract" in modifiers or body is None,
            "is_final": "final" in modifiers,
            "visibility": next((m for m in modifiers if m in VISIBILITY), "package-private"),
            "returns": _field_text(ts_node, "type", 32),
            "decorators": annotations,
            "throws": _text(
                next((c for c in ts_node.named_children if c.type == "throws"), None), 48
            ).removeprefix("throws "),
            "docstring": "",
            "full_span": _span(ts_node).to_dict(),
            "body_lines": _span(ts_node).line_count,
            "is_dunder": False,
            "is_private": "private" in modifiers,
            "is_override": "@Override" in annotations,
        }

    meta_method = _callable_meta
    meta_constructor = _callable_meta

    def meta_lambda(self, ts_node) -> dict[str, Any]:
        params = _java_params(ts_node)
        body = _field(ts_node, "body")
        return {
            "params": params,
            "param_count": len(params),
            "param_names": [p["name"] for p in params],
            "body": _text(body, 48),
            "is_expression_body": body is not None and body.type != "block",
        }

    def _type_meta(self, ts_node) -> dict[str, Any]:
        body = _field(ts_node, "body")
        methods = (
            [
                _field_text(c, "name", 32)
                for c in body.named_children
                if c.type in {"method_declaration", "constructor_declaration"}
            ]
            if body is not None
            else []
        )
        modifiers = _modifiers(ts_node)
        superclass = _text(
            next((c for c in ts_node.named_children if c.type == "superclass"), None), 32
        ).removeprefix("extends ")
        interfaces = _text(
            next((c for c in ts_node.named_children if c.type == "super_interfaces"), None), 48
        ).removeprefix("implements ")
        bases = [b for b in [superclass] if b]
        return {
            "bases": bases,
            "is_subclass": bool(superclass),
            "interfaces": [i.strip() for i in interfaces.split(",") if i.strip()],
            "method_names": methods,
            "method_count": len(methods),
            "decorators": [m for m in modifiers if m.startswith("@")],
            "visibility": next((m for m in modifiers if m in VISIBILITY), "package-private"),
            "is_abstract": "abstract" in modifiers,
            "is_final": "final" in modifiers,
            "is_generic": bool(_field(ts_node, "type_parameters")),
            "type_params": _field_text(ts_node, "type_parameters", 32),
            "docstring": "",
            "full_span": _span(ts_node).to_dict(),
        }

    meta_class = _type_meta
    meta_interface = _type_meta

    def meta_param(self, ts_node) -> dict[str, Any]:
        return {
            "name": _field_text(ts_node, "name", 24)
            or _text(_field(_field(ts_node, "declarator") or ts_node, "name"), 24),
            "annotation": _field_text(ts_node, "type", 32),
            "default": "",
            "variadic": "args" if ts_node.type == "spread_parameter" else None,
        }

    def meta_decl(self, ts_node) -> dict[str, Any]:
        declarators = _children_of_type(ts_node, "variable_declarator")
        first = declarators[0] if declarators else None
        value = _field(first, "value") if first is not None else None
        modifiers = _modifiers(ts_node)
        name = _field_text(first, "name", 32) if first is not None else ""
        return {
            "name": name,
            "targets": [name],
            "annotation": _field_text(ts_node, "type", 32),
            "value": _text(value, 48),
            "has_value": value is not None,
            "is_const": "final" in modifiers,
            "is_static": "static" in modifiers,
            "is_field": ts_node.type == "field_declaration",
            "visibility": next((m for m in modifiers if m in VISIBILITY), ""),
            "from_call": _field_text(value, "name", 32)
            if value is not None and value.type == "method_invocation"
            else "",
            "declares": len(declarators),
        }

    def meta_loop_foreach(self, ts_node) -> dict[str, Any]:
        return {
            "target": _field_text(ts_node, "name", 32),
            "iterable": _field_text(ts_node, "value", 40),
            "element_type": _field_text(ts_node, "type", 24),
            "counted": False,
        }

    def meta_import(self, ts_node) -> dict[str, Any]:
        path = _text(ts_node, 80).removeprefix("import ").rstrip(";")
        is_static = path.startswith("static ")
        path = path.removeprefix("static ")
        return {
            "module": path.rsplit(".", 1)[0] if "." in path else path,
            "names": [path.rsplit(".", 1)[-1]],
            "is_from": True,
            "is_static": is_static,
            "is_wildcard": path.endswith("*"),
            "is_stdlib": path.startswith("java.") or path.startswith("javax."),
        }

    def meta_namespace(self, ts_node) -> dict[str, Any]:
        return {"name": _text(ts_node, 48).removeprefix("package ").rstrip(";"), "is_package": True}

    def meta_annotation(self, ts_node) -> dict[str, Any]:
        name = _field_text(ts_node, "name", 32)
        parent = ts_node.parent
        target = ""
        if parent is not None and parent.type == "modifiers" and parent.parent is not None:
            target = _field_text(parent.parent, "name", 32)
        return {
            "name": "@" + name,
            "target": target,
            "target_kind": parent.parent.type if parent is not None and parent.parent else "",
            "args": _field_text(ts_node, "arguments", 32),
        }

    def meta_cast(self, ts_node) -> dict[str, Any]:
        return {
            "target_type": _field_text(ts_node, "type", 24),
            "value": _field_text(ts_node, "value", 32),
        }

    def meta_case(self, ts_node) -> dict[str, Any]:
        label = next((c for c in ts_node.named_children if c.type == "switch_label"), None)
        text = _text(label, 32)
        return {
            "pattern": text.removeprefix("case ").rstrip(":"),
            "is_default": text.startswith("default"),
            "has_guard": False,
        }

    def meta_aug_assign(self, ts_node) -> dict[str, Any]:
        op = _field_text(ts_node, "operator", 4)
        target = _field_text(ts_node, "operand", 32) or _text(
            ts_node.named_children[0] if ts_node.named_children else None, 32
        )
        return {
            "target": target, "targets": [target], "op": op[0] if op else "+",
            "value": "1", "is_accumulator": True, "is_increment": op == "++",
        }

    def meta_with(self, ts_node) -> dict[str, Any]:
        return {
            "managers": [_text(ts_node.named_children[0], 32) if ts_node.named_children else ""],
            "is_lock": True,
            "is_async": False,
            "binds": [],
        }


def _modifiers(ts_node) -> list[str]:
    node = next((c for c in ts_node.named_children if c.type == "modifiers"), None)
    if node is None:
        return []
    out: list[str] = []
    for child in node.children:
        text = _text(child, 32)
        if text:
            out.append(text)
    return out


def _java_params(ts_node) -> list[dict[str, Any]]:
    holder = _field(ts_node, "parameters")
    if holder is None:
        return []
    out: list[dict[str, Any]] = []
    for child in holder.named_children:
        if child.type == "formal_parameter":
            out.append(
                {
                    "name": _field_text(child, "name", 24),
                    "annotation": _field_text(child, "type", 32),
                    "default": "",
                    "variadic": None,
                }
            )
        elif child.type == "spread_parameter":
            declarator = next(
                (c for c in child.named_children if c.type == "variable_declarator"), None
            )
            out.append(
                {
                    "name": _field_text(declarator, "name", 24) if declarator else _text(child, 24),
                    "annotation": _text(child.named_children[0], 32)
                    if child.named_children
                    else "",
                    "default": "",
                    "variadic": "args",
                }
            )
        elif child.type == "identifier":
            out.append({"name": _text(child, 24), "annotation": "", "default": "", "variadic": None})
    return out


@register(Language.JAVA)
def _factory() -> JavaAdapter:
    return JavaAdapter()
