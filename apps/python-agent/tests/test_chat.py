# Python API 自动化测试

from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from openai import APITimeoutError
import httpx


class FakeLLMService:
    model = "fake-model"

    async def chat(self, message: str) -> str:
        return f"模拟回答：{message}"

    async def stream(self, message: str) -> str:
        for chunk in ["你好，", "世界"]:
            yield chunk

class TimeoutLLMService:
    model = "fake-model"

    async def chat(self, message: str):
        raise APITimeoutError(
            request=httpx.Request(
                "POST",
                "https://example.com/v1/chat/completions",
            ),
        )

@pytest.mark.asyncio
async def test_model_timeout():
    app.state.llm = TimeoutLLMService()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/chat", json={"message": "你好"})

        assert response.status_code == 504
        assert response.json()["code"] == "LLM_TIMEOUT"

@pytest.fixture(autouse=True)
def fake_service():
    previous = getattr(app.state, "llm", None)
    app.state.llm = FakeLLMService()

    yield

    if previous is None:
        del app.state.llm
    else:
        app.state.llm = previous

@pytest.mark.asyncio
async def test_chat_success():
    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            "/chat",
            json={"message": "你好"},
        )

    assert response.status_code == 200

    result = response.json()
    assert result["answer"] == "模拟回答：你好"
    assert result["model"] == "fake-model"
    UUID(result["sessionId"])

@pytest.mark.asyncio
async def test_session_id_passthrough():
    session_id = "1f23f734-bd03-49ce-9c57-bf7c81dc2ed4"

    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            "/chat",
            json={
                "message": "继续",
                "sessionId": session_id,
            },
        )

    assert response.status_code == 200
    assert response.json()["sessionId"] == session_id

@pytest.mark.asyncio
async def test_stream_events():
    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            "/chat/stream",
            json={"message": "测试"},
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    body = response.text

    assert "event: start" in body
    assert "event: delta" in body
    assert "event: done" in body

    assert body.index("event: start") < body.index("event: delta")
    assert body.index("event: delta") < body.index("event: done")

    assert '"content":"你好，"' in body


@pytest.mark.asyncio
async def test_invalid_message():
    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            "/chat",
            json={"message": ""},
        )

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_REQUEST"
