import asyncio
import json
import math
import re
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.schemas import ContextResult, VectorSearchResponse


class VectorStoreService:
    """Recherche Milvus avec repli local pour une démonstration dégradée."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model: Any | None = None
        self._data_path = Path(__file__).parents[2] / "data" / "wikichess_openings.json"

    async def search(self, query: str, limit: int = 3) -> VectorSearchResponse:
        try:
            results = await asyncio.to_thread(self._search_milvus, query, limit)
            if results:
                return VectorSearchResponse(query=query, backend="milvus", results=results)
        except Exception:
            # Le repli est intentionnel : l'agent reste démontrable pendant le démarrage de Milvus.
            pass
        return VectorSearchResponse(
            query=query,
            backend="local-fallback",
            results=self._search_local(query, limit),
        )

    async def seed(self) -> int:
        return await asyncio.to_thread(self._seed_sync)

    def _get_model(self) -> Any:
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self.settings.embedding_model)
        return self._model

    def _embedding(self, text: str) -> list[float]:
        vector = next(self._get_model().embed([text]))
        return vector.tolist()

    def _client(self) -> Any:
        from pymilvus import MilvusClient

        return MilvusClient(uri=self.settings.milvus_uri)

    def _seed_sync(self) -> int:
        client = self._client()
        collection = self.settings.milvus_collection
        if client.has_collection(collection_name=collection):
            client.drop_collection(collection_name=collection)
        client.create_collection(
            collection_name=collection,
            dimension=self.settings.embedding_dimension,
            metric_type="COSINE",
            auto_id=True,
            enable_dynamic_field=True,
        )
        rows = []
        for chunk in self._load_data():
            rows.append({**chunk, "vector": self._embedding(chunk["text"])})
        client.insert(collection_name=collection, data=rows)
        return len(rows)

    def _search_milvus(self, query: str, limit: int) -> list[ContextResult]:
        client = self._client()
        collection = self.settings.milvus_collection
        if not client.has_collection(collection_name=collection):
            return []
        hits = client.search(
            collection_name=collection,
            data=[self._embedding(query)],
            limit=limit,
            output_fields=["title", "text", "source_url"],
        )[0]
        return [
            ContextResult(
                title=hit["entity"]["title"],
                text=hit["entity"]["text"],
                source_url=hit["entity"]["source_url"],
                score=round(float(hit["distance"]), 4),
            )
            for hit in hits
        ]

    def _load_data(self) -> list[dict[str, str]]:
        return json.loads(self._data_path.read_text(encoding="utf-8"))

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return set(re.findall(r"[a-zà-ÿ]{3,}", value.casefold()))

    def _search_local(self, query: str, limit: int) -> list[ContextResult]:
        query_tokens = self._tokens(query)
        scored: list[tuple[float, dict[str, str]]] = []
        for chunk in self._load_data():
            tokens = self._tokens(f"{chunk['title']} {chunk['text']}")
            overlap = len(query_tokens & tokens)
            score = overlap / math.sqrt(max(1, len(query_tokens) * len(tokens)))
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            ContextResult(
                title=chunk["title"],
                text=chunk["text"],
                source_url=chunk["source_url"],
                score=round(score, 4),
            )
            for score, chunk in scored[:limit]
        ]
