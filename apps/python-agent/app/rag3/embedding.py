import numpy as np
from openai import AsyncOpenAI

from app.rag3.errors import RagError
from app.rag3.settings import RagSettings

#封装向量 API
class EmbeddingService:
    def __init__(self, settings: RagSettings):
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        self.space_id = f"{settings.embedding_base_url.rstrip('/')}|{self.model}|{self.dimensions}"
        self.client = AsyncOpenAI(
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
            timeout=30.0, max_retries=1,
        )

        async def embed(self, texts: list[str]) -> list[np.ndarray]:
            vectors: list[np.ndarray] = []
            for start in range(0, len(texts), 32):
                batch = texts[start:start + 32]
                # 默认使用 text-embedding-3-small 的 1536 维，不发送厂商特有 dimensions。
                response = await self.client.embeddings.create(model=self.model, input=batch)
                # 用响应 index 恢复输入顺序
                items = sorted(response.data, key=lambda item: item.index)
                # 检查漏项、重复项、越界项
                if [item.index for item in items] != list(range(len(batch))):
                    raise RagError("BAD_EMBEDDING", "向量返回数量或顺序异常", 502)
                for item in items:
                    vector = np.asarray(item.embedding, dtype=np.float32)
                    if (vector.shape != (self.dimensions,) or not np.isfinite(vector).all()
                            or np.linalg.norm(vector) == 0):
                        raise RagError("BAD_EMBEDDING", "向量维度或数值异常", 502)
                    vectors.append(vector)
            return vectors

        async def close(self):
            await self.client.close()