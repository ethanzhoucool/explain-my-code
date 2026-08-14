"""Adapter contract and registry.

An adapter's only job is `source -> ParseResult`. It must not explain anything: all
phrasing lives in `explain/phrasebook.py`, all measurement in `analysis/`. Keeping
adapters dumb is what stops the per-language rule-file duplication from growing back.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from explain_my_code.ir import Language, ParseResult


class Adapter(Protocol):
    language: Language
    #: Human-readable name of the underlying parser, shown in the API response.
    parser_name: str

    def available(self) -> bool:
        """False when an optional grammar wheel is missing, so the caller can degrade."""
        ...

    def parse(self, source: str) -> ParseResult: ...


_REGISTRY: dict[Language, Callable[[], Adapter]] = {}


def register(language: Language) -> Callable[[Callable[[], Adapter]], Callable[[], Adapter]]:
    def decorate(factory: Callable[[], Adapter]) -> Callable[[], Adapter]:
        _REGISTRY[language] = factory
        return factory

    return decorate


_cache: dict[Language, Adapter] = {}


def get_adapter(language: Language) -> Adapter:
    if language not in _cache:
        if language not in _REGISTRY:
            raise KeyError(f"no adapter registered for {language.value}")
        _cache[language] = _REGISTRY[language]()
    return _cache[language]


def registered_languages() -> list[Language]:
    return sorted(_REGISTRY, key=lambda lang: lang.value)


def load_all() -> None:
    """Import adapter modules for their registration side effects."""
    from explain_my_code.adapters import (  # noqa: F401
        cpp,
        java,
        javascript,
        python,
        sql,
    )
