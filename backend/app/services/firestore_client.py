"""Firestore-compatible in-memory store for local dev/tests.

Public interface (.set/.get/.list/.delete_all) is designed to be a drop-in
replacement for google.cloud.firestore.Client() in production.
"""
from typing import Any, Optional

_memory_store: dict[str, dict[str, dict[str, Any]]] = {
    "users": {}, "profiles": {}, "crisis_events": {},
    "caregiver_alerts": {}, "checkins": {},
}


class FirestoreClient:
    def collection(self, name: str):
        return _CollectionProxy(name)


class _CollectionProxy:
    def __init__(self, name: str):
        self._name = name

    def set(self, doc_id: str, data: dict[str, Any]) -> None:
        _memory_store.setdefault(self._name, {})[doc_id] = data

    def get(self, doc_id: str) -> Optional[dict[str, Any]]:
        return _memory_store.get(self._name, {}).get(doc_id)

    def list(self) -> list[dict[str, Any]]:
        return list(_memory_store.get(self._name, {}).values())

    def delete_all(self) -> None:
        _memory_store[self._name] = {}


def get_firestore_client() -> FirestoreClient:
    return FirestoreClient()
