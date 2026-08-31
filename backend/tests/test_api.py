import httpx

from app.main import app


async def test_healthcheck() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/healthcheck")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_agent_rejects_invalid_fen_before_external_calls() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/agent/analyze", json={"fen": "invalid"})
    assert response.status_code == 422
    assert "FEN invalide" in response.json()["detail"]
