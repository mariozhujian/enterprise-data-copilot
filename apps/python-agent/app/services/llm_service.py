from openai import AsyncOpenAI, max_retries

from app.config import get_settings
from app.schemas import ChatResponse
from openai.resources import Chat
from openai.types import Completion

SYSTEM_PROMPT = """
    你是一名企业级智能数据分析助手。
    请使用简体中文回答问题。

    规则：
    1. 不能编造企业经营数据。
    2. 数据不足时明确说明。
    3. 回答尽量简洁、准确。
    4. 当前阶段不能访问企业数据库。
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

    async def chat(self, message: str) -> ChatResponse:

        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": message,
                }
            ]
        )

        answer = completion.choices[0].message.content

        return ChatResponse(
            answer=answer or "",
            model=self.model,
        )
