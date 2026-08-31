from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    provide_agent_workflow,
    provide_lichess_service,
    provide_settings,
    provide_stockfish_service,
    provide_vector_store_service,
    provide_video_service,
)
from app.core.config import Settings
from app.schemas import (
    AgentRequest,
    AgentResponse,
    EvaluationResponse,
    HealthResponse,
    MovesResponse,
    VectorSearchRequest,
    VectorSearchResponse,
    VideosResponse,
)
from app.services.chess_utils import validate_fen
from app.services.lichess import LichessService, LichessUnavailable
from app.services.stockfish import StockfishService, StockfishUnavailable
from app.services.vector_store import VectorStoreService
from app.services.videos import VideoService
from app.workflows.opening_agent import OpeningAgentWorkflow

router = APIRouter(prefix="/api/v1")
SettingsDep = Annotated[Settings, Depends(provide_settings)]
LichessDep = Annotated[LichessService, Depends(provide_lichess_service)]
StockfishDep = Annotated[StockfishService, Depends(provide_stockfish_service)]
VectorStoreDep = Annotated[VectorStoreService, Depends(provide_vector_store_service)]
VideoDep = Annotated[VideoService, Depends(provide_video_service)]
WorkflowDep = Annotated[OpeningAgentWorkflow, Depends(provide_agent_workflow)]


@router.get("/healthcheck", response_model=HealthResponse, tags=["système"])
async def healthcheck(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        service=settings.app_name,
        environment=settings.app_env,
        dependencies={
            "lichess": "configured" if settings.lichess_api_token else "token-missing",
            "stockfish": settings.stockfish_path,
            "mongodb": settings.mongodb_url,
            "milvus": settings.milvus_uri,
            "youtube": "configured" if settings.youtube_api_key else "demo-mode",
        },
    )


@router.get("/moves/{fen:path}", response_model=MovesResponse, tags=["échecs"])
async def theoretical_moves(
    fen: str,
    service: LichessDep,
) -> MovesResponse:
    valid_fen = validate_fen(fen)
    try:
        return await service.get_moves(valid_fen)
    except LichessUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("/evaluate/{fen:path}", response_model=EvaluationResponse, tags=["échecs"])
async def evaluate_position(
    fen: str,
    service: StockfishDep,
) -> EvaluationResponse:
    valid_fen = validate_fen(fen)
    try:
        return await service.evaluate(valid_fen)
    except StockfishUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post("/vector-search", response_model=VectorSearchResponse, tags=["contexte"])
async def vector_search(
    request: VectorSearchRequest,
    service: VectorStoreDep,
) -> VectorSearchResponse:
    return await service.search(request.query, request.limit)


@router.get("/videos/{opening}", response_model=VideosResponse, tags=["ressources"])
async def videos(
    opening: str,
    service: VideoDep,
) -> VideosResponse:
    return await service.search(opening)


@router.post("/agent/analyze", response_model=AgentResponse, tags=["agent"])
async def analyze(
    request: AgentRequest,
    workflow: WorkflowDep,
) -> AgentResponse:
    return await workflow.analyze(validate_fen(request.fen))
