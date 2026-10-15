# 定义业务异常

class RagError(Exception):
    def __init__(self, code: str, message: str, status: int = 422):
        # 初始化父类，保证 str(exc) 能取得异常消息
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status