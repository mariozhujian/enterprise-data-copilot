
import asyncio
import json
import logging
from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.schemas import ChatRequest, ChatResponse
from app.services.llm_service import LLMService
from app.errors import (LLMGatewayError, convert_llm_error)

# 为了避免中文、换行或 JSON 特殊字符破坏 SSE 协议，事件数据统一编码为 JSON。
# 第一，start、delta、done、error 是我们自己定义的业务协议。 它不是 OpenAI 内部的标准事件格式，而是 Java 与 Python 服务之间约定的统一接口。
# 第二，不要在 SSE 生成器中吞掉 asyncio.CancelledError。 客户端断开后应允许取消向上传播，使模型流尽快结束，避免继续消耗 Token。

router = APIRouter()
logger = logging.getLogger(__name__)


def encode_sse(event: str, data: dict) -> str:
    payload = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":")
    )
    return f"event:{event}\ndata: {payload}\n\n"

@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request):
    session_id = body.sessionId or uuid4()
    service: LLMService = request.app.state.llm

    try:
        answer = await service.chat(body.message)
    except Exception as exc:
        raise convert_llm_error(exc) from exc

    return ChatResponse(
        sessionId=session_id,
        answer=answer,
        model=service.model,
    )

@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, request: Request):
    session_id = body.sessionId or uuid4()
    service: LLMService = request.app.state.llm

    async def event_generator():
        try:
            yield encode_sse(
                "start",
                {
                    "sessionId": str(session_id),
                    "model": service.model,
                }
            )

            async for token in service.stream(body.message):
                if await request.is_disconnected():
                    logger.info(
                        "Client disconnected: %s",
                        session_id,
                    )
                    break

                yield encode_sse(
                    "delta",
                    {"content": token},
                )

            else: yield encode_sse(
                "done",
                {
                    "sessionId": str(session_id),
                    "status": "completed",
                },
            )

        except asyncio.CancelledError:
            logger.info(
                "Stream cancelled: %s",
                session_id,
            )
            raise

        except Exception as exc:
            error = convert_llm_error(exc)
            logger.exception("LLM stream failure")

            yield encode_sse(
                "error",
                {
                    "code": error.code,
                    "message": error.message,
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )