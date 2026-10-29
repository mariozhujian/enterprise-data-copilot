"""RAG4 检索流程的数据契约：请求、身份、命中片段和检索结果。"""

from dataclasses import dataclass, field
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 限定客户端可选择的检索流程：向量、混合检索、混合检索后重排。
Strategy = Literal["vector", "hybrid", "hybrid_rerank"]

@dataclass(frozen=True)
class Principal:
    """服务端认证得到的访问主体；不可变，避免检索过程中意外修改权限。"""

    subject: str
    tenant: UUID  # 所属租户
    roles: tuple[str, ...]  # 用户角色
    allowed_kbs: tuple[UUID, ...]  # 允许访问的知识库
    clearance: int  # 可访问的最高文档密级

@dataclass
class Hit:
    """一个命中的文档片段，以及各检索阶段产生的分数。"""

    id: str
    document_id: str
    content: str
    filename: str
    metadata: dict = field(default_factory=dict)  # 每个命中使用独立字典
    vector_score: float | None = None
    bm25_score: float
    rrf_score: float | None = None
    rerank_logit: float | None = None

    @classmethod
    def from_row(cls, row):
        """将数据库查询行转换为命中片段；缺失向量分数时记为 None。"""
        return cls(str(row["chunk_id"]), str(row["document_id"]), row["content"],
                   row["filename"], row["metadata"], row.get("vector_score"))

class SearchRequest(BaseModel):
    """对外搜索请求；由 Pydantic 校验 UUID、策略和参数范围。"""

    # 身份/角色不允许从 JSON 提交，额外字段直接拒绝
    model_config = ConfigDict(extra="forbid")
    knowledgeBaseId: UUID
    query: str = Field(min_length=1, max_length=2000)
    strategy: Strategy = "hybrid_rerank"
    topK: int = Field(default=5, ge=1, le=10)
    multiQuery: bool = False
    sessionId: UUID | None = None

    @field_validator("query")
    @classmethod
    def clean_query(cls, value):
        """去掉问题两端空白，并拒绝纯空白问题。"""
        value = value.strip()
        if not value:
            raise ValueError("问题不能为空")
        return value

@dataclass
class SearchResult:
    """检索流程的内部结果：最终命中、候选、查询词及耗时。"""

    hits: list[Hit]
    candidates: list[Hit]  # 中间阶段召回的候选片段
    queries: list[str]  # 实际参与检索的问题列表
    timings: dict[str, float]  # 各阶段耗时
    needs_clarification: bool = False  # 是否需要向用户追问
