from pydantic import BaseModel, Field


# 定义请求和响应DTO
class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
        description="用户输入的问题",
    )

class ChatResponse(BaseModel):
    answer: str
    model: str