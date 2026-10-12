from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.config import get_settings

SYSTEM_PROMPT = """
    你是企业级智能数据分析助手。

    规则：
    1. 使用简体中文回答。
    2. 不能编造企业经营数据。
    3. 没有查询工具时，应说明无法取得真实数据。
    4. 不要声称已经执行数据库查询。
"""

class LLMService:

    def __init__(self):
        settings = get_settings()

        self.model = settings.deepseek_model

        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            timeout=30,
            max_retries=1
        )

    def build_messages(self, message: str) -> list[dict]:
        return [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": message,
            }
        ]

    async def chat(self, message: str) -> str:

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=self.build_messages(message),
        )

        return response.choices[0].message.content or ""

    # 流式输出：返回一个异步迭代器，允许逐段消费模型输出
    async def stream(self, message: str) -> AsyncIterator[str]:
        async with self.client.chat.completions.stream(
            model=self.model,
            messages=self.build_messages(message),
        ) as stream:
            async for event in stream:
                if event.type == "content.delta" and event.delta:
                    yield event.delta

    async def close(self):
        await self.client.close()
