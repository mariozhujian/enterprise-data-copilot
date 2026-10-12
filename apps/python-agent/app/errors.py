# 统一异常处理
import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
)

logger = logging.getLogger(__name__)

class LLMGatewayError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 502):
        self.code = code
        self.message = message
        self.status_code = status_code


def convert_llm_error(exc: Exception) -> LLMGatewayError:
    if isinstance(exc, APITimeoutError):
        return LLMGatewayError(
            "LLM_TIMEOUT",
            "模型响应超时",
            504,
        )

    if isinstance(exc, APIConnectionError):
        return LLMGatewayError(
            "LLM_CONNECTION_ERROR",
            "无法连接模型服务",
            502,
        )

    if isinstance(exc, APIStatusError):
        return LLMGatewayError(
            "LLM_UPSTREAM_ERROR",
            "上游模型请求失败",
            502,
        )

    return LLMGatewayError(
        "INTERNAL_ERROR",
        "AI服务内部异常",
        500,
    )

async def gateway_error_handler(request: Request, exc: LLMGatewayError):
    logger.warning("AI request failed: %s", exc.code)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
        },
    )

async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "code": "INVALID_REQUEST",
            "message": "请求参数不合法",
        },
    )

async def unexpected_error_handler(request: Request, exc: Exception):
    logger.error("Unexpected error: %s", exc_info=exc,)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "服务器内部异常",
        }
    )
