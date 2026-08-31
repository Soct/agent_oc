import pytest
from fastapi import HTTPException

from app.services.chess_utils import validate_fen


def test_validate_fen_normalizes_a_valid_position() -> None:
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    assert validate_fen(fen) == fen


def test_validate_fen_rejects_an_invalid_position() -> None:
    with pytest.raises(HTTPException) as error:
        validate_fen("not-a-fen")
    assert error.value.status_code == 422

