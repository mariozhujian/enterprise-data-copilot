"""独立联调入口，Week 2 合并时使用 README 的 main.py 增量片段。"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.rag3.api import install_rag_routes
from app.rag3.runtime import rag_runtime

app = FastAPI(title="Enterprise Data Copilot - Week 3", lifespan=rag_runtime)
install_rag_routes(app)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"code": "INVALID_REQUEST",
                                                  "message": "请求参数不合法"})


@app.get("/health")
async def health():
    return {"status": "UP"}
