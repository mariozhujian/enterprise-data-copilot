from contextlib import asynccontextmanager

from app.rag3.embedding import EmbeddingService
from app.rag3.repository import RagRepository, create_pool
from app.rag3.service import AnswerGenerator, RagService
from app.rag3.settings import get_rag_settings

# 负责创建并连接所有组件
@asynccontextmanager
async def rag_runtime(app):
    settings = get_rag_settings()
    pool = create_pool(settings.database_url)
    embedding = EmbeddingService(settings)
    generator = AnswerGenerator(settings)
    try:
        await pool.open(wait=True, timeout=15)
        app.state.rag = RagService(RagRepository(pool), embedding, generator)
        # 服务运行期间暂停在这里，关闭继续执行清理
        yield
    finally:
        await generator.close()
        await embedding.close()
        await pool.close()
