import httpx

from app.core.config import Settings
from app.schemas import MovesResponse, OpeningInfo, TheoryMove


class LichessUnavailable(RuntimeError):
    """L'explorateur Lichess n'a pas répondu correctement."""


class LichessService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def get_moves(self, fen: str) -> MovesResponse:
        url = f"{self.settings.lichess_base_url}/masters"
        headers = {"User-Agent": "ffe-opening-coach-student-poc/1.0"}
        if self.settings.lichess_api_token:
            headers["Authorization"] = f"Bearer {self.settings.lichess_api_token}"
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.external_api_timeout_seconds
            ) as client:
                response = await client.get(
                    url,
                    params={"fen": fen, "moves": 8, "topGames": 0},
                    headers=headers,
                )
                response.raise_for_status()
        except (httpx.TimeoutException, httpx.HTTPError) as exc:
            raise LichessUnavailable(
                "L'explorateur d'ouvertures Lichess est indisponible."
            ) from exc

        payload = response.json()
        moves = []
        for item in payload.get("moves", []):
            popularity = int(item.get("white", 0) + item.get("draws", 0) + item.get("black", 0))
            moves.append(
                TheoryMove(
                    uci=item["uci"],
                    san=item["san"],
                    white=item.get("white", 0),
                    draws=item.get("draws", 0),
                    black=item.get("black", 0),
                    average_rating=item.get("averageRating"),
                    popularity=popularity,
                )
            )
        opening_data = payload.get("opening")
        opening = OpeningInfo(**opening_data) if opening_data else None
        return MovesResponse(fen=fen, opening=opening, moves=moves)
