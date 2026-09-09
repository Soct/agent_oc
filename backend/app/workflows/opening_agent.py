from typing import Literal, TypedDict

import chess
from langgraph.graph import END, START, StateGraph

from app.schemas import (
    AgentResponse,
    ContextResult,
    EvaluationResponse,
    OpeningInfo,
    TheoryMove,
    VideoResult,
)
from app.services.lichess import LichessService, LichessUnavailable
from app.services.stockfish import StockfishService, StockfishUnavailable
from app.services.vector_store import VectorStoreService
from app.services.videos import VideoService


class AgentState(TypedDict, total=False):
    fen: str
    route: Literal["theory", "engine"]
    opening: OpeningInfo | None
    suggested_moves: list[TheoryMove]
    evaluation: EvaluationResponse | None
    context: list[ContextResult]
    videos: list[VideoResult]
    warnings: list[str]
    trace: list[str]
    summary: str


class OpeningAgentWorkflow:
    """Petit graphe déterministe : Lichess si théorique, Stockfish sinon."""

    def __init__(
        self,
        lichess: LichessService,
        stockfish: StockfishService,
        vector_store: VectorStoreService,
        videos: VideoService,
    ) -> None:
        self.lichess = lichess
        self.stockfish = stockfish
        self.vector_store = vector_store
        self.video_service = videos
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("identify_position", self._identify_position)
        builder.add_node("evaluate_with_stockfish", self._evaluate_with_stockfish)
        builder.add_node("retrieve_context", self._retrieve_context)
        builder.add_node("find_videos", self._find_videos)
        builder.add_node("format_answer", self._format_answer)
        builder.add_edge(START, "identify_position")
        builder.add_conditional_edges(
            "identify_position",
            self._route_position,
            {"theory": "retrieve_context", "engine": "evaluate_with_stockfish"},
        )
        builder.add_edge("evaluate_with_stockfish", "retrieve_context")
        builder.add_edge("retrieve_context", "find_videos")
        builder.add_edge("find_videos", "format_answer")
        builder.add_edge("format_answer", END)
        return builder.compile()

    async def _identify_position(self, state: AgentState) -> dict:
        warnings = list(state.get("warnings", []))
        trace = [*state.get("trace", []), "identify_position:lichess"]
        try:
            theory = await self.lichess.get_moves(state["fen"])
        except LichessUnavailable as exc:
            warnings.append(str(exc))
            return {
                "route": "engine",
                "opening": None,
                "suggested_moves": [],
                "warnings": warnings,
                "trace": trace,
            }
        route: Literal["theory", "engine"] = "theory" if theory.moves else "engine"
        return {
            "route": route,
            "opening": theory.opening,
            "suggested_moves": theory.moves[:3],
            "warnings": warnings,
            "trace": trace,
        }

    @staticmethod
    async def _route_position(state: AgentState) -> Literal["theory", "engine"]:
        return state["route"]

    async def _evaluate_with_stockfish(self, state: AgentState) -> dict:
        warnings = list(state.get("warnings", []))
        evaluation = None
        try:
            evaluation = await self.stockfish.evaluate(state["fen"])
        except StockfishUnavailable as exc:
            warnings.append(str(exc))
        return {
            "evaluation": evaluation,
            "warnings": warnings,
            "trace": [*state.get("trace", []), "evaluate_with_stockfish"],
        }

    async def _retrieve_context(self, state: AgentState) -> dict:
        opening = state.get("opening")
        query = opening.name if opening and opening.name else "principes d'ouverture aux échecs"
        response = await self.vector_store.search(query, limit=3)
        warnings = list(state.get("warnings", []))
        if response.backend == "local-fallback":
            warnings.append("Milvus indisponible ou vide : contexte local utilisé.")
        return {
            "context": response.results,
            "warnings": warnings,
            "trace": [*state.get("trace", []), f"retrieve_context:{response.backend}"],
        }

    async def _find_videos(self, state: AgentState) -> dict:
        opening = state.get("opening")
        name = opening.name if opening and opening.name else "principes d'ouverture"
        response = await self.video_service.search(name)
        warnings = list(state.get("warnings", []))
        if response.notice:
            warnings.append(response.notice)
        return {
            "videos": response.videos,
            "warnings": warnings,
            "trace": [*state.get("trace", []), f"find_videos:{response.source}"],
        }

    @staticmethod
    async def _format_answer(state: AgentState) -> dict:
        opening = state.get("opening")
        board = chess.Board(state["fen"])
        side = "les Blancs" if board.turn == chess.WHITE else "les Noirs"
        side_verb = f"C'est aux {side[4:]} de jouer"
        if state["route"] == "theory":
            moves = ", ".join(move.san for move in state.get("suggested_moves", []))
            name = opening.name if opening and opening.name else "ouverture connue"
            summary = (
                f"Position théorique ({name}). {side_verb}. "
                f"Coups les plus joués : {moves}."
            )
        else:
            evaluation = state.get("evaluation")
            if evaluation and evaluation.mate_in is not None:
                score = f"mat en {evaluation.mate_in}"
            elif evaluation and evaluation.centipawns is not None:
                score = f"{evaluation.centipawns / 100:+.2f} pion(s) pour {side}"
            else:
                score = "évaluation indisponible"
            best_san = ""
            if evaluation and evaluation.best_move:
                try:
                    move = board.parse_uci(evaluation.best_move)
                    best_san = f", meilleur coup {board.san(move)}"
                except ValueError:
                    best_san = f", meilleur coup {evaluation.best_move}"
            summary = f"Position hors théorie : Stockfish indique {score}{best_san}."
        return {
            "summary": summary,
            "trace": [*state.get("trace", []), "format_answer"],
        }

    async def analyze(self, fen: str) -> AgentResponse:
        state = await self.graph.ainvoke({"fen": fen, "warnings": [], "trace": []})
        return AgentResponse(**state)
