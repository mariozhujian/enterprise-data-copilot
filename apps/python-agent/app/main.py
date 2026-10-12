# 编写 FastAPI 接口
# 这里没有把上游服务的完整异常内容返回给前端，因为原始错误里可能包含不适合向用户暴露的信息


from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.chat import router
from app.errors import (
    LLMGatewayError,
    gateway_error_handler,
    unexpected_error_handler,
    validation_error_handler,
)
from app.services.llm_service import LLMService


@asynccontextmanager
async def lifespan(app: FastAPI):
    service = LLMService()
    app.state.llm = service

    try:
        yield
    finally:
        await service.close()


app = FastAPI(
    title="Enterprise Data Copilot - Agent",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_exception_handler(
    LLMGatewayError,
    gateway_error_handler,
)
app.add_exception_handler(
    RequestValidationError,
    validation_error_handler,
)
app.add_exception_handler(
    Exception,
    unexpected_error_handler,
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "UP"}
