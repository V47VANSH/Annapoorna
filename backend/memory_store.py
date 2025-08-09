"""In-memory stand-in for MongoDB, used when no database is reachable.

Supports only what database.py uses: equality filters, sorting and $set
updates. Data is lost on restart.
"""

from __future__ import annotations

import threading
from typing import Any

from bson import ObjectId

SortSpec = list[tuple[str, int]]


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    """Equality-only filter matching, which is all this app's queries need."""
    return all(document.get(field) == value for field, value in query.items())


def _sorted(documents: list[dict], sort: SortSpec | None) -> list[dict]:
    if not sort:
        return documents
    result = list(documents)
    # sort by the last key first so the first key wins, like Mongo
    for field, direction in reversed(sort):
        result.sort(
            key=lambda doc: (doc.get(field) is None, doc.get(field)),
            reverse=direction < 0,
        )
    return result


class _Cursor:
    """The small slice of pymongo's cursor API that database.py relies on."""

    def __init__(self, documents: list[dict]):
        self._documents = documents

    def sort(self, key: str | SortSpec, direction: int = 1) -> _Cursor:
        sort: SortSpec = [(key, direction)] if isinstance(key, str) else list(key)
        return _Cursor(_sorted(self._documents, sort))

    def limit(self, count: int) -> _Cursor:
        return _Cursor(self._documents[:count])

    def __iter__(self):
        return iter(self._documents)

    def __len__(self) -> int:
        return len(self._documents)


class _InsertOneResult:
    def __init__(self, inserted_id: ObjectId):
        self.inserted_id = inserted_id


class _UpdateResult:
    def __init__(self, matched_count: int):
        self.matched_count = matched_count
        self.modified_count = matched_count


class InMemoryCollection:
    """A dict-backed collection with a pymongo-compatible surface."""

    def __init__(self, name: str):
        self.name = name
        self._documents: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    # projection is ignored, callers only read fields with .get()
    def find_one(
        self,
        query: dict[str, Any] | None = None,
        projection: Any = None,
        sort: SortSpec | None = None,
    ) -> dict[str, Any] | None:
        query = query or {}
        with self._lock:
            candidates = [doc for doc in self._documents if _matches(doc, query)]
        candidates = _sorted(candidates, sort)
        return dict(candidates[0]) if candidates else None

    def find(
        self, query: dict[str, Any] | None = None, projection: Any = None
    ) -> _Cursor:
        query = query or {}
        with self._lock:
            return _Cursor(
                [dict(doc) for doc in self._documents if _matches(doc, query)]
            )

    def insert_one(self, document: dict[str, Any]) -> _InsertOneResult:
        stored = dict(document)
        stored.setdefault("_id", ObjectId())
        with self._lock:
            self._documents.append(stored)
        return _InsertOneResult(stored["_id"])

    def update_one(
        self, query: dict[str, Any], update: dict[str, Any], upsert: bool = False
    ) -> _UpdateResult:
        changes = update.get("$set", {})
        with self._lock:
            for document in self._documents:
                if _matches(document, query):
                    document.update(changes)
                    return _UpdateResult(1)

            if upsert:
                stored = {**query, **changes}
                stored.setdefault("_id", ObjectId())
                self._documents.append(stored)
        return _UpdateResult(0)

    def count_documents(self, query: dict[str, Any] | None = None) -> int:
        query = query or {}
        with self._lock:
            return sum(1 for doc in self._documents if _matches(doc, query))

    def delete_many(self, query: dict[str, Any] | None = None) -> None:
        query = query or {}
        with self._lock:
            self._documents = [
                doc for doc in self._documents if not _matches(doc, query)
            ]

    # no-op, kept so database.py can call it
    def create_index(self, *args: Any, **kwargs: Any) -> None:
        return None


class InMemoryDatabase:
    """Hands out collections by name, creating them on first use."""

    def __init__(self):
        self._collections: dict[str, InMemoryCollection] = {}
        self._lock = threading.Lock()

    def __getitem__(self, name: str) -> InMemoryCollection:
        with self._lock:
            if name not in self._collections:
                self._collections[name] = InMemoryCollection(name)
            return self._collections[name]
