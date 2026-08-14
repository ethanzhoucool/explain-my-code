"""API contract, cache behaviour, and the LLM layer's failure modes."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from explain_my_code.api.main import app
from explain_my_code.cache import Cache, cache_key
from explain_my_code.core import explain
from explain_my_code.ir import Level, Source
from explain_my_code.narrate.llm import (
    RESPONSE_SCHEMA,
    Enrichment,
    EnrichmentError,
    _validate,
    build_context,
    enrich,
    merge,
)

client = TestClient(app)
PY = "def add(a, b):\n    return a + b\n"


# -- endpoints -------------------------------------------------------------------


def test_explain_returns_the_documented_shape():
    body = client.post("/v1/explain", json={"code": PY, "level": "beginner"}).json()
    for key in ("language", "level", "parser", "summary", "lines", "annotations",
                "concepts", "analysis", "timingsMs"):
        assert key in body, f"missing {key}"
    assert body["language"] == "python"


def test_explain_auto_detects_when_language_is_omitted():
    body = client.post("/v1/explain", json={"code": "SELECT 1 FROM t;"}).json()
    assert body["language"] == "sql"


def test_explain_rejects_an_unknown_language():
    assert client.post("/v1/explain", json={"code": PY, "language": "cobol"}).status_code == 422


def test_explain_rejects_empty_code():
    assert client.post("/v1/explain", json={"code": ""}).status_code == 422


def test_oversized_payload_returns_413():
    response = client.post("/v1/explain", json={"code": "x = 1\n" * 60_000})
    assert response.status_code in (413, 422)


def test_all_levels_returns_all_three():
    body = client.post("/v1/explain/all-levels", json={"code": PY}).json()
    assert {"eli5", "beginner", "developer"} <= set(body)
    assert body["eli5"]["summary"] != body["developer"]["summary"]


def test_include_ir_is_opt_in():
    without = client.post("/v1/explain", json={"code": PY}).json()
    with_ir = client.post("/v1/explain", json={"code": PY, "includeIr": True}).json()
    assert "ir" not in without or without["ir"] is None
    assert with_ir["ir"]["kind"] == "module"


def test_analyze_returns_metrics_without_prose():
    body = client.post("/v1/analyze", json={"code": PY}).json()
    assert "summary" not in body
    assert body["analysis"]["metrics"]["cyclomatic"] == 1


def test_detect_endpoint():
    body = client.post("/v1/detect", json={"code": "#include <cstdio>\nint main(){}"}).json()
    assert body["language"] == "cpp"
    assert 0 <= body["confidence"] <= 1


def test_languages_endpoint_lists_five():
    body = client.get("/v1/languages").json()
    assert len(body["languages"]) == 5


def test_concepts_endpoint_documents_the_catalogue():
    body = client.get("/v1/concepts").json()
    assert len(body["concepts"]) > 20
    for concept in body["concepts"]:
        assert set(concept["texts"]) == {"eli5", "beginner", "developer"}


def test_healthz():
    body = client.get("/healthz").json()
    assert body["status"] == "ok"
    assert body["languages"] and "cache" in body


def test_openapi_is_valid_and_documents_every_route():
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "Explain My Code"
    for path in ("/v1/explain", "/v1/analyze", "/v1/detect", "/healthz"):
        assert path in schema["paths"]


def test_index_serves_the_ui():
    response = client.get("/")
    assert response.status_code == 200
    assert "Explain My Code" in response.text


def test_streaming_emits_the_static_frame_first():
    with client.stream("POST", "/v1/explain/stream", json={"code": PY}) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())
    assert "event: static" in body
    assert "event: done" in body
    payload = json.loads(body.split("event: static\ndata: ")[1].split("\n\n")[0])
    assert payload["language"] == "python"


def test_streaming_reports_a_missing_provider_without_failing_the_request(monkeypatch):
    monkeypatch.setattr("explain_my_code.api.main.get_provider", lambda name=None: None)
    with client.stream("POST", "/v1/explain/stream",
                       json={"code": PY, "enrich": True}) as response:
        body = "".join(response.iter_text())
    assert "event: static" in body      # the static explanation still arrived
    assert "no_provider" in body


# -- cache -------------------------------------------------------------------------


def test_cache_round_trip_and_stats():
    cache = Cache(capacity=2)
    cache.set("a", {"v": 1})
    assert cache.get("a") == {"v": 1}
    assert cache.get("missing") is None
    assert cache.stats["hits"] == 1 and cache.stats["misses"] == 1


def test_cache_evicts_least_recently_used():
    cache = Cache(capacity=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.get("a")          # 'a' becomes most-recent, so 'b' is next out
    cache.set("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1


def test_cache_respects_ttl():
    cache = Cache(ttl_seconds=0)
    cache.set("a", 1)
    assert cache.get("a") is None


def test_cache_key_covers_everything_that_changes_the_answer():
    base = {"source": "x", "language": "python", "level": "beginner",
            "provider": "p", "model": "m"}
    key = cache_key(**base)
    for field in base:
        changed = {**base, field: "different"}
        assert cache_key(**changed) != key, f"{field} does not affect the key"


def test_disk_cache_survives_a_new_instance(tmp_path):
    Cache(directory=tmp_path).set("k", {"v": 7})
    assert Cache(directory=tmp_path).get("k") == {"v": 7}


# -- LLM layer ---------------------------------------------------------------------


def test_grounding_context_contains_the_established_facts():
    result = explain("def fib(n):\n    return n if n <= 1 else fib(n-1)+fib(n-2)\n")
    context = build_context(result.analysis, Level.DEVELOPER, result.source)
    assert "STATIC FACTS" in context and "do not repeat" in context
    assert "fib" in context and "recursive" in context
    assert "   1 | def fib(n):" in context, "source must be line-numbered for the model"


def test_response_schema_is_strict():
    assert RESPONSE_SCHEMA["additionalProperties"] is False
    assert set(RESPONSE_SCHEMA["required"]) == {"summary", "lines", "risks"}


def test_validate_accepts_a_good_payload():
    summary, lines, risks = _validate(
        {"summary": "ok", "lines": [{"line": 1, "text": "hi", "confidence": 0.8}], "risks": []}, 3
    )
    assert summary == "ok" and lines[0]["confidence"] == 0.8 and risks == []


def test_validate_drops_lines_outside_the_file():
    _, lines, _ = _validate(
        {"summary": "s", "lines": [{"line": 999, "text": "nope", "confidence": 1}]}, 3
    )
    assert lines == [], "a hallucinated line number must not reach the UI"


def test_validate_clamps_confidence():
    _, lines, _ = _validate(
        {"summary": "s", "lines": [{"line": 1, "text": "t", "confidence": 42}]}, 3
    )
    assert lines[0]["confidence"] == 1.0


@pytest.mark.parametrize("payload", ["not a dict", {}, {"summary": "", "lines": []}])
def test_validate_rejects_unusable_payloads(payload):
    with pytest.raises(EnrichmentError):
        _validate(payload, 3)


def test_enrich_degrades_gracefully_with_no_provider(monkeypatch):
    monkeypatch.setattr("explain_my_code.narrate.llm.get_provider", lambda name=None: None)
    result = explain(PY)
    outcome = enrich(PY, result.analysis, Level.BEGINNER)
    assert not outcome.ok and "no LLM provider" in outcome.error


def test_merge_never_drops_static_annotations():
    result = explain(PY, level=Level.BEGINNER)
    before = len(result.annotations)
    merged = merge(result.annotations, Enrichment(summary="", error="boom"))
    assert len(merged) == before
    assert all(a.source is Source.STATIC for a in merged)


def test_merge_layers_llm_annotations_on_top():
    result = explain(PY, level=Level.BEGINNER)
    from explain_my_code.narrate.llm import _to_annotations

    extra = _to_annotations([{"line": 1, "text": "adds two numbers", "confidence": 0.7}],
                            Level.BEGINNER, PY)
    merged = merge(result.annotations, Enrichment(summary="s", annotations=extra))
    assert len(merged) == len(result.annotations) + 1
    assert any(a.source is Source.LLM for a in merged)


def test_enriched_lines_survive_the_line_view():
    """Regression: LLM annotations were ranked against static ones by Kind.

    An LLM annotation has no Kind to score, so the static annotation always won and
    every enriched line vanished from `lines` — the CLI's --enrich flag rendered
    nothing and the API response looked unenriched.
    """
    from explain_my_code.core import explain as run
    from explain_my_code.narrate.annotate import line_view
    from explain_my_code.narrate.llm import _to_annotations

    result = run(PY, level=Level.BEGINNER)
    static_line = result.lines[0].line
    llm = _to_annotations(
        [{"line": static_line, "text": "adds two numbers for the caller", "confidence": 0.8}],
        Level.BEGINNER,
        PY,
    )
    merged = line_view([*result.annotations, *llm], Level.BEGINNER)
    row = next(r for r in merged if r.line == static_line)
    assert row.text, "static explanation must survive"
    assert row.ai == "adds two numbers for the caller", "LLM insight must survive too"
    assert row.ai_confidence == 0.8
    assert "ai" in row.to_dict()


def test_line_view_keeps_an_llm_only_line():
    """An LLM annotation on a line with no static explanation still shows up."""
    from explain_my_code.narrate.annotate import line_view
    from explain_my_code.narrate.llm import _to_annotations

    llm = _to_annotations([{"line": 2, "text": "off-by-one risk", "confidence": 0.4}],
                          Level.BEGINNER, PY)
    rows = line_view(llm, Level.BEGINNER)
    assert [r.line for r in rows] == [2]
    assert rows[0].ai == "off-by-one risk"
    assert rows[0].source is Source.LLM
