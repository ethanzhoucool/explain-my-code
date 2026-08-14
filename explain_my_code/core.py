"""The one entry point everything else calls: `explain(code, ...)`.

The API, the CLI and the web UI are all thin wrappers over this function, so they can
never drift in what they report.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

from explain_my_code.adapters.base import get_adapter, load_all, registered_languages
from explain_my_code.analysis.pipeline import Analysis, analyze
from explain_my_code.ir import Annotation, Diagnostic, Language, Level, ParseResult
from explain_my_code.narrate.annotate import LineExplanation, annotate, line_view, summarize

load_all()

MAX_SOURCE_BYTES = 200_000

EXTENSIONS = {
    ".py": Language.PYTHON, ".pyi": Language.PYTHON,
    ".js": Language.JAVASCRIPT, ".mjs": Language.JAVASCRIPT, ".cjs": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT, ".ts": Language.JAVASCRIPT, ".tsx": Language.JAVASCRIPT,
    ".java": Language.JAVA,
    ".cpp": Language.CPP, ".cc": Language.CPP, ".cxx": Language.CPP, ".c": Language.CPP,
    ".h": Language.CPP, ".hpp": Language.CPP, ".hh": Language.CPP,
    ".sql": Language.SQL,
}

#: (pattern, language, weight). Weighted because single keywords overlap heavily —
#: `class` says nothing, `def foo(self)` and `#include <` say a great deal.
SIGNATURES: list[tuple[re.Pattern[str], Language, int]] = [
    (re.compile(r"^\s*def\s+\w+\s*\(.*\)\s*(->.*)?:", re.M), Language.PYTHON, 5),
    (re.compile(r"^\s*(from\s+[\w.]+\s+)?import\s+\w+", re.M), Language.PYTHON, 3),
    (re.compile(r"^\s*(async\s+)?def\s|self\.", re.M), Language.PYTHON, 2),
    (re.compile(r'^\s*(elif|print\()', re.M), Language.PYTHON, 2),
    (re.compile(r"#include\s*[<\"]", re.M), Language.CPP, 6),
    (re.compile(r"\bstd::\w+|->\s*\w+\(|::\w+\s*\(", re.M), Language.CPP, 4),
    (re.compile(r"\b(nullptr|template\s*<|namespace\s+\w+)", re.M), Language.CPP, 4),
    (re.compile(r"^\s*(public|private|protected)\s+(static\s+)?(class|void|int|final)", re.M), Language.JAVA, 5),
    (re.compile(r"\bSystem\.out\.print|\bpublic\s+static\s+void\s+main", re.M), Language.JAVA, 6),
    (re.compile(r"^\s*package\s+[\w.]+;|^\s*import\s+java", re.M), Language.JAVA, 5),
    (re.compile(r"@Override|\bnew\s+\w+<.*>\(", re.M), Language.JAVA, 3),
    (re.compile(r"\b(const|let|var)\s+\w+\s*=", re.M), Language.JAVASCRIPT, 4),
    (re.compile(r"=>\s*[{(]|\bfunction\s*\w*\s*\(", re.M), Language.JAVASCRIPT, 3),
    (re.compile(r"\bconsole\.(log|error|warn)\b|\brequire\(|\bexport\s+(default|const)", re.M), Language.JAVASCRIPT, 5),
    (re.compile(r"^\s*(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|WITH|CREATE\s+TABLE)\b", re.M | re.I), Language.SQL, 7),
    (re.compile(r"\b(LEFT\s+JOIN|INNER\s+JOIN|GROUP\s+BY|ORDER\s+BY)\b", re.M | re.I), Language.SQL, 4),
]


@dataclass(slots=True)
class DetectionResult:
    language: Language
    confidence: float
    runner_up: Language | None = None


def detect_language(code: str, filename: str | None = None) -> DetectionResult:
    """Guess the language from the source, or from a filename when one is given."""
    if filename:
        for extension, language in EXTENSIONS.items():
            if filename.lower().endswith(extension):
                return DetectionResult(language, 1.0)

    scores: dict[Language, int] = dict.fromkeys(Language, 0)
    for pattern, language, weight in SIGNATURES:
        matches = len(pattern.findall(code))
        if matches:
            scores[language] += weight * min(matches, 3)

    ranked = sorted(scores.items(), key=lambda item: -item[1])
    best, best_score = ranked[0]
    second, second_score = ranked[1] if len(ranked) > 1 else (None, 0)
    if best_score == 0:
        return DetectionResult(Language.PYTHON, 0.0)
    total = best_score + second_score
    return DetectionResult(best, round(best_score / total, 2) if total else 1.0, second)


@dataclass(slots=True)
class Explanation:
    language: Language
    level: Level
    source: str
    summary: str
    lines: list[LineExplanation]
    annotations: list[Annotation]
    analysis: Analysis
    diagnostics: list[Diagnostic] = field(default_factory=list)
    detection_confidence: float = 1.0
    timings_ms: dict[str, float] = field(default_factory=dict)
    enrichment: Any = None

    def to_dict(self, *, include_ir: bool = False) -> dict[str, Any]:
        out: dict[str, Any] = {
            "language": self.language.value,
            "level": self.level.value,
            "parser": self.analysis.parser,
            "degraded": self.analysis.degraded,
            "summary": self.summary,
            "lines": [line.to_dict() for line in self.lines],
            "annotations": [a.to_dict(self.level) for a in self.annotations],
            "concepts": [c.to_dict(self.level) for c in self.analysis.concepts],
            "analysis": self.analysis.to_dict(),
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "detectionConfidence": self.detection_confidence,
            "timingsMs": {k: round(v, 2) for k, v in self.timings_ms.items()},
        }
        if self.enrichment is not None:
            out["enrichment"] = self.enrichment.to_dict()
        if include_ir:
            out["ir"] = self.analysis.root.to_dict()
        return out


class SourceTooLarge(ValueError):
    pass


def explain(
    code: str,
    language: Language | str | None = None,
    level: Level | str = Level.BEGINNER,
    *,
    filename: str | None = None,
    enrich: bool | str = False,
) -> Explanation:
    """Parse, analyse and narrate `code`. Never raises on malformed input.

    `enrich` opts into the LLM layer — True for the default provider, or a provider
    name. A failed enrichment is reported on the result, never raised: the static
    explanation is always complete on its own.
    """
    if len(code.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise SourceTooLarge(
            f"Source is larger than {MAX_SOURCE_BYTES // 1000}KB. Explain one file at a time."
        )

    level = Level(level) if not isinstance(level, Level) else level
    confidence = 1.0
    if language is None:
        detected = detect_language(code, filename)
        language, confidence = detected.language, detected.confidence
    elif not isinstance(language, Language):
        language = Language(language)

    timings: dict[str, float] = {}

    started = time.perf_counter()
    parsed: ParseResult = get_adapter(language).parse(code)
    timings["parse"] = (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    analysis = analyze(parsed)
    timings["analyze"] = (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    annotations = annotate(parsed, analysis, level)
    summary = summarize(analysis, level)
    timings["explain"] = (time.perf_counter() - started) * 1000

    enrichment = None
    if enrich:
        from explain_my_code.narrate.llm import enrich as run_enrichment
        from explain_my_code.narrate.llm import merge

        started = time.perf_counter()
        enrichment = run_enrichment(
            code, analysis, level, provider=enrich if isinstance(enrich, str) else None
        )
        if enrichment.ok:
            annotations = merge(annotations, enrichment)
            if enrichment.summary:
                summary = f"{summary}\n\n{enrichment.summary}"
        timings["enrich"] = (time.perf_counter() - started) * 1000

    lines = line_view(annotations, level)
    timings["total"] = sum(timings.values())

    return Explanation(
        language=language,
        level=level,
        source=code,
        summary=summary,
        lines=lines,
        annotations=annotations,
        analysis=analysis,
        diagnostics=parsed.diagnostics,
        detection_confidence=confidence,
        timings_ms=timings,
        enrichment=enrichment,
    )


def supported_languages() -> list[dict[str, Any]]:
    out = []
    for language in registered_languages():
        adapter = get_adapter(language)
        out.append(
            {
                "id": language.value,
                "parser": adapter.parser_name,
                "available": adapter.available(),
                "extensions": [e for e, lang in EXTENSIONS.items() if lang is language],
            }
        )
    return out
