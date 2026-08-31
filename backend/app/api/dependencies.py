from functools import lru_cache

from app.core.config import get_settings
from app.services.lichess import LichessService
from app.services.stockfish import StockfishService
from app.services.vector_store import VectorStoreService
from app.services.videos import VideoService
from app.workflows.opening_agent import OpeningAgentWorkflow


@lru_cache
def get_lichess_service() -> LichessService:
    return LichessService(get_settings())


@lru_cache
def get_stockfish_service() -> StockfishService:
    return StockfishService(get_settings())


@lru_cache
def get_vector_store_service() -> VectorStoreService:
    return VectorStoreService(get_settings())


@lru_cache
def get_video_service() -> VideoService:
    return VideoService(get_settings())


@lru_cache
def get_agent_workflow() -> OpeningAgentWorkflow:
    return OpeningAgentWorkflow(
        get_lichess_service(),
        get_stockfish_service(),
        get_vector_store_service(),
        get_video_service(),
    )


async def provide_settings():
    return get_settings()


async def provide_lichess_service():
    return get_lichess_service()


async def provide_stockfish_service():
    return get_stockfish_service()


async def provide_vector_store_service():
    return get_vector_store_service()


async def provide_video_service():
    return get_video_service()


async def provide_agent_workflow():
    return get_agent_workflow()
