from app.schemas import (
    ContextResult,
    EvaluationResponse,
    MovesResponse,
    OpeningInfo,
    TheoryMove,
    VectorSearchResponse,
    VideoResult,
    VideosResponse,
)
from app.workflows.opening_agent import OpeningAgentWorkflow

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class FakeLichess:
    def __init__(self, theoretical: bool) -> None:
        self.theoretical = theoretical

    async def get_moves(self, fen: str) -> MovesResponse:
        moves = [TheoryMove(uci="e2e4", san="e4", popularity=100)] if self.theoretical else []
        opening = OpeningInfo(eco="A00", name="Position initiale") if self.theoretical else None
        return MovesResponse(fen=fen, moves=moves, opening=opening)


class FakeStockfish:
    def __init__(self) -> None:
        self.calls = 0

    async def evaluate(self, fen: str) -> EvaluationResponse:
        self.calls += 1
        return EvaluationResponse(fen=fen, centipawns=24, best_move="e2e4", depth=12)


class FakeVectors:
    async def search(self, query: str, limit: int) -> VectorSearchResponse:
        result = ContextResult(
            title="Principes",
            text=query,
            source_url="https://example.test",
            score=1,
        )
        return VectorSearchResponse(query=query, backend="milvus", results=[result])


class FakeVideos:
    async def search(self, opening: str) -> VideosResponse:
        video = VideoResult(
            video_id="1",
            title=opening,
            channel="Test",
            thumbnail_url="",
            url="https://example.test/video",
        )
        return VideosResponse(opening=opening, source="youtube", videos=[video])


async def test_graph_uses_lichess_for_theoretical_position() -> None:
    stockfish = FakeStockfish()
    workflow = OpeningAgentWorkflow(FakeLichess(True), stockfish, FakeVectors(), FakeVideos())

    response = await workflow.analyze(FEN)

    assert response.route == "theory"
    assert response.suggested_moves[0].san == "e4"
    assert stockfish.calls == 0
    assert "identify_position:lichess" in response.trace


async def test_graph_uses_stockfish_outside_theory() -> None:
    stockfish = FakeStockfish()
    workflow = OpeningAgentWorkflow(FakeLichess(False), stockfish, FakeVectors(), FakeVideos())

    response = await workflow.analyze(FEN)

    assert response.route == "engine"
    assert response.evaluation is not None
    assert response.evaluation.best_move == "e2e4"
    assert stockfish.calls == 1
    assert "evaluate_with_stockfish" in response.trace
