# 定义请求和响应	DTO、Validation

from uuid import UUID

from pydantic import BaseModel, Field, field_validator

class SearchRequest(BaseModel):
    # 限定查询哪个知识库
    knowledgeBaseId: UUID
    # 限制问题长度
    query: str = Field(min_length=1, max_length=2000)
    # 默认取前 5 条，最多 10 条
    topK: int = Field(default=5, ge=1, le=10)
    # 仅为示范初始值，不是置信概率；需要用业务评测集调参。
    # 相似度阈值，不是答案正确概率
    minScore: float = Field(default=0.35, ge=-1, le=1)

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value

class AskRequest(SearchRequest):
    sessionId: UUID | None = None

class Source(BaseModel):
    citationId: str
    chunkId: UUID
    documentId: UUID
    filename: str
    page: int | None = None
    heading: str | None = None
    chunkIndex: int
    score: float
    # 返回实际送入 Prompt 的片段，便于验证引用。
    excerpt: str


class SearchResponse(BaseModel):
    sources: list[Source]


class AskResponse(BaseModel):
    sessionId: UUID
    answer: str
    model: str
    grounded: bool
    sources: list[Source]
    # 结构化 status 由程序设置；不等同于事实正确性验证。
    status: str


class UploadResponse(BaseModel):
    documentId: UUID
    knowledgeBaseId: UUID
    filename: str
    chunkCount: int
    status: str
    warnings: list[str] = Field(default_factory=list)
