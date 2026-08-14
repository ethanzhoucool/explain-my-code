"""C++ -> IR.

The awkward part of C++ is that a function's name lives at the bottom of a declarator
chain (`function_declarator -> pointer_declarator -> identifier`), so `name_for` walks
down rather than reading a `name` field.
"""

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
        "printf", "scanf", "malloc", "free", "memcpy", "memset", "strlen", "strcpy",
        "push_back", "pop_back", "size", "empty", "begin", "end", "find", "insert",
        "erase", "at", "front", "back", "clear", "resize", "reserve", "sort",
        "make_shared", "make_unique", "move", "swap", "count", "accumulate", "max",
        "min", "abs", "cout", "cin", "endl", "to_string", "stoi", "emplace_back",
    }
)

KNOWN_COSTS = {
    "sort": "n log n", "stable_sort": "n log n", "find": "n", "count": "n",
    "accumulate": "n", "copy": "n", "erase": "n", "insert": "n", "reverse": "n",
    "max_element": "n", "min_element": "n", "lower_bound": "log n", "upper_bound": "log n",
    "binary_search": "log n", "resize": "n", "memcpy": "n", "strlen": "n",
}

DECLARATOR_FIELDS = ("declarator",)


class CppAdapter(TreeSitterAdapter):
    language = Language.CPP
    parser_name = "tree-sitter-cpp"
    BUILTINS = BUILTINS
    KNOWN_COSTS = KNOWN_COSTS

    KINDS = {
        "class_specifier": Kind.CLASS,
        "struct_specifier": Kind.CLASS,
        "union_specifier": Kind.CLASS,
        "enum_specifier": Kind.CLASS,
        "function_definition": Kind.FUNCTION,
        "parameter_declaration": Kind.PARAM,
        "optional_parameter_declaration": Kind.PARAM,
        "variadic_parameter_declaration": Kind.PARAM,
        "if_statement": Kind.BRANCH,
        "else_clause": Kind.ELSE,
        "for_statement": Kind.LOOP_FOR,
        "for_range_loop": Kind.LOOP_FOREACH,
        "while_statement": Kind.LOOP_WHILE,
        "do_statement": Kind.LOOP_DO,
        "switch_statement": Kind.SWITCH,
        "case_statement": Kind.CASE,
        "break_statement": Kind.BREAK,
        "continue_statement": Kind.CONTINUE,
        "return_statement": Kind.RETURN,
        "throw_statement": Kind.THROW,
        "try_statement": Kind.TRY,
        "catch_clause": Kind.CATCH,
        "declaration": Kind.DECL,
        "field_declaration": Kind.DECL,
        "assignment_expression": Kind.ASSIGN,
        "update_expression": Kind.AUG_ASSIGN,
        "call_expression": Kind.CALL,
        "new_expression": Kind.NEW,
        "delete_expression": Kind.DELETE,
        "field_expression": Kind.ATTRIBUTE,
        "subscript_expression": Kind.INDEX,
        "initializer_list": Kind.COLLECTION,
        "lambda_expression": Kind.LAMBDA,
        "cast_expression": Kind.CAST,
        "static_cast_expression": Kind.CAST,
        "conditional_expression": Kind.TERNARY,
        "preproc_include": Kind.IMPORT,
        "using_declaration": Kind.IMPORT,
        "namespace_definition": Kind.NAMESPACE,
        "preproc_def": Kind.DECL,
        "preproc_function_def": Kind.FUNCTION,
        "binary_expression": Kind.BINOP,
        "unary_expression": Kind.UNOP,
        "co_await_expression": Kind.AWAIT,
        "co_yield_expression": Kind.YIELD,
        "identifier": Kind.NAME,
        "field_identifier": Kind.NAME,
    }

    LITERAL_TYPES = frozenset(
        {
            "number_literal", "string_literal", "char_literal", "true", "false",
            "null", "nullptr", "raw_string_literal", "concatenated_string",
        }
    )
    LEAVES = frozenset(
        {"identifier", "field_identifier", "parameter_declaration",
         "optional_parameter_declaration", "variadic_parameter_declaration"}
    )
    OPAQUE = frozenset(
        {
            "type_identifier", "primitive_type", "namespace_identifier", "type_qualifier",
            "storage_class_specifier", "access_specifier", "template_parameter_list",
            "template_argument_list", "template_type", "sized_type_specifier",
            "placeholder_type_specifier", "auto", "type_descriptor", "system_lib_string",
            "string_content", "destructor_name", "qualified_identifier", "base_class_clause",
            "abstract_function_declarator", "lambda_capture_specifier", "lambda_default_capture",
            "attribute_specifier", "ms_declspec_modifier", "virtual", "explicit_function_specifier",
        }
    )
    COMMENT_TYPES = frozenset({"comment"})

    def _grammar(self) -> Any:
        import tree_sitter_cpp

        return tree_sitter_cpp.language()

    # -- overrides --------------------------------------------------------------

    def kind_for(self, ts_node):  # type: ignore[override]
        node_type = ts_node.type
        if node_type == "function_definition":
            owner = _enclosing_class_name(ts_node)
            if owner is None:
                return Kind.FUNCTION
            name = _declarator_name(ts_node)
            if name == owner or name == f"~{owner}":
                return Kind.CONSTRUCTOR
            return Kind.METHOD
        if node_type == "call_expression":
            func = _field(ts_node, "function")
            if func is not None and func.type == "field_expression":
                return Kind.METHOD_CALL
            return Kind.CALL
        return super().kind_for(ts_node)

    def name_for(self, ts_node, kind):  # type: ignore[override]
        if kind in {Kind.FUNCTION, Kind.METHOD, Kind.CONSTRUCTOR}:
            return _declarator_name(ts_node) or "function"
        if kind is Kind.DECL:
            declarator = _field(ts_node, "declarator")
            return _declarator_name(ts_node) or _text(declarator, 32) or None
        if kind is Kind.IMPORT:
            if ts_node.type == "preproc_include":
                return _field_text(ts_node, "path", 48).strip('<>"')
            return _text(ts_node, 48).removeprefix("using ").rstrip(";")
        if kind is Kind.PARAM:
            return _declarator_name(ts_node) or _field_text(ts_node, "type", 24)
        if kind is Kind.LAMBDA:
            return "lambda"
        return super().name_for(ts_node, kind)

    def recurse_into(self, ts_node, kind):  # type: ignore[override]
        if kind is Kind.DECL:
            declarators = _children_of_type(ts_node, "init_declarator")
            if declarators:
                return [
                    value
                    for declarator in declarators
                    if (value := _field(declarator, "value")) is not None
                ]
            return []
        return super().recurse_into(ts_node, kind)

    def _catch_type(self, ts_node) -> str:  # type: ignore[override]
        params = _field(ts_node, "parameters")
        if params is None:
            return ""
        return _text(params, 40).strip("()")

    def _meta_member(self, ts_node) -> dict[str, Any]:  # type: ignore[override]
        return {
            "object": _field_text(ts_node, "argument", 32),
            "attribute": _field_text(ts_node, "field", 32),
            "via_pointer": _field_text(ts_node, "operator", 4) == "->",
        }

    def _meta_index(self, ts_node) -> dict[str, Any]:  # type: ignore[override]
        return {
            "container": _field_text(ts_node, "argument", 32),
            "key": _field_text(ts_node, "indices", 24).strip("[]"),
            "is_slice": False,
        }

    # -- meta --------------------------------------------------------------------

    def _callable_meta(self, ts_node) -> dict[str, Any]:
        params = _cpp_params(ts_node)
        declarator = _find_function_declarator(ts_node)
        qualifiers = _text(declarator, 200) if declarator is not None else ""
        source = _text(ts_node, 8192)
        template = _enclosing_template(ts_node)
        return {
            "params": params,
            "param_count": len(params),
            "param_names": [p["name"] for p in params],
            "is_async": False,
            "is_generator": "co_yield" in source,
            "is_const": qualifiers.rstrip().endswith("const") or ") const" in qualifiers,
            "is_static": "static" in _leading_text(ts_node),
            "is_virtual": "virtual" in _leading_text(ts_node),
            "returns": _field_text(ts_node, "type", 32),
            "decorators": [],
            "docstring": "",
            "is_template": template is not None,
            "template_params": _field_text(template, "parameters", 40) if template else "",
            "full_span": _span(ts_node).to_dict(),
            "body_lines": _span(ts_node).line_count,
            "is_dunder": False,
            "is_private": False,
            "allocates": "new " in source,
            "frees": "delete " in source,
        }

    meta_function = _callable_meta
    meta_method = _callable_meta
    meta_constructor = _callable_meta

    def meta_lambda(self, ts_node) -> dict[str, Any]:
        captures = _text(_field(ts_node, "captures"), 24)
        body = _field(ts_node, "body")
        return {
            "params": _cpp_params(ts_node),
            "param_count": len(_cpp_params(ts_node)),
            "param_names": [p["name"] for p in _cpp_params(ts_node)],
            "captures": captures,
            "captures_by_reference": "&" in captures,
            "captures_by_value": "=" in captures,
            "body": _text(body, 48),
            "is_expression_body": False,
        }

    def meta_class(self, ts_node) -> dict[str, Any]:
        body = _field(ts_node, "body")
        methods = (
            [
                _declarator_name(c)
                for c in body.named_children
                if c.type in {"function_definition", "declaration", "field_declaration"}
                and _find_function_declarator(c) is not None
            ]
            if body is not None
            else []
        )
        bases_node = next(
            (c for c in ts_node.named_children if c.type == "base_class_clause"), None
        )
        bases = [
            b.strip()
            for b in _text(bases_node, 64).lstrip(": ").replace("public", "").replace(
                "private", ""
            ).replace("protected", "").replace("virtual", "").split(",")
            if b.strip()
        ]
        template = _enclosing_template(ts_node)
        return {
            "bases": bases,
            "is_subclass": bool(bases),
            "method_names": [m for m in methods if m],
            "method_count": len([m for m in methods if m]),
            "is_struct": ts_node.type == "struct_specifier",
            "is_template": template is not None,
            "template_params": _field_text(template, "parameters", 40) if template else "",
            "decorators": [],
            "docstring": "",
            "full_span": _span(ts_node).to_dict(),
        }

    def meta_param(self, ts_node) -> dict[str, Any]:
        declarator = _field(ts_node, "declarator")
        declarator_text = _text(declarator, 32)
        return {
            "name": _declarator_name(ts_node) or declarator_text,
            "annotation": _field_text(ts_node, "type", 32),
            "default": _field_text(ts_node, "default_value", 24),
            "variadic": "args" if ts_node.type == "variadic_parameter_declaration" else None,
            "is_pointer": "*" in declarator_text,
            "is_reference": "&" in declarator_text,
        }

    def meta_decl(self, ts_node) -> dict[str, Any]:
        declarators = _children_of_type(ts_node, "init_declarator")
        first = declarators[0] if declarators else None
        value = _field(first, "value") if first is not None else None
        declarator_text = _text(_field(ts_node, "declarator"), 40)
        name = _declarator_name(ts_node)
        return {
            "name": name,
            "targets": [name] if name else [],
            "annotation": _field_text(ts_node, "type", 32),
            "value": _text(value, 48),
            "has_value": value is not None,
            "is_pointer": "*" in declarator_text,
            "is_reference": "&" in declarator_text,
            "is_const": "const" in _leading_text(ts_node),
            "is_static": "static" in _leading_text(ts_node),
            "is_auto": _field_text(ts_node, "type", 16) == "auto",
            "from_call": _field_text(value, "function", 32)
            if value is not None and value.type == "call_expression"
            else "",
            "declares": max(len(declarators), 1),
        }

    def meta_loop_foreach(self, ts_node) -> dict[str, Any]:
        declarator = _text(_field(ts_node, "declarator"), 32)
        return {
            "target": declarator.lstrip("&* "),
            "iterable": _field_text(ts_node, "right", 40),
            "element_type": _field_text(ts_node, "type", 24),
            "by_reference": "&" in declarator,
            "counted": False,
        }

    def meta_import(self, ts_node) -> dict[str, Any]:
        if ts_node.type == "preproc_include":
            path = _field_text(ts_node, "path", 48)
            return {
                "module": path.strip('<>"'),
                "names": [],
                "is_from": False,
                "is_system": path.startswith("<"),
                "is_stdlib": path.startswith("<") and "." not in path,
            }
        target = _text(ts_node, 48).removeprefix("using ").rstrip(";")
        return {
            "module": target.removeprefix("namespace ").strip(),
            "names": [],
            "is_from": False,
            "is_namespace": target.startswith("namespace"),
            "is_stdlib": "std" in target,
        }

    def meta_namespace(self, ts_node) -> dict[str, Any]:
        return {"name": _field_text(ts_node, "name", 32), "is_package": False}

    def meta_new(self, ts_node) -> dict[str, Any]:
        args = _field(ts_node, "arguments")
        declarator = _field(ts_node, "declarator")
        return {
            "type": _field_text(ts_node, "type", 32),
            "arity": len(args.named_children) if args is not None else 0,
            "is_array": declarator is not None and "[" in _text(declarator, 16),
        }

    def meta_delete(self, ts_node) -> dict[str, Any]:
        return {
            "target": _text(ts_node.named_children[0], 32) if ts_node.named_children else "",
            "is_array": "[]" in _text(ts_node, 32),
        }

    def meta_cast(self, ts_node) -> dict[str, Any]:
        return {
            "target_type": _field_text(ts_node, "type", 24),
            "value": _field_text(ts_node, "value", 32),
            "style": "static_cast" if ts_node.type == "static_cast_expression" else "c-style",
        }

    def meta_case(self, ts_node) -> dict[str, Any]:
        value = _field_text(ts_node, "value", 32)
        return {"pattern": value, "is_default": not value, "has_guard": False}

    def meta_aug_assign(self, ts_node) -> dict[str, Any]:
        op = _field_text(ts_node, "operator", 4)
        target = _field_text(ts_node, "argument", 32)
        return {
            "target": target, "targets": [target], "op": op[0] if op else "+",
            "value": "1", "is_accumulator": True, "is_increment": op == "++",
        }


def _enclosing_class_name(ts_node) -> str | None:
    """Name of the class this node sits inside, or None at file scope.

    Also the destructor test: `~Cache` matching the class name makes it a constructor
    kind rather than an ordinary method.
    """
    node = ts_node.parent
    while node is not None:
        if node.type in {"class_specifier", "struct_specifier"}:
            return _field_text(node, "name", 48)
        if node.type == "function_definition":
            return None
        node = node.parent
    return None


def _enclosing_template(ts_node):
    parent = ts_node.parent
    if parent is not None and parent.type == "template_declaration":
        return parent
    return None


def _find_function_declarator(ts_node):
    """Descend the declarator chain to the `function_declarator`, if there is one."""
    node = _field(ts_node, "declarator")
    seen = 0
    while node is not None and seen < 8:
        if node.type == "function_declarator":
            return node
        node = _field(node, "declarator")
        seen += 1
    return None


def _declarator_name(ts_node) -> str:
    """Bottom of the declarator chain: `int* f(int)` -> `f`, `int** p` -> `p`."""
    node = _field(ts_node, "declarator")
    seen = 0
    while node is not None and seen < 12:
        if node.type in {
            "identifier", "field_identifier", "type_identifier",
            "qualified_identifier", "destructor_name", "operator_name",
        }:
            return _text(node, 48)
        nested = _field(node, "declarator")
        if nested is None:
            return _text(node, 48).split("(")[0].strip("*&[] ")
        node = nested
        seen += 1
    return ""


def _leading_text(ts_node) -> str:
    """Anonymous tokens before the first named child (`static`, `const`, `virtual`)."""
    parts: list[str] = []
    for child in ts_node.children:
        if child.is_named and child.type not in {"type_qualifier", "storage_class_specifier"}:
            break
        text = child.text
        if text:
            parts.append(text.decode("utf-8", "replace"))
    return " ".join(parts)


def _cpp_params(ts_node) -> list[dict[str, Any]]:
    declarator = _find_function_declarator(ts_node)
    holder = _field(declarator, "parameters") if declarator is not None else None
    if holder is None:
        holder = _field(ts_node, "declarator")
        if holder is not None and holder.type == "abstract_function_declarator":
            holder = _field(holder, "parameters")
        else:
            holder = None
    if holder is None:
        return []
    out: list[dict[str, Any]] = []
    for child in holder.named_children:
        if child.type not in {
            "parameter_declaration", "optional_parameter_declaration",
            "variadic_parameter_declaration",
        }:
            continue
        declarator_text = _text(_field(child, "declarator"), 32)
        out.append(
            {
                "name": _declarator_name(child) or declarator_text,
                "annotation": _field_text(child, "type", 32),
                "default": _field_text(child, "default_value", 24),
                "variadic": "args" if child.type == "variadic_parameter_declaration" else None,
                "is_pointer": "*" in declarator_text,
                "is_reference": "&" in declarator_text,
            }
        )
    return out


@register(Language.CPP)
def _factory() -> CppAdapter:
    return CppAdapter()
