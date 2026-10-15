import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.rag3.errors import RagError

# RAG 文件解析器，负责读取文本

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_PAGES = 200
MAX_TEXT_CHARS = 500_000

@dataclass
class Section:
    text: str
    # PDF 的物理页码，从 1 开始
    page: int | None = None
    # Markdown 的标题路径
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
                    # 每页单独保存定位信息
                    sections.append(Section(text=text, page=page_no))
                else:
                    warnings.append(f"第 {page_no} 页无可提取文本，可能需要 OCR")
        except RagError:
            raise
        except Exception as exc:
            raise RagError("INVALID_PDF", "PDF 解析失败") from exc
    else:
        try:
            # 兼容带 BOM 的 UTF-8 文件
            # 统一换行，移除 NUL 字符
            text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\x00", "")
        except UnicodeDecodeError as exc:
            raise RagError("INVALID_ENCODING", "请将文本转为 UTF-8 后上传") from exc
        if suffix == ".txt":
            sections = [Section(text.strip())] if text.strip() else []
        else:
            # 简化 Markdown 解析：ATX 标题 + fenced code，不处理 Setext/HTML。
            headings: dict[int, str] = {}
            buffer: list[str] = []
            heading = None
            fence: str | None = None
            for line in text.splitlines():
                stripped = line.lstrip()
                if stripped.startswith(("```", "~~~")):
                    marker = stripped[:3]
                    if fence is None:
                        fence = marker
                    elif fence == marker:
                        fence = None
                match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line) if fence is None else None
                if match:
                    if "\n".join(buffer).strip():
                        sections.append(Section("\n".join(buffer).strip(), heading=heading))
                    level = len(match[1])
                    headings = {k: v for k, v in match.groupdict().items() if k < level}
                    headings[level] = match[2]
                    heading = " / ".join(headings.values())
                    buffer = [line]
                else:
                    buffer.append(line)
            if "\n".join(buffer).strip():
                sections.append(Section("\n".join(buffer).strip(), heading=heading))
    if not sections:
        raise RagError("NO_EXTRACTABLE_TEXT", "没有可提取文本；扫描 PDF 请先 OCR")
    if sum(len(s.text) for s in sections) > MAX_TEXT_CHARS:
        raise RagError("TEXT_TOO_LARGE", "提取文本过大，请拆分文档")
    return sections, warnings

