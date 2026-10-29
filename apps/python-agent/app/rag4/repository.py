"""RAG4 数据访问层：按同一权限条件读取 BM25 语料和向量检索结果。"""
from app.rag3.chunker import PIPELINE_VERSION
from app.rag3.errors import RagError
from app.rag4.security import authorize_kb
from app.rag4.types import Hit

# 两路检索共用权限谓词；%s 占位符对应 params() 返回的参数顺序。
# 同时限定知识库、租户、角色、密级和当前嵌入/切分版本。
ACCESS_SQL = """
 c.knowledge_base_id = %s AND d.knowledge_base_id = %s
 AND d.tenant_id = %s AND d.allowed_roles && %s::text[]
 AND d.classification <= %s AND d.is_current = true
 AND d.embedding_model = %s AND d.pipeline_version = %s
"""
# 全量语料查询与向量查询都需要片段及其所属文档的信息。
SELECT_SQL = """SELECT c.id AS chunk_id, c.document_id, c.content, c.metadata, d.filename
                FROM rag_chunks c JOIN rag_documents d ON d.id = c.document_id \
             """

class HybridRepository:
    """封装授权语料读取和向量近邻查询所需的数据库连接与配置。"""

    def __init__(self, pool, embedding_space_id, max_corpus=5000):
        self.pool = pool
        self.space_id = embedding_space_id
        self.max_corpus = max_corpus
        self.max_corpus = max_corpus

    def params(self, principal, kb):
        """先确认知识库访问权，再生成 ACCESS_SQL 所需的绑定参数。"""
        authorize_kb(principal, kb)
        return (kb, kb, principal.tenant_id, list(principal.roles), principal.clearance,
                self.space_id, PIPELINE_VERSION)

    async def corpus(self, principal, kb):
        """读取授权片段供进程内 BM25 使用，超过上限则拒绝加载。"""
        params = self.params(principal, kb)
        async with self.pool.connection() as conn:
            cursor = await conn.execute(
                SELECT_SQL +  " WHERE " + ACCESS_SQL + " ORDER BY c.id LIMIT %s",
                (*params, self.max_corpus + 1),  # 多取一条，用于判断是否超限。
            )
            rows = await cursor.fetchall()

        if len(rows) > self.max_corpus:
            raise RagError("CORPUS_TOO_LARGE", "教学BM25最多5000个授权Chunk，请升级检索后端", 503)
        return [Hit.from_row(row) for row in rows]

async def vector(self, principal, kb, vector, limit):
    """按向量距离排序并返回指定数量的授权片段。"""
    params = self.params(principal, kb)
    sql = """SELECT c.id AS chunk_id, c.document_id, c.content, c.metadata, d.filename,
                    1 - (c.embedding <=> %s) AS vector_score
                 FROM rag_chunks c JOIN rag_documents d ON d.id=c.document_id
                 WHERE """ + ACCESS_SQL + " ORDER BY c.embedding <=> %s, c.id LIMIT %s"
    async with self.pool.connection() as conn:
        cursor = await conn.execute(sql, (vector, *params, vector, limit))
        return [Hit.from_row(row) for row in await cursor.fetchall()]
