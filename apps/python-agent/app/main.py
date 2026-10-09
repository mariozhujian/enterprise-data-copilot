# 编写 FastAPI 接口
# 这里没有把上游服务的完整异常内容返回给前端，因为原始错误里可能包含不适合向用户暴露的信息

import logging

from fastapi import FastAPI, HTTPException
from openai import APIConnectionError, APITimeoutError, APIStatusError

from app.schemas import ChatRequest, ChatResponse
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise Data Copilot - Agent Service",
    version="0.1.0",
)

_llm_service = None

def get_llm_service() -> LLMService:
    global _llm_service

    if _llm_service is None:
        _llm_service = LLMService()

    return _llm_service

@app.get("/health")
async def health():
    return {"status": "UP"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        service = get_llm_service()

        return await service.chat(request.message)

    except APITimeoutError:
        logger.warning("LLM request timed out")
        raise HTTPException(
            status_code=504,
            detail="模型响应超时",
        )

    except APIConnectionError:
        logger.exception("LLM connection error")
        raise HTTPException(
            status_code=502,
            detail="模型连接失败"
        )

    except APIStatusError as exc:
        logger.warning("LLM API error: status=%s", exc.status_code)
        raise HTTPException(
            status_code=502,
            detail="上游模型服务请求失败",
        )