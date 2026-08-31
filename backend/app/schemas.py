from typing import Any, Literal

from pydantic import BaseModel, Field


class OpeningInfo(BaseModel):
    eco: str | None = None
    name: str | None = None


class TheoryMove(BaseModel):
    uci: str
    san: str
    white: int = 0
    draws: int = 0
    black: int = 0
    average_rating: int | None = None
    popularity: int = 0


class MovesResponse(BaseModel):
    fen: str
    source: Literal["lichess"] = "lichess"
    opening: OpeningInfo | None = None
    moves: list[TheoryMove]


class EvaluationResponse(BaseModel):
    fen: str
    source: Literal["stockfish"] = "stockfish"
    centipawns: int | None
    mate_in: int | None = None
    best_move: str | None = None
    depth: int


class VectorSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=300)
    limit: int = Field(default=3, ge=1, le=10)


class ContextResult(BaseModel):
    title: str
    text: str
    source_url: str
    score: float


class VectorSearchResponse(BaseModel):
    query: str
    backend: Literal["milvus", "local-fallback"]
    results: list[ContextResult]


class VideoResult(BaseModel):
    video_id: str
    title: str
    channel: str
    thumbnail_url: str
    url: str
    published_at: str | None = None


class VideosResponse(BaseModel):
    opening: str
    source: Literal["youtube", "catalogue-demo", "mongodb-cache"]
    videos: list[VideoResult]
    notice: str | None = None


class AgentRequest(BaseModel):
    fen: str


class AgentResponse(BaseModel):
    fen: str
    route: Literal["theory", "engine"]
    summary: str
    opening: OpeningInfo | None = None
    suggested_moves: list[TheoryMove] = Field(default_factory=list)
    evaluation: EvaluationResponse | None = None
    context: list[ContextResult] = Field(default_factory=list)
    videos: list[VideoResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    environment: str
    dependencies: dict[str, Any]
