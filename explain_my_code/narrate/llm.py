"""Optional LLM enrichment, grounded in the static analysis.

v1 handed the model a bare snippet and asked it to explain everything, so its output
had to be trusted wholesale. Here the static pass has already established the facts:
what the constructs are, how they nest, what they cost. The model is given that
as context and asked only for what static analysis genuinely cannot derive: intent,
naming quality, domain meaning, and likely bugs.

Three things follow from that:
  * the model is told to defer to the supplied facts, so it cannot silently contradict
    the parse tree;
  * output is constrained to a JSON schema and validated before use, so a malformed
    reply degrades to the static explanation rather than breaking the response;
  * every enriched annotation is tagged `Source.LLM` with a confidence below 1.0, so
    the UI can mark it as model-generated.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol

from explain_my_code.analysis.pipeline import Analysis
from explain_my_code.cache import Cache, cache_key, default_cache
from explain_my_code.ir import Annotation, Kind, Level, Source, Span

MAX_LINES_SENT = 400
MAX_ENRICHED_LINES = 120

#: Constrains the model's reply. Every provider gets the same shape.
RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "2-3 sentences on what this code is for and why it is written this way. Say what the static facts cannot: the intent behind the code.",
        },
        "lines": {
            "type": "array",
            "description": "Only lines where you can add something the static analysis missed. Skip the rest.",
            "items": {
                "type": "object",
                "properties": {
                    "line": {"type": "integer", "description": "1-based line number"},
                    "text": {"type": "string", "description": "One sentence of added insight."},
                    "confidence": {
                        "type": "number",
                        "description": "0-1. Below 0.5 if you are inferring intent you cannot verify.",
                    },
                },
                "required": ["line", "text", "confidence"],
                "additionalProperties": False,
            },
        },
        "risks": {
            "type": "array",
            "description": "Likely bugs or surprises a reader should know about. Empty if none.",
            "items": {
                "type": "object",
                "properties": {
                    "line": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["line", "text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "lines", "risks"],
    "additionalProperties": False,
}

LEVEL_GUIDANCE = {
    Level.ELI5: (
        "Explain to a curious twelve-year-old. Everyday words and concrete images, no "
        "jargon. Never sacrifice accuracy for simplicity."
    ),
    Level.BEGINNER: (
        "Explain to someone who has written a little code but has not seen this pattern. "
        "Name the construct, then say what it does with these particular values."
    ),
    Level.DEVELOPER: (
        "Explain to an experienced engineer reading this file for the first time. Assume "
        "the syntax is obvious. Say what is worth noticing: intent, trade-offs, edge cases."
    ),
}

SYSTEM_PROMPT = """You annotate source code that has ALREADY been parsed and analysed.

You are given the static facts: the structure, the metrics, the detected concepts and
the findings. Those facts are derived from a real parse tree and are correct.

Your job is ONLY to add what static analysis cannot derive:
  - intent: what is this code FOR, in the domain it belongs to
  - naming: whether the names match what the code actually does
  - correctness: bugs a parser cannot see, like an off-by-one or a wrong comparison
  - context: why a reader might find a construct surprising here

Rules:
  - Never restate a fact you were given. "This is a for loop" is worthless. The reader
    already has that.
  - Never contradict the supplied facts. If your reading disagrees with them, say so in
    `risks` and lower your confidence; do not assert the opposite.
  - Annotate only lines where you genuinely add something. Most lines need nothing.
    Returning three good lines beats returning thirty filler ones.
  - Be specific to THIS code. Never write advice that would fit any program.
  - If you are guessing at intent, set confidence below 0.5 and say what you are assuming.

Return only JSON matching the given schema."""


@dataclass(slots=True)
class Enrichment:
    """One provider's contribution, already validated."""

    summary: str
    annotations: list[Annotation] = field(default_factory=list)
    risks: list[dict[str, Any]] = field(default_factory=list)
    provider: str = ""
    model: str = ""
    cached: bool = False
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "risks": self.risks,
            "provider": self.provider,
            "model": self.model,
            "cached": self.cached,
            "error": self.error,
            "annotationCount": len(self.annotations),
        }


class EnrichmentError(RuntimeError):
    pass


# -- grounding ---------------------------------------------------------------------


def build_context(analysis: Analysis, level: Level, source: str) -> str:
    """The facts block. Compact on purpose. It is prepended to every request."""
    metrics = analysis.metrics
    parts: list[str] = [
        f"LANGUAGE: {analysis.language.value} (parsed by {analysis.parser})",
        f"AUDIENCE: {level.value}: {LEVEL_GUIDANCE[level]}",
        "",
        "STATIC FACTS (already established, do not repeat these):",
        f"- {metrics.code_lines} lines of code, cyclomatic complexity {metrics.cyclomatic}, "
        f"maintainability {metrics.maintainability}/100",
    ]
    if analysis.functions:
        parts.append("- Callables:")
        for function in analysis.functions[:12]:
            note = f"{function.complexity_class}"
            if function.is_recursive:
                note += ", recursive"
            parts.append(
                f"    line {function.line}: {function.kind} `{function.name}` "
                f"({function.param_count} params, cyclomatic {function.cyclomatic}, {note})"
            )
    if analysis.concepts:
        parts.append(
            "- Concepts detected: "
            + ", ".join(f"{c.label} (x{c.count})" for c in analysis.concepts[:10])
        )
    if analysis.findings:
        parts.append("- Findings already reported (do not repeat):")
        for finding in analysis.findings[:8]:
            location = f"line {finding.span.start_line}" if finding.span else "file"
            parts.append(f"    {location}: [{finding.severity}] {finding.title}")
    if analysis.imports:
        parts.append("- Imports: " + ", ".join(analysis.imports[:10]))

    lines = source.splitlines()[:MAX_LINES_SENT]
    numbered = "\n".join(f"{index + 1:4d} | {line}" for index, line in enumerate(lines))
    parts += ["", "SOURCE:", numbered]
    if len(source.splitlines()) > MAX_LINES_SENT:
        parts.append(f"... ({len(source.splitlines()) - MAX_LINES_SENT} more lines omitted)")
    return "\n".join(parts)


def _validate(payload: Any, line_count: int) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    """Schema-shaped payload -> (summary, lines, risks). Raises on anything unusable."""
    if not isinstance(payload, dict):
        raise EnrichmentError("model returned a non-object")
    summary = str(payload.get("summary") or "").strip()
    raw_lines = payload.get("lines")
    lines: list[dict[str, Any]] = []
    if isinstance(raw_lines, list):
        for item in raw_lines[:MAX_ENRICHED_LINES]:
            if not isinstance(item, dict):
                continue
            try:
                number = int(item["line"])
            except (KeyError, TypeError, ValueError):
                continue
            text = str(item.get("text") or "").strip()
            # A line number outside the file means the model lost track of the source.
            if not text or not (1 <= number <= line_count):
                continue
            confidence = item.get("confidence", 0.6)
            try:
                confidence = max(0.0, min(1.0, float(confidence)))
            except (TypeError, ValueError):
                confidence = 0.6
            lines.append({"line": number, "text": text, "confidence": confidence})
    risks: list[dict[str, Any]] = []
    raw_risks = payload.get("risks")
    if isinstance(raw_risks, list):
        for item in raw_risks[:10]:
            if isinstance(item, dict) and item.get("text"):
                try:
                    risks.append({"line": int(item.get("line", 0)), "text": str(item["text"])})
                except (TypeError, ValueError):
                    continue
    if not summary and not lines:
        raise EnrichmentError("model returned nothing usable")
    return summary, lines, risks


def _to_annotations(lines: list[dict[str, Any]], level: Level, source: str) -> list[Annotation]:
    source_lines = source.splitlines()
    out: list[Annotation] = []
    for item in lines:
        number = item["line"]
        text_of_line = source_lines[number - 1] if number <= len(source_lines) else ""
        indent = len(text_of_line) - len(text_of_line.lstrip())
        out.append(
            Annotation(
                span=Span(number, indent, number, max(len(text_of_line), indent + 1)),
                kind=Kind.UNKNOWN,
                texts={level: item["text"]},
                source=Source.LLM,
                confidence=item["confidence"],
            )
        )
    return out


def _extract_json(text: str) -> Any:
    """Parse a JSON body that may still be wrapped in a fenced block."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Last resort: the outermost {...} in the reply.
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


# -- providers ----------------------------------------------------------------------


class Provider(Protocol):
    name: str
    model: str

    def available(self) -> bool: ...

    def complete(self, system: str, prompt: str) -> Any: ...

    def stream(self, system: str, prompt: str) -> Iterator[str]: ...


class AnthropicProvider:
    """Claude via the official SDK, with schema-constrained output."""

    name = "anthropic"

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.environ.get("EMC_ANTHROPIC_MODEL", "claude-opus-5")
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError as exc:  # pragma: no cover
                raise EnrichmentError("the `anthropic` package is not installed") from exc
            self._client = Anthropic()
        return self._client

    def available(self) -> bool:
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            # An `ant auth login` profile also works, so absence of the env var is not
            # proof of no credentials: only that we cannot confirm them cheaply.
            return _anthropic_profile_exists()
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return True

    def complete(self, system: str, prompt: str) -> Any:
        client = self._get_client()
        response = client.messages.create(
            model=self.model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
        )
        if response.stop_reason == "refusal":
            raise EnrichmentError("the model declined to answer this request")
        text = next((b.text for b in response.content if b.type == "text"), "")
        if not text:
            raise EnrichmentError("empty response")
        return _extract_json(text)

    def stream(self, system: str, prompt: str) -> Iterator[str]:
        client = self._get_client()
        with client.messages.stream(
            model=self.model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
        ) as stream:
            yield from stream.text_stream


def _anthropic_profile_exists() -> bool:
    from pathlib import Path

    config = os.environ.get("ANTHROPIC_CONFIG_DIR") or os.path.expanduser("~/.config/anthropic")
    return Path(config, "credentials").is_dir()


class GeminiProvider:
    """Gemini via the REST API: kept from v1 so existing deployments keep working.

    Google retires model IDs on a schedule, and a pinned one turns into a 404 with no
    warning: v1 shipped `gemini-2.0-flash` and simply stopped working when it was shut
    down. So a 404 here is treated as a recoverable condition. The provider asks the
    API which models exist and retries once against a current one, rather than handing
    the user a dead model name.
    """

    name = "gemini"
    ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"
    # An alias rather than a pinned version: pinning is what broke v1 when
    # gemini-2.0-flash was shut down. Confirmed live against the production key.
    DEFAULT_MODEL = "gemini-flash-latest"
    #: Preference order when recovering from a retired model.
    PREFERRED = ("flash-latest", "3.7-flash", "3.5-flash", "2.5-flash", "flash", "pro")

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.environ.get("EMC_GEMINI_MODEL", self.DEFAULT_MODEL)

    def available(self) -> bool:
        return bool(os.environ.get("GEMINI_API_KEY"))

    def list_models(self) -> list[str]:
        """Model IDs on this key that can serve generateContent."""
        import httpx

        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            return []
        try:
            response = httpx.get(f"{self.ENDPOINT}?key={key}&pageSize=200", timeout=30.0)
            response.raise_for_status()
        except httpx.HTTPError:
            return []
        out = []
        for entry in response.json().get("models", []):
            if "generateContent" in entry.get("supportedGenerationMethods", []):
                out.append(str(entry.get("name", "")).removeprefix("models/"))
        return out

    def _pick_model(self) -> str | None:
        """Best current stand-in for a retired model."""
        candidates = [m for m in self.list_models() if "flash" in m or "pro" in m]
        if not candidates:
            return None
        for token in self.PREFERRED:
            for candidate in candidates:
                if candidate.endswith(token) and "preview" not in candidate:
                    return candidate
        stable = [c for c in candidates if "preview" not in c and "exp" not in c]
        return (stable or candidates)[0]

    def _payload(self, system: str, prompt: str) -> dict[str, Any]:
        return {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": _gemini_schema(RESPONSE_SCHEMA),
                "temperature": 0.4,
            },
        }

    def complete(self, system: str, prompt: str) -> Any:
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise EnrichmentError("GEMINI_API_KEY is not set")

        response = self._post(system, prompt, key, self.model)

        # 503 ("high demand") and 429 are transient upstream states, not failures of
        # this request. Retry a couple of times before giving up on the whole pass.
        for attempt in range(2):
            if response.status_code not in (429, 503):
                break
            time.sleep(1.5 * (attempt + 1))
            response = self._post(system, prompt, key, self.model)

        if response.status_code == 404:
            # The configured model was retired. Find a live one and say which, so the
            # deployment can be pinned deliberately instead of drifting again.
            replacement = self._pick_model()
            if replacement is None or replacement == self.model:
                available = ", ".join(self.list_models()[:8]) or "none returned"
                raise EnrichmentError(
                    f"Gemini model '{self.model}' no longer exists and no replacement "
                    f"was found. Set EMC_GEMINI_MODEL to one of: {available}"
                )
            self.model = replacement
            response = self._post(system, prompt, key, replacement)

        if response.status_code == 429:
            raise EnrichmentError("Gemini is rate limiting: try again shortly")
        if response.status_code >= 400:
            detail = ""
            with contextlib.suppress(ValueError):
                detail = response.json().get("error", {}).get("message", "")[:160]
            raise EnrichmentError(f"Gemini returned {response.status_code}. {detail}".strip())

        data = response.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise EnrichmentError("unexpected Gemini response shape") from exc
        return _extract_json(text)

    def _post(self, system: str, prompt: str, key: str, model: str) -> Any:
        import httpx

        url = f"{self.ENDPOINT}/{model}:generateContent?key={key}"
        try:
            return httpx.post(url, json=self._payload(system, prompt), timeout=60.0)
        except httpx.HTTPError as exc:
            raise EnrichmentError(f"network error talking to Gemini: {exc}") from exc

    def stream(self, system: str, prompt: str) -> Iterator[str]:
        import httpx

        key = os.environ.get("GEMINI_API_KEY")
        url = f"{self.ENDPOINT}/{self.model}:streamGenerateContent?alt=sse&key={key}"
        with httpx.stream(
            "POST", url, json=self._payload(system, prompt), timeout=120.0
        ) as response:
            for line in response.iter_lines():
                if not line.startswith("data:"):
                    continue
                try:
                    chunk = json.loads(line[5:].strip())
                    yield chunk["candidates"][0]["content"]["parts"][0]["text"]
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue


def _gemini_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Gemini's schema dialect rejects `additionalProperties` and lowercases types."""
    out: dict[str, Any] = {}
    for key, value in schema.items():
        if key == "additionalProperties":
            continue
        if key == "type" and isinstance(value, str):
            out["type"] = value.upper()
        elif isinstance(value, dict):
            out[key] = _gemini_schema(value)
        elif key == "properties" and isinstance(value, dict):
            out[key] = {k: _gemini_schema(v) for k, v in value.items()}
        else:
            out[key] = value
    return out


PROVIDERS: dict[str, type[Provider]] = {
    "anthropic": AnthropicProvider,  # type: ignore[dict-item]
    "gemini": GeminiProvider,  # type: ignore[dict-item]
}


def get_provider(name: str | None = None) -> Provider | None:
    """The requested provider, or the first configured one."""
    if name:
        factory = PROVIDERS.get(name)
        if factory is None:
            return None
        provider = factory()
        return provider if provider.available() else None
    preferred = os.environ.get("EMC_PROVIDER")
    order = [preferred] if preferred else ["anthropic", "gemini"]
    for candidate in order:
        factory = PROVIDERS.get(candidate or "")
        if factory is None:
            continue
        provider = factory()
        if provider.available():
            return provider
    return None


def available_providers() -> list[dict[str, Any]]:
    out = []
    for name, factory in PROVIDERS.items():
        provider = factory()
        out.append({"id": name, "model": provider.model, "available": provider.available()})
    return out


# -- entry point --------------------------------------------------------------------


def enrich(
    source: str,
    analysis: Analysis,
    level: Level,
    *,
    provider: Provider | str | None = None,
    cache: Cache | None = None,
) -> Enrichment:
    """Run the enrichment pass. Returns an `Enrichment` with `error` set on failure;
    callers keep the static explanation either way."""
    resolved = provider if not isinstance(provider, (str, type(None))) else get_provider(provider)
    if resolved is None:
        return Enrichment(summary="", error="no LLM provider is configured")

    cache = cache or default_cache()
    key = cache_key(
        source=source,
        language=analysis.language.value,
        level=level.value,
        provider=resolved.name,
        model=resolved.model,
    )
    hit = cache.get(key)
    if hit is not None:
        summary, lines, risks = _validate(hit, len(source.splitlines()))
        return Enrichment(
            summary=summary,
            annotations=_to_annotations(lines, level, source),
            risks=risks,
            provider=resolved.name,
            model=resolved.model,
            cached=True,
        )

    prompt = build_context(analysis, level, source)
    try:
        payload = resolved.complete(SYSTEM_PROMPT, prompt)
        summary, lines, risks = _validate(payload, len(source.splitlines()))
    except EnrichmentError as exc:
        return Enrichment(summary="", provider=resolved.name, model=resolved.model, error=str(exc))
    except Exception as exc:  # pragma: no cover - provider SDKs raise their own types
        return Enrichment(
            summary="",
            provider=resolved.name,
            model=resolved.model,
            error=f"{type(exc).__name__}: {exc}",
        )

    cache.set(key, payload)
    return Enrichment(
        summary=summary,
        annotations=_to_annotations(lines, level, source),
        risks=risks,
        provider=resolved.name,
        model=resolved.model,
    )


def merge(
    static_annotations: list[Annotation], enrichment: Enrichment
) -> list[Annotation]:
    """Layer LLM annotations over the static ones.

    Static annotations always survive. The model supplements the parse tree, it never
    replaces it. Where both describe a line, both are kept and the UI shows the source.
    """
    if not enrichment.ok or not enrichment.annotations:
        return static_annotations
    combined = [*static_annotations, *enrichment.annotations]
    combined.sort(key=lambda a: (a.span.start_line, a.source is Source.LLM))
    return combined
