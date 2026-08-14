"""Runs every analysis pass over one parse result and returns a single `Analysis`.

Order matters in one place: the call graph must exist before complexity estimation,
because "is this recursive?" changes the asymptotic answer entirely.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from explain_my_code.analysis.callgraph import CallGraph, build_call_graph
from explain_my_code.analysis.complexity import estimate
from explain_my_code.analysis.concepts import ConceptHit, concept_hit, detect_concepts
from explain_my_code.analysis.findings import Finding, collect_findings
from explain_my_code.analysis.metrics import (
    FileMetrics,
    FunctionMetrics,
    cognitive_of,
    cyclomatic_of,
    file_metrics,
    halstead_of,
    max_nesting_of,
)
from explain_my_code.analysis.symbols import SymbolTable, build_symbol_table
from explain_my_code.ir import CALLABLE_KINDS, Kind, Language, Node, ParseResult


@dataclass(slots=True)
class Analysis:
    language: Language
    parser: str
    degraded: bool
    root: Node
    metrics: FileMetrics
    functions: list[FunctionMetrics]
    call_graph: CallGraph
    symbols: SymbolTable
    concepts: list[ConceptHit]
    findings: list[Finding]
    imports: list[str] = field(default_factory=list)

    @property
    def hotspot(self) -> FunctionMetrics | None:
        """The function most worth looking at first."""
        if not self.functions:
            return None
        return max(self.functions, key=lambda f: (f.cognitive, f.cyclomatic, f.lines))

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language.value,
            "parser": self.parser,
            "degraded": self.degraded,
            "metrics": self.metrics.to_dict(),
            "functions": [f.to_dict() for f in self.functions],
            "callGraph": self.call_graph.to_dict(),
            "symbols": self.symbols.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
            "imports": self.imports,
            "hotspot": self.hotspot.name if self.hotspot else None,
        }


def _function_metrics(node: Node, graph: CallGraph) -> FunctionMetrics:
    qualified = node.qualified_name or (node.name or "<anonymous>")
    full_span = node.meta.get("full_span") or {}
    start_line = int(full_span.get("startLine", node.span.start_line))
    end_line = int(full_span.get("endLine", node.span.end_line))
    is_recursive = graph.is_recursive(qualified)
    estimate_result = estimate(node, is_recursive=is_recursive)
    return FunctionMetrics(
        name=node.name or "<anonymous>",
        qualified_name=qualified,
        node_id=node.id,
        line=start_line,
        end_line=end_line,
        kind=node.kind.value,
        param_count=int(node.meta.get("param_count", 0)),
        lines=max(end_line - start_line + 1, 1),
        cyclomatic=cyclomatic_of(node),
        cognitive=cognitive_of(node),
        max_nesting=max_nesting_of(node),
        halstead=halstead_of(node),
        calls=graph.edges.get(qualified, []),
        is_recursive=is_recursive,
        complexity_class=estimate_result.label,
        complexity_reason=estimate_result.reason,
        is_async=bool(node.meta.get("is_async")),
        is_generator=bool(node.meta.get("is_generator")),
    )


def analyze(parsed: ParseResult) -> Analysis:
    root = parsed.root
    graph = build_call_graph(root)
    callables = [n for n in root.walk() if n.kind in CALLABLE_KINDS]
    functions = [_function_metrics(node, graph) for node in callables]
    symbols = build_symbol_table(root)

    concepts = detect_concepts(root, parsed.language)
    recursive_nodes = [
        node
        for node in callables
        if graph.is_recursive(node.qualified_name or (node.name or ""))
    ]
    recursion = concept_hit("recursion", recursive_nodes)
    if recursion is not None:
        concepts.insert(0, recursion)

    findings = collect_findings(root, parsed.language, functions, symbols)

    imports = []
    for node in root.find(Kind.IMPORT):
        module = str(node.meta.get("module") or node.name or "")
        if module and module not in imports:
            imports.append(module)

    return Analysis(
        language=parsed.language,
        parser=parsed.parser,
        degraded=parsed.degraded,
        root=root,
        metrics=file_metrics(root, parsed.source),
        functions=functions,
        call_graph=graph,
        symbols=symbols,
        concepts=concepts,
        findings=findings,
        imports=imports[:20],
    )
