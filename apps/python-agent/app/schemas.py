from pydantic import BaseModel, Field
from uuid import UUID


# 定义请求和响应DTO
class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
        description="用户输入的问题",
    )
    sessionId: UUID | None = None

class ChatResponse(BaseModel):
    sessionId: UUID
    answer: str
    model: str

class ApiError(BaseModel):
    code: str
    message: str