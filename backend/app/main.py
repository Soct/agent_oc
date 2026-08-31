from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import provide_vector_store_service
from app.api.routes import router
from app.core.config import get_settings
from app.schemas import VectorSearchRequest, VectorSearchResponse
from app.services.vector_store import VectorStoreService

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="POC pédagogique de recommandation d'ouvertures d'échecs.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"message": "FFE Opening Coach", "documentation": "/docs"}


@app.post("/vector-search", response_model=VectorSearchResponse, tags=["contexte"])
async def unversioned_vector_search(
    request: VectorSearchRequest,
    service: Annotated[VectorStoreService, Depends(provide_vector_store_service)],
) -> VectorSearchResponse:
    """Alias conservé pour correspondre mot pour mot au livrable demandé."""

    return await service.search(request.query, request.limit)
