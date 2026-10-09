
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app, get_llm_service
from app.schemas import ChatResponse


class FakeLLMService:

    async def chat(self, message: str) -> ChatResponse:
        return ChatResponse(
            answer=f"模拟回复：{message}",
            model="fake-model",
        )


@pytest.mark.asyncio
async def test_chat_success(monkeypatch):

    monkeypatch.setattr(
        "app.main.get_llm_service",
        lambda: FakeLLMService(),
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:

        response = await client.post(
            "/api/chat",
            json={"message": "你好"},
        )

    assert response.status_code == 200
    assert response.json()["answer"] == "模拟回复：你好"


@pytest.mark.asyncio
async def test_chat_empty_message():

    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:

        response = await client.post(
            "/api/chat",
            json={"message": ""},
        )

    assert response.status_code == 422
