from dataclasses import dataclass

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag3.errors import RagError
from app.rag3.loader import Section

# 把结构段变成检索单元
PIPELINE_VERSION = "rag3-heading-page-char800-overlap120-v1"
ENCODING = tiktoken.get_encoding("cl100k_base")


@dataclass
class Chunk:
    index: int
    content: str
    metadata: dict

def split_sections(sections: list[Section]) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 800, # 字符数
        chunk_overlap=120, # 目标重叠字符数
        length_function=len,
        # 优先段落，其次换行和中文标点
        separators=["\n\n", "\n", "。", "！", "？", ";", "；", "，", " ", ""],
        keep_separator=True,
    )
    result: list[Chunk] = []
    for section in sections:
        for text in splitter.split_text(section.text):
            token_count = len(ENCODING.encode(text, disallowed_special=()))
            if token_count > 3000:
                raise RagError("CHUNK_TOO_LARGE", "Chunk 超出示例 Token 上限")
            result.append(
                # 整份文档内从 0 连续编号
                Chunk(len(result), text, {
                "page": section.page,  # PDF 来源在哪一页
                "heading": section.heading, # 来源属于哪个主题
                "token_count": token_count, # 是否超过上下文预算
                "pipeline_version": PIPELINE_VERSION, # 切分规则变化后如何识别旧数据
            }))
    if not result:
        raise RagError("NO_CHUNKS", "文档没有有效内容")
    if len(result) > 1000:
        raise RagError("TOO_MANY_CHUNKS", "本周同步入库最多 1000 个 Chunk")
    return result