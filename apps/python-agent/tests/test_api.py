
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


class FakeLLMService:

    model = "fake-model"

    async def chat(self, message: str) -> str:
        return f"模拟回复：{message}"


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
    assert response.json()["answer"] == "模拟回复：你好"


@pytest.mark.asyncio
async def test_chat_empty_message():

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
