from urllib.parse import unquote

import chess
from fastapi import HTTPException, status


def validate_fen(raw_fen: str) -> str:
    """Décode et valide une FEN complète avant tout appel externe."""

    fen = unquote(raw_fen).strip()
    try:
        board = chess.Board(fen)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Position FEN invalide : {exc}",
        ) from exc
    if not board.is_valid():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Position FEN incohérente selon les règles des échecs.",
        )
    return board.fen()

