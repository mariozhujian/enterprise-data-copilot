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
import asyncio
import time



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

@app.get("/info")
async def info():
    return {
        "name": "Enterprise AI Agent",
        "version": "1.0.0",
        "language": "python",
    }

@app.get("/chat/demo")
async def chat_demo():
    print("1. 收到用户请求")
    # 模拟调用大模型，等待 3 秒
    await asyncio.sleep(3)
    print("2. 大模型返回结果")
    return {
        "answer": "最近7天设备运行正常"
    }

@app.get("/chat/bad")
async def chat_bad():
    time.sleep(3)
    return {"answer": "success"}
