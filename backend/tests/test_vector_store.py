from app.core.config import Settings
from app.services.vector_store import VectorStoreService


def test_local_vector_fallback_returns_relevant_opening() -> None:
    service = VectorStoreService(Settings())
    results = service._search_local("sicilian defense pawn c5", limit=2)
    titles = [r.title for r in results]
    assert any("Sicilian" in t or "sicilian" in t.lower() for t in titles)


def test_local_vector_fallback_prioritizes_exact_opening_title() -> None:
    service = VectorStoreService(Settings())
    results = service._search_local("Polish Opening", limit=3)
    assert results[0].title == "A00 Polish (Sokolsky) opening"
