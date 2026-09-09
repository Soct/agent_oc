import httpx

from app.core.config import Settings
from app.schemas import MovesResponse, OpeningInfo, ReferenceGame, ReferencePlayer, TheoryMove


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
                    params={"fen": fen, "moves": 8, "topGames": 3},
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
        games = []
        top_games = payload.get("topGames", [])
        # Selon la variante de l'explorateur, une partie peut être renvoyée
        # dans topGames ou attachée au coup correspondant.
        if not top_games:
            top_games = [item["game"] for item in payload.get("moves", []) if item.get("game")]
        for item in top_games:
            game = item.get("game", item)
            game_id = game.get("id")
            if not game_id:
                continue
            games.append(
                ReferenceGame(
                    id=game_id,
                    winner=game.get("winner"),
                    white=ReferencePlayer(**(game.get("white") or {})),
                    black=ReferencePlayer(**(game.get("black") or {})),
                    year=game.get("year"),
                    month=game.get("month"),
                    url=f"https://lichess.org/{game_id}",
                )
            )
        return MovesResponse(
            fen=fen, opening=opening, moves=moves, reference_games=games[:3]
        )
