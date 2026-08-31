from app.core.config import Settings
from app.services.vector_store import VectorStoreService


def test_local_vector_fallback_returns_relevant_opening() -> None:
    service = VectorStoreService(Settings())
    results = service._search_local("défense sicilienne pion c5", limit=2)
    assert results[0].title == "Défense sicilienne"
