"""FastAPI service. Everything routes through `core.explain`, so the API, the CLI and
the web UI can never disagree about what the analysis says."""

from __future__ import annotations

import json
import os
import time
from collections import deque
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from explain_my_code import __version__
from explain_my_code.api.schemas import (
    AnalyzeRequest,
    DetectRequest,
    ExplainRequest,
    ExplainResponse,
    HealthResponse,
)
from explain_my_code.cache import default_cache
from explain_my_code.core import (
    SourceTooLarge,
    detect_language,
    explain,
    supported_languages,
)
from explain_my_code.ir import Level
from explain_my_code.narrate.llm import (
    SYSTEM_PROMPT,
    available_providers,
    build_context,
    get_provider,
)

WEB_ROOT = Path(__file__).resolve().parent.parent.parent / "web"

DESCRIPTION = """
Static analysis that explains itself.

Source is parsed to a **language-neutral IR** (CPython `ast` for Python, tree-sitter for
JavaScript / Java / C++, sqlglot for SQL), analysed for complexity, scope, call structure
and asymptotic cost, then narrated at three audience levels from typed facts rather than
keyword matching.

The optional `enrich` flag layers an LLM pass on top, grounded in that analysis. It can
add intent and likely bugs, and is never the source of structural claims.
"""

app = FastAPI(
    title="Explain My Code",
    description=DESCRIPTION,
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "explain", "description": "Turn source into explanations."},
        {"name": "analyze", "description": "Metrics and findings without prose."},
        {"name": "meta", "description": "Capabilities and health."},
    ],
)


# -- rate limiting -------------------------------------------------------------------

RATE_LIMIT = int(os.environ.get("EMC_RATE_LIMIT", "60"))
RATE_WINDOW = 60.0
_buckets: dict[str, deque[float]] = {}


@app.middleware("http")
async def rate_limit(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Fixed-window limiter on the write-shaped endpoints.

    The LLM path costs real money, so an unauthenticated public demo needs some ceiling.
    In-process by design. One instance, one bucket; a multi-instance deployment should
    put a real limiter in front.
    """
    if request.method != "POST" or not request.url.path.startswith("/v1/"):
        return await call_next(request)

    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = _buckets.setdefault(client, deque())
    while bucket and now - bucket[0] > RATE_WINDOW:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT:
        retry_after = int(RATE_WINDOW - (now - bucket[0])) + 1
        return JSONResponse(
            {"error": "rate_limited", "detail": f"Try again in {retry_after}s."},
            status_code=429,
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)
    return await call_next(request)


@app.exception_handler(SourceTooLarge)
async def _too_large(_: Request, exc: SourceTooLarge) -> JSONResponse:
    return JSONResponse({"error": "source_too_large", "detail": str(exc)}, status_code=413)


# -- endpoints -----------------------------------------------------------------------


@app.post("/v1/explain", response_model=ExplainResponse, tags=["explain"])
def explain_endpoint(payload: ExplainRequest) -> Any:
    """Parse, analyse and explain a snippet at one audience level."""
    try:
        result = explain(
            payload.code,
            language=payload.language,
            level=payload.level,
            filename=payload.filename,
            enrich=(payload.provider or True) if payload.enrich else False,
        )
    except SourceTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    return result.to_dict(include_ir=payload.include_ir)


@app.post("/v1/explain/all-levels", tags=["explain"])
def explain_all_levels(payload: ExplainRequest) -> Any:
    """All three levels in one call.

    The parse and analysis passes are the expensive part and are level-independent, so
    the client can switch levels instantly instead of paying a round trip per level.
    """
    out: dict[str, Any] = {}
    for level in Level:
        result = explain(
            payload.code,
            language=payload.language,
            level=level,
            filename=payload.filename,
            enrich=False,
        )
        out[level.value] = {
            "summary": result.summary,
            "lines": [line.to_dict() for line in result.lines],
            "annotations": [a.to_dict(level) for a in result.annotations],
            "concepts": [c.to_dict(level) for c in result.analysis.concepts],
        }
        out.setdefault("language", result.language.value)
        out.setdefault("analysis", result.analysis.to_dict())
        out.setdefault("diagnostics", [d.to_dict() for d in result.diagnostics])
    return out


@app.post("/v1/analyze", tags=["analyze"])
def analyze_endpoint(payload: AnalyzeRequest) -> Any:
    """Metrics, findings, call graph and symbols. No prose."""
    result = explain(payload.code, language=payload.language, filename=payload.filename)
    return {
        "language": result.language.value,
        "parser": result.analysis.parser,
        "analysis": result.analysis.to_dict(),
        "concepts": [c.to_dict() for c in result.analysis.concepts],
        "diagnostics": [d.to_dict() for d in result.diagnostics],
        "timingsMs": result.timings_ms,
    }


@app.post("/v1/detect", tags=["analyze"])
def detect_endpoint(payload: DetectRequest) -> Any:
    """Guess the language of a snippet."""
    detected = detect_language(payload.code, payload.filename)
    return {
        "language": detected.language.value,
        "confidence": detected.confidence,
        "runnerUp": detected.runner_up.value if detected.runner_up else None,
    }


@app.post("/v1/explain/stream", tags=["explain"])
async def explain_stream(payload: ExplainRequest) -> StreamingResponse:
    """Server-sent events: static explanation first, enrichment as it arrives.

    The static pass takes about a millisecond, so the page can render fully before the
    model has produced a token. The LLM is a progressive enhancement, not a dependency.
    """

    async def events() -> AsyncIterator[str]:
        def sse(event: str, data: Any) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        try:
            result = explain(
                payload.code,
                language=payload.language,
                level=payload.level,
                filename=payload.filename,
            )
        except SourceTooLarge as exc:
            yield sse("error", {"error": "source_too_large", "detail": str(exc)})
            return

        yield sse("static", result.to_dict())

        if not payload.enrich:
            yield sse("done", {"enriched": False})
            return

        provider = get_provider(payload.provider)
        if provider is None:
            yield sse("error", {"error": "no_provider", "detail": "No LLM provider configured."})
            yield sse("done", {"enriched": False})
            return

        yield sse("enrich_start", {"provider": provider.name, "model": provider.model})
        prompt = build_context(result.analysis, result.level, result.source)
        try:
            for chunk in provider.stream(SYSTEM_PROMPT, prompt):
                yield sse("delta", {"text": chunk})
        except Exception as exc:  # provider SDKs raise their own error types
            yield sse("error", {"error": "enrichment_failed", "detail": str(exc)})
        yield sse("done", {"enriched": True})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/v1/languages", tags=["meta"])
def languages_endpoint() -> Any:
    return {"languages": supported_languages()}


@app.get("/v1/concepts", tags=["meta"])
def concepts_endpoint() -> Any:
    """The full concept catalogue the analyser can detect."""
    from explain_my_code.analysis.concepts import CONCEPTS

    return {
        "concepts": [
            {
                "id": c.concept_id,
                "label": c.label,
                "category": c.category,
                "languages": sorted(lang.value for lang in c.languages) if c.languages else "all",
                "texts": {"eli5": c.eli5, "beginner": c.beginner, "developer": c.developer},
            }
            for c in CONCEPTS
        ]
    }


@app.get("/healthz", response_model=HealthResponse, tags=["meta"])
def health() -> Any:
    return {
        "status": "ok",
        "version": __version__,
        "languages": supported_languages(),
        "providers": available_providers(),
        "cache": default_cache().stats,
    }


# -- web UI ---------------------------------------------------------------------------

if (WEB_ROOT / "static").is_dir():
    app.mount("/static", StaticFiles(directory=WEB_ROOT / "static"), name="static")


@app.get("/", include_in_schema=False)
def index() -> HTMLResponse:
    page = WEB_ROOT / "index.html"
    if not page.exists():
        return HTMLResponse(
            "<h1>Explain My Code</h1><p>API is running. See <a href='/docs'>/docs</a>.</p>"
        )
    return HTMLResponse(page.read_text("utf-8"))
