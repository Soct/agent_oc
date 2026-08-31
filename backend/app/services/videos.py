import asyncio
from datetime import UTC, datetime
from urllib.parse import quote_plus

import httpx
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.core.config import Settings
from app.schemas import VideoResult, VideosResponse


class VideoService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def search(self, opening: str) -> VideosResponse:
        cached = await asyncio.to_thread(self._read_cache, opening)
        if cached:
            return VideosResponse(opening=opening, source="mongodb-cache", videos=cached)

        if not self.settings.youtube_api_key:
            return self._demo_catalogue(opening)

        query = f"{opening} échecs ouverture tutoriel explication"
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.external_api_timeout_seconds
            ) as client:
                response = await client.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params={
                        "key": self.settings.youtube_api_key,
                        "part": "snippet",
                        "type": "video",
                        "safeSearch": "strict",
                        "relevanceLanguage": "fr",
                        "maxResults": self.settings.youtube_max_results,
                        "q": query,
                    },
                )
                response.raise_for_status()
        except (httpx.TimeoutException, httpx.HTTPError):
            result = self._demo_catalogue(opening)
            result.notice = "API YouTube indisponible : catalogue de démonstration utilisé."
            return result

        videos = [self._from_youtube(item) for item in response.json().get("items", [])]
        await asyncio.to_thread(self._write_cache, opening, videos)
        return VideosResponse(opening=opening, source="youtube", videos=videos)

    @staticmethod
    def _from_youtube(item: dict) -> VideoResult:
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]
        thumbnails = snippet.get("thumbnails", {})
        thumbnail = thumbnails.get("medium") or thumbnails.get("default") or {}
        return VideoResult(
            video_id=video_id,
            title=snippet["title"],
            channel=snippet["channelTitle"],
            thumbnail_url=thumbnail.get("url", ""),
            url=f"https://www.youtube.com/watch?v={video_id}",
            published_at=snippet.get("publishedAt"),
        )

    def _mongo_collection(self):
        client = MongoClient(self.settings.mongodb_url, serverSelectionTimeoutMS=1000)
        return client, client[self.settings.mongodb_database]["video_searches"]

    def _read_cache(self, opening: str) -> list[VideoResult]:
        try:
            client, collection = self._mongo_collection()
            try:
                item = collection.find_one({"opening_key": opening.casefold()})
            finally:
                client.close()
        except PyMongoError:
            return []
        return [VideoResult(**video) for video in item.get("videos", [])] if item else []

    def _write_cache(self, opening: str, videos: list[VideoResult]) -> None:
        try:
            client, collection = self._mongo_collection()
            try:
                collection.update_one(
                    {"opening_key": opening.casefold()},
                    {
                        "$set": {
                            "opening": opening,
                            "videos": [video.model_dump() for video in videos],
                            "updated_at": datetime.now(UTC),
                        }
                    },
                    upsert=True,
                )
            finally:
                client.close()
        except PyMongoError:
            return

    @staticmethod
    def _demo_catalogue(opening: str) -> VideosResponse:
        query = quote_plus(f"{opening} échecs ouverture explication français")
        video = VideoResult(
            video_id="youtube-search",
            title=f"Rechercher un cours sur : {opening}",
            channel="YouTube (recherche de démonstration)",
            thumbnail_url="",
            url=f"https://www.youtube.com/results?search_query={query}",
        )
        return VideosResponse(
            opening=opening,
            source="catalogue-demo",
            videos=[video],
            notice="Ajoutez YOUTUBE_API_KEY pour obtenir des vidéos et métadonnées réelles.",
        )
