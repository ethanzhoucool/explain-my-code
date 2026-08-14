"""Every adapter must produce the same IR shapes for the same concepts.

These are the tests that keep "one phrasebook, five languages" honest: if a grammar
update changes a field name, the corresponding `Kind` disappears here and the suite
fails rather than the UI quietly losing an explanation.
"""

from __future__ import annotations

import pytest

from explain_my_code.adapters.base import get_adapter, load_all, registered_languages
from explain_my_code.ir import CALLABLE_KINDS, Kind, Language

load_all()

SNIPPETS = {
    Language.PYTHON: """
import os

class Store:
    def __init__(self, cap=10):
        self.cap = cap

    def find(self, items, target):
        for index, value in enumerate(items):
            if value == target:
                return index
        return None

def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
""",
    Language.JAVASCRIPT: """
import fs from 'fs';

class Store {
  constructor(cap = 10) { this.cap = cap; }

  find(items, target) {
    for (const value of items) {
      if (value === target) { return value; }
    }
    return null;
  }
}

function fib(n) {
  if (n <= 1) return n;
  return fib(n - 1) + fib(n - 2);
}
""",
    Language.JAVA: """
import java.util.List;

public class Store {
    private int cap;

    public Store(int cap) { this.cap = cap; }

    public int find(int[] items, int target) {
        for (int value : items) {
            if (value == target) { return value; }
        }
        return -1;
    }

    public int fib(int n) {
        if (n <= 1) return n;
        return fib(n - 1) + fib(n - 2);
    }
}
""",
    Language.CPP: """
#include <vector>

class Store {
 public:
  Store(int cap) : cap_(cap) {}

  int find(const std::vector<int>& items, int target) {
    for (const auto& value : items) {
      if (value == target) { return value; }
    }
    return -1;
  }

  int fib(int n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
  }

 private:
  int cap_;
};
""",
    Language.SQL: """
SELECT c.name, COUNT(*) AS orders
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE c.active = TRUE
GROUP BY c.name
ORDER BY orders DESC
LIMIT 10;
""",
}


@pytest.fixture(scope="module", params=list(SNIPPETS), ids=lambda lang: lang.value)
def parsed(request):
    language = request.param
    return language, get_adapter(language).parse(SNIPPETS[language])


def test_every_registered_language_has_a_snippet():
    assert set(registered_languages()) == set(SNIPPETS)


def test_adapter_is_available(parsed):
    language, _ = parsed
    assert get_adapter(language).available(), f"{language.value} grammar failed to load"


def test_parses_without_errors(parsed):
    _, result = parsed
    assert not result.degraded
    assert [d for d in result.diagnostics if d.severity == "error"] == []


def test_root_is_a_module(parsed):
    _, result = parsed
    assert result.root.kind is Kind.MODULE
    assert result.root.children, "adapter produced an empty tree"


def test_spans_are_within_the_source(parsed):
    _, result = parsed
    line_count = len(result.source.splitlines())
    for node in result.root.walk():
        assert 1 <= node.span.start_line <= line_count, f"{node.kind} out of range"
        assert node.span.end_line >= node.span.start_line


def test_finds_a_branch_and_a_loop(parsed):
    language, result = parsed
    kinds = {node.kind for node in result.root.walk()}
    if language is Language.SQL:
        assert Kind.SELECT in kinds and Kind.JOIN in kinds and Kind.WHERE in kinds
        assert Kind.GROUP_BY in kinds and Kind.ORDER_BY in kinds and Kind.LIMIT in kinds
    else:
        assert Kind.BRANCH in kinds, "no conditional found"
        assert kinds & {Kind.LOOP_FOR, Kind.LOOP_FOREACH}, "no loop found"
        assert Kind.RETURN in kinds


def test_finds_callables_with_parameters(parsed):
    language, result = parsed
    if language is Language.SQL:
        pytest.skip("SQL has no callables")
    callables = [n for n in result.root.walk() if n.kind in CALLABLE_KINDS]
    assert callables, "no functions found"
    names = {node.name for node in callables}
    assert "fib" in names
    fib = next(node for node in callables if node.name == "fib")
    assert fib.meta["param_count"] == 1
    assert fib.meta["param_names"] == ["n"]


def test_finds_a_class(parsed):
    language, result = parsed
    if language is Language.SQL:
        pytest.skip("SQL has no classes")
    classes = [n for n in result.root.walk() if n.kind is Kind.CLASS]
    assert [c.name for c in classes] == ["Store"]


def test_finds_an_import(parsed):
    language, result = parsed
    if language is Language.SQL:
        pytest.skip("SQL has no imports")
    imports = [n for n in result.root.walk() if n.kind is Kind.IMPORT]
    assert imports, "no import found"
    assert imports[0].meta.get("module")


def test_keyword_inside_a_string_is_not_a_construct():
    """The v1 regression: `# for` and `"if"` are not control flow."""
    source = 'message = "if you can for loop while true"\n# for while if\n'
    result = get_adapter(Language.PYTHON).parse(source)
    kinds = {node.kind for node in result.root.walk()}
    assert not kinds & {Kind.BRANCH, Kind.LOOP_FOR, Kind.LOOP_FOREACH, Kind.LOOP_WHILE}


def test_broken_python_still_explains_the_prefix():
    source = "def good():\n    return 1\n\ndef broken(:\n"
    result = get_adapter(Language.PYTHON).parse(source)
    assert any(d.severity == "error" for d in result.diagnostics)
    names = {n.name for n in result.root.walk() if n.kind in CALLABLE_KINDS}
    assert "good" in names, "salvageable prefix was discarded"


def test_empty_source_is_not_a_crash():
    for language in SNIPPETS:
        result = get_adapter(language).parse("")
        assert result.root.kind is Kind.MODULE


@pytest.mark.parametrize("language", [Language.JAVASCRIPT, Language.JAVA, Language.CPP])
def test_tree_sitter_recovers_from_syntax_errors(language):
    result = get_adapter(language).parse("function ( { [ unclosed")
    assert result.root.kind is Kind.MODULE  # a tree is always returned
