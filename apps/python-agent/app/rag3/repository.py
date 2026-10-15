#写入库、去重、检索
from uuid import UUID, uuid4

from pgvector.psycopg import register_vector_async
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from app.rag3.chunker import PIPELINE_VERSION


async def configure_vector(conn):
    await register_vector_async(conn)
    # 类型注册可能查询数据库；连接池 configure 必须归还 idle 连接。
    await conn.commit()

def create_pool(database_url: str) -> AsyncConnectionPool:
    return AsyncConnectionPool(
        database_url, open=False, min_size=1, max_size=5,
        timeout=10, configure=configure_vector,
        kwargs={"row_factory": dict_row, "connect_timeout": 5},
    )


class RagRepository:
    def __init__(self, pool):
        self.pool = pool

    async def find_document(self, kb: UUID, digest: str, model: str):
        async with self.pool.connection() as conn:
            cursor = await conn.execute(
                """SELECT * FROM rag_documents
                   WHERE knowledge_base_id=%s AND sha256=%s
                     AND embedding_model=%s AND pipeline_version=%s""",
                (kb, digest, model, PIPELINE_VERSION),
            )
            return await cursor.fetchone()

    async def save_document(self, kb, filename, digest, model, chunks, vectors, warnings):
        document_id = uuid4()
        # 先完成 Embedding，再占用数据库事务；任何 Chunk 写入失败整笔回滚。
        async with self.pool.connection() as conn, conn.transaction():
            cursor = await conn.execute(
                """INSERT INTO rag_documents
                   (id,knowledge_base_id,filename,sha256,embedding_model,pipeline_version,
                    chunk_count,metadata)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (knowledge_base_id,sha256,embedding_model,pipeline_version)
                    DO NOTHING RETURNING *""",
                (document_id, kb, filename, digest, model, PIPELINE_VERSION,
                 len(chunks), Jsonb({"warnings": warnings})),
            )
            row = await cursor.fetchone()
            if row is None:
                cursor = await conn.execute(
                    """SELECT * FROM rag_documents
                       WHERE knowledge_base_id=%s AND sha256=%s
                         AND embedding_model=%s AND pipeline_version=%s""",
                    (kb, digest, model, PIPELINE_VERSION),
                )
                return await cursor.fetchone(), True
            async with conn.cursor() as cursor:
                await cursor.executemany(
                    """INSERT INTO rag_chunks
                       (id,document_id,knowledge_base_id,chunk_index,content,metadata,embedding)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    [(uuid4(), document_id, kb, c.index, c.content,
                      Jsonb(c.metadata), v) for c, v in zip(chunks, vectors, strict=True)],
                )
            return row, False

    async def search(self, kb, model, vector, top_k):
        async with self.pool.connection() as conn:
            cursor = await conn.execute(
                """SELECT c.id AS chunk_id, c.document_id, c.chunk_index, c.content,
                          c.metadata, d.filename,
                          1 - (c.embedding <=> %s) AS score
                   FROM rag_chunks c JOIN rag_documents d ON d.id=c.document_id
                   WHERE c.knowledge_base_id=%s AND d.knowledge_base_id=%s
                     AND d.embedding_model=%s AND d.pipeline_version=%s
                   ORDER BY c.embedding <=> %s LIMIT %s""",
                (vector, kb, kb, model, PIPELINE_VERSION, vector, top_k),
            )
            return await cursor.fetchall()
