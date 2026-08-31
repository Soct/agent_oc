import asyncio
from pathlib import Path

import chess
import chess.engine

from app.core.config import Settings
from app.schemas import EvaluationResponse


class StockfishUnavailable(RuntimeError):
    """Le binaire Stockfish est absent ou ne peut pas être démarré."""


class StockfishService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def evaluate(self, fen: str) -> EvaluationResponse:
        return await asyncio.to_thread(self._evaluate_sync, fen)

    def _evaluate_sync(self, fen: str) -> EvaluationResponse:
        path = Path(self.settings.stockfish_path)
        if not path.exists():
            raise StockfishUnavailable(f"Binaire Stockfish introuvable : {path}")

        board = chess.Board(fen)
        try:
            with chess.engine.SimpleEngine.popen_uci(str(path)) as engine:
                info = engine.analyse(
                    board,
                    chess.engine.Limit(depth=self.settings.stockfish_depth),
                )
                best = engine.play(board, chess.engine.Limit(depth=self.settings.stockfish_depth))
        except (OSError, chess.engine.EngineError, chess.engine.EngineTerminatedError) as exc:
            raise StockfishUnavailable("Stockfish n'a pas pu analyser la position.") from exc

        score = info["score"].pov(board.turn)
        return EvaluationResponse(
            fen=fen,
            centipawns=score.score(),
            mate_in=score.mate(),
            best_move=best.move.uci() if best.move else None,
            depth=info.get("depth", self.settings.stockfish_depth),
        )
