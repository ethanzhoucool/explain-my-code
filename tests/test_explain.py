"""End-to-end behaviour of `explain()` — levels, detection, rendering, robustness."""

from __future__ import annotations

import pytest

from explain_my_code.core import SourceTooLarge, detect_language, explain, supported_languages
from explain_my_code.ir import Kind, Language, Level, Node, Source, Span
from explain_my_code.narrate.phrasebook import TEMPLATES, phrase

SAMPLE = """
def duplicates(items):
    seen = set()
    for item in items:
        if item in seen:
            return item
        seen.add(item)
    return None
"""


def test_all_three_levels_produce_different_prose():
    texts = {}
    for level in Level:
        result = explain(SAMPLE, level=level)
        texts[level] = {line.line: line.text for line in result.lines}
    assert texts[Level.ELI5] != texts[Level.BEGINNER] != texts[Level.DEVELOPER]


def test_eli5_avoids_jargon():
    jargon = ("cyclomatic", "asymptotic", "invariant", "idempotent", "polymorphism")
    result = explain(SAMPLE, level=Level.ELI5)
    blob = " ".join(line.text for line in result.lines).lower() + result.summary.lower()
    for term in jargon:
        assert term not in blob, f"ELI5 used the word {term!r}"


def test_developer_level_annotates_more_than_eli5():
    assert len(explain(SAMPLE, level=Level.DEVELOPER).lines) >= len(
        explain(SAMPLE, level=Level.ELI5).lines
    )


def test_one_explanation_per_line_at_most():
    result = explain(SAMPLE, level=Level.DEVELOPER)
    numbers = [line.line for line in result.lines]
    assert len(numbers) == len(set(numbers))


def test_explanations_point_at_real_lines():
    result = explain(SAMPLE, level=Level.BEGINNER)
    line_count = len(SAMPLE.splitlines())
    for line in result.lines:
        assert 1 <= line.line <= line_count


def test_summary_mentions_the_function():
    assert "duplicates" in explain(SAMPLE, level=Level.BEGINNER).summary


def test_static_explanations_are_marked_as_static():
    result = explain(SAMPLE)
    assert all(annotation.source is Source.STATIC for annotation in result.annotations)


def test_no_unfilled_template_placeholders_leak():
    """A missing meta key must drop the phrase, never render a raw `{slot}`."""
    for language in Language:
        for level in Level:
            result = explain(_snippet_for(language), language=language, level=level)
            for line in result.lines:
                assert "{" not in line.text and "}" not in line.text, line.text


def _snippet_for(language: Language) -> str:
    return {
        Language.PYTHON: SAMPLE,
        Language.JAVASCRIPT: "function f(xs){ for (const x of xs){ if (x) return x; } return null; }",
        Language.JAVA: "class A { int f(int[] xs){ for (int x : xs){ if (x > 0) return x; } return -1; } }",
        Language.CPP: "int f(int* xs, int n){ for (int i = 0; i < n; ++i){ if (xs[i]) return xs[i]; } return -1; }",
        Language.SQL: "SELECT a, COUNT(*) FROM t JOIN u ON u.id = t.id WHERE a > 1 GROUP BY a;",
    }[language]


@pytest.mark.parametrize("language", list(Language), ids=lambda lang: lang.value)
def test_every_language_explains_end_to_end(language):
    result = explain(_snippet_for(language), language=language)
    assert result.summary
    assert result.lines
    assert result.timings_ms["total"] > 0


def test_phrasebook_covers_every_level_it_declares():
    for kind, levels in TEMPLATES.items():
        assert set(levels) == set(Level), f"{kind} is missing a level"


def test_phrase_returns_none_rather_than_raising_on_bad_meta():
    node = Node(kind=Kind.LOOP_FOREACH, span=Span(1, 0, 1, 1), name="for", meta={})
    for level in Level:
        text = phrase(node, level)
        assert text is None or "{" not in text


# -- language detection --------------------------------------------------------


@pytest.mark.parametrize(
    "source,expected",
    [
        ("def f(x):\n    return x\n", Language.PYTHON),
        ("const a = 1;\nconsole.log(a);\n", Language.JAVASCRIPT),
        ("public static void main(String[] a) { System.out.println(1); }", Language.JAVA),
        ("#include <vector>\nint main(){ return 0; }", Language.CPP),
        ("SELECT * FROM users WHERE id = 1;", Language.SQL),
    ],
)
def test_detection_from_source(source, expected):
    assert detect_language(source).language is expected


@pytest.mark.parametrize(
    "filename,expected",
    [("a.py", Language.PYTHON), ("a.ts", Language.JAVASCRIPT), ("A.java", Language.JAVA),
     ("a.cc", Language.CPP), ("q.sql", Language.SQL)],
)
def test_detection_from_filename_wins(filename, expected):
    result = detect_language("SELECT 1", filename)
    assert result.language is expected
    assert result.confidence == 1.0


def test_detection_reports_low_confidence_on_ambiguous_input():
    assert detect_language("x = 1").confidence < 1.0


# -- robustness ----------------------------------------------------------------


def test_oversized_source_is_rejected_cleanly():
    with pytest.raises(SourceTooLarge):
        explain("x = 1\n" * 60_000)


@pytest.mark.parametrize("source", ["", "   ", "\n\n\n", "\t", "# just a comment\n", "???"])
def test_degenerate_input_does_not_raise(source):
    result = explain(source, language=Language.PYTHON)
    assert isinstance(result.summary, str)


def test_unicode_survives_the_round_trip():
    result = explain('def greet():\n    return "héllo wörld 👋"\n')
    assert result.lines


def test_syntax_error_is_reported_not_raised():
    result = explain("def broken(:\n    pass\n")
    assert any(d.severity == "error" for d in result.diagnostics)


def test_supported_languages_are_all_available():
    for entry in supported_languages():
        assert entry["available"], f"{entry['id']} is not available"
        assert entry["extensions"]


def test_serialises_to_json():
    import json

    payload = explain(SAMPLE).to_dict(include_ir=True)
    assert json.loads(json.dumps(payload))["language"] == "python"
