import logging
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse
from openai import APIError, APITimeoutError
from psycopg import Error as DatabaseError

from app.rag3.errors import RagError
from app.rag3.loader import MAX_FILE_BYTES
from app.rag3.schemas import AskRequest, AskResponse, SearchRequest, SearchResponse, UploadResponse

# 接收请求并调用 Service
router = APIRouter(prefix="/rag", tags=["RAG"])
logger = logging.getLogger(__name__)


@router.post("/documents", response_model=UploadResponse)
async def upload_document(request: Request, knowledgeBaseId: Annotated[UUID, Form()],
                          file: Annotated[UploadFile, File()]):
    try:
        filename = Path((file.filename or "document").replace("\\", "/")).name
        if len(filename) > 255:
            raise RagError("BAD_FILENAME", "文件名过长")
        # MIME 和扩展名都不能当成安全保证；解析器还会验证 PDF/UTF-8 内容。
        if Path(filename).suffix.lower() not in {".pdf", ".md", ".txt"}:
            raise RagError("UNSUPPORTED_FILE", "仅支持 PDF、Markdown、TXT", 415)
        # 多读 1 字节，用于识别超限
        data = await file.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise RagError("FILE_TOO_LARGE", "文件不能超过 10 MiB", 413)
        return await request.app.state.rag.ingest(knowledgeBaseId, filename, data)
    finally:
        # 无论成功或失败，都释放上传文件资源
        await file.close()


@router.post("/search", response_model=SearchResponse)
async def search(body: SearchRequest, request: Request):
    return SearchResponse(sources=await request.app.state.rag.search(body))


@router.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest, request: Request):
    return await request.app.state.rag.ask(body)


async def handle_rag_error(request: Request, exc: RagError):
    return JSONResponse(status_code=exc.status, content={"code": exc.code, "message": exc.message})


async def handle_api_error(request: Request, exc: APIError):
    logger.warning("RAG provider error: %s", type(exc).__name__)
    timeout = isinstance(exc, APITimeoutError)
    return JSONResponse(status_code=504 if timeout else 502, content={
        "code": "LLM_TIMEOUT" if timeout else "AI_UPSTREAM_ERROR",
        "message": "模型响应超时" if timeout else "模型服务暂时不可用",
    })


async def handle_database_error(request: Request, exc: DatabaseError):
    logger.error("RAG database error", exc_info=exc)
    return JSONResponse(status_code=503, content={"code": "DATABASE_UNAVAILABLE",
                                                  "message": "知识库数据库暂时不可用"})


def install_rag_routes(app):
    app.include_router(router)
    app.add_exception_handler(RagError, handle_rag_error)
    app.add_exception_handler(APIError, handle_api_error)
    app.add_exception_handler(DatabaseError, handle_database_error)
