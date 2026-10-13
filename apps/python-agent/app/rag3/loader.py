import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.rag3.errors import RagError

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_PAGES = 200
MAX_TEXT_CHARS = 500_000

@dataclass
class Section:
    text: str
    page: int | None = None
    heading:str | None = None

def load_section(filename: str, data: bytes) -> tuple[list[Section], list[str]]:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".md", ".txt"}:
        raise RagError("UNSUPPORTED_FILE", "仅支持 PDF、Markdown、TXT", 415)
    if not data:
        raise RagError("EMPTY_FILE", "文件为空")
    if len(data) > MAX_FILE_BYTES:
        raise RagError("FILE_TOO_LARGE", "文件不能超过 10 MiB", 413)
    sections: list[Section] = []
    warnings: list[str] = []
    if suffix == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise RagError("INVALID_PDF", "文件内容不是有效 PDF")
        try:
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                raise RagError("ENCRYPTED_PDF", "请先解密 PDF")
            if len(reader.pages) > MAX_PAGES:
                raise RagError("TOO_MANY_PAGES", "本周示例最多支持 200 页")
            total_chars = 0
            for page_no, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                total_chars += len(text)
                if total_chars > MAX_TEXT_CHARS:
                    raise RagError("TEXT_TOO_LARGE", "提取文本过大，请拆分文档")
                if text:
                    sections.append(Section(text=text, page=page_no))
                else:
                    warnings.append(f"第 {page_no} 页无可提取文本，可能需要 OCR")
        except RagError:
            raise
        except Exception as exc:
            raise RagError("INVALID_PDF", "PDF 解析失败") from exc
    else:
        try:
            text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\x00", "")
        except UnicodeDecodeError as exc:
            raise RagError("INVALID_ENCODING", "请将文本转为 UTF-8 后上传") from exc
        if suffix == ".txt":
            sections = [Section(text=text, page=page_no)]
