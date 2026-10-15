from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

# 读取运行配置，类似 Java @ConfigurationProperties
class RagSettings(BaseSettings):
    # 忽略与当前配置类无关的额外配置
    model_config: SettingsConfigDict(extra="ignore")
    database_url: str = "postgresql://postgres:Zj931110@101.35.29.66:5432/copilot"
    # 没有默认值，是启动时必须提供的字段
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"
    embedding_api_key: str
    embedding_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_model: str = "qwen3.7-text-embedding-flash"
    # 表中固定 vector(1536)，换维度需要新表/迁移并重新向量化。
    embedding_dimensions: int = 1536

@lru_cache # 配置对象只初始化一次
def get_rag_settings() -> RagSettings:
    # 第一次调用读取配置，之后复用同一个结果
    settings = RagSettings()
    if settings.embedding_dimensions != 1536:
        raise ValueError("本周 schema 固定 vector(1536)，请先迁移数据库再改维度")
    return settings

