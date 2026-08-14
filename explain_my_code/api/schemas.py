"""Pydantic request/response models: also the OpenAPI contract at /docs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from explain_my_code.core import MAX_SOURCE_BYTES

LanguageId = Literal["python", "javascript", "java", "cpp", "sql"]
LevelId = Literal["eli5", "beginner", "developer"]


class ExplainRequest(BaseModel):
    code: str = Field(..., description="Source to explain.", min_length=1)
    language: LanguageId | None = Field(
        None, description="Omit to auto-detect from the source."
    )
    level: LevelId = Field("beginner", description="Audience the explanation is pitched at.")
    filename: str | None = Field(
        None, description="Used for language detection when `language` is omitted."
    )
    enrich: bool = Field(
        False, description="Run the optional LLM pass on top of the static analysis."
    )
    provider: Literal["anthropic", "gemini"] | None = Field(
        None, description="Which LLM provider to enrich with. Defaults to the configured one."
    )
    include_ir: bool = Field(
        False, alias="includeIr", description="Include the full IR tree in the response."
    )

    model_config = {"populate_by_name": True}

    @field_validator("code")
    @classmethod
    def _within_size_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_SOURCE_BYTES:
            raise ValueError(f"code exceeds the {MAX_SOURCE_BYTES // 1000}KB limit")
        return value


class AnalyzeRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: LanguageId | None = None
    filename: str | None = None

    model_config = {"populate_by_name": True}


class DetectRequest(BaseModel):
    code: str = Field(..., min_length=1)
    filename: str | None = None


class SpanModel(BaseModel):
    startLine: int
    startCol: int
    endLine: int
    endCol: int


class LineExplanationModel(BaseModel):
    line: int
    text: str
    kind: str
    source: str
    detail: str | None = None
    concepts: list[str] | None = None
    nodeId: int | None = None
    ai: str | None = None
    aiConfidence: float | None = None


class AnnotationModel(BaseModel):
    span: SpanModel
    kind: str
    source: str
    confidence: float
    text: str | None = None
    nodeId: int | None = None
    concepts: list[str] | None = None
    detail: str | None = None


class ConceptModel(BaseModel):
    id: str
    label: str
    category: str
    count: int
    lines: list[int]
    nodeIds: list[int]
    text: str | None = None


class FindingModel(BaseModel):
    rule: str
    title: str
    message: str
    severity: str
    line: int | None = None
    span: SpanModel | None = None
    suggestion: str | None = None


class ExplainResponse(BaseModel):
    language: str
    level: str
    parser: str
    degraded: bool
    summary: str
    lines: list[LineExplanationModel]
    annotations: list[AnnotationModel]
    concepts: list[ConceptModel]
    analysis: dict[str, Any]
    diagnostics: list[dict[str, Any]]
    detectionConfidence: float
    timingsMs: dict[str, float]
    enrichment: dict[str, Any] | None = None
    ir: dict[str, Any] | None = None


class LanguageInfo(BaseModel):
    id: str
    parser: str
    available: bool
    extensions: list[str]


class HealthResponse(BaseModel):
    status: str
    version: str
    languages: list[LanguageInfo]
    providers: list[dict[str, Any]]
    cache: dict[str, Any]


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
