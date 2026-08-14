"""Content-addressed cache for enrichment results.

Keyed on everything that can change the answer — source, language, level, provider,
model, and a schema version — so a prompt change or a model swap never serves a stale
explanation. In-memory LRU by default, with an optional disk tier for the deployed
service where a cold instance would otherwise re-pay for every popular snippet.
"""

from __future__ import annotations

import json
import os
import time
from collections import OrderedDict
from hashlib import blake2b
from pathlib import Path
from threading import Lock
from typing import Any

#: Bump when the prompt or the response schema changes.
SCHEMA_VERSION = 3

DEFAULT_CAPACITY = 256
DEFAULT_TTL_SECONDS = 60 * 60 * 24


def cache_key(**parts: Any) -> str:
    payload = json.dumps({**parts, "v": SCHEMA_VERSION}, sort_keys=True, default=str)
    return blake2b(payload.encode("utf-8"), digest_size=16).hexdigest()


class Cache:
    """LRU with a TTL, optionally mirrored to disk."""

    def __init__(
        self,
        capacity: int = DEFAULT_CAPACITY,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        directory: str | os.PathLike[str] | None = None,
    ) -> None:
        self.capacity = capacity
        self.ttl = ttl_seconds
        self._entries: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = Lock()
        self.directory = Path(directory) if directory else None
        if self.directory:
            self.directory.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Any | None:
        now = time.time()
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                stored_at, value = entry
                if now - stored_at <= self.ttl:
                    self._entries.move_to_end(key)
                    self.hits += 1
                    return value
                del self._entries[key]

        value = self._read_disk(key, now)
        if value is not None:
            with self._lock:
                self._entries[key] = (now, value)
                self._evict()
            self.hits += 1
            return value

        self.misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        now = time.time()
        with self._lock:
            self._entries[key] = (now, value)
            self._entries.move_to_end(key)
            self._evict()
        self._write_disk(key, value)

    def _evict(self) -> None:
        while len(self._entries) > self.capacity:
            self._entries.popitem(last=False)

    def _path(self, key: str) -> Path | None:
        return self.directory / f"{key}.json" if self.directory else None

    def _read_disk(self, key: str, now: float) -> Any | None:
        path = self._path(key)
        if path is None or not path.exists():
            return None
        try:
            if now - path.stat().st_mtime > self.ttl:
                path.unlink(missing_ok=True)
                return None
            return json.loads(path.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _write_disk(self, key: str, value: Any) -> None:
        path = self._path(key)
        if path is None:
            return
        try:
            # Write-then-rename so a crashed write never leaves half a JSON document
            # that the next reader would treat as a cache hit.
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(value), "utf-8")
            temporary.replace(path)
        except (OSError, TypeError):
            pass

    @property
    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "entries": len(self._entries),
            "capacity": self.capacity,
            "hits": self.hits,
            "misses": self.misses,
            "hitRate": round(self.hits / total, 3) if total else 0.0,
            "persistent": self.directory is not None,
        }

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


_default: Cache | None = None


def default_cache() -> Cache:
    global _default
    if _default is None:
        _default = Cache(directory=os.environ.get("EMC_CACHE_DIR") or None)
    return _default
