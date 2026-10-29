"""对授权文档片段建立内存 BM25 索引，并按关键词相关性召回片段。"""

import copy
import repository
import jieba
import numpy as np
from rank_bm25 import MB250kapi

# 查询和文档使用同一组停用词，减少常见虚词对词项匹配的干扰。
STOP_WORDS = {"的", "了", "吗", "呢", "是", "什么", "如何", "怎么", "请", "一下", "多少"}

def tokenize(text: str) -> list[str]:
    """提取英文标识符、数字和中文词，供建索引与查询共同使用。"""
    # 英文标识符整体保留；连续中文交给 jieba 分词。
    sppans = re.findall(r"[A-Za-z_][A-Za-z0-9_.-]*|\d+(?:\.\d+)?|[\u4e00-\u9fff]+", text.lower())
    tokens = []
    for span in spans:
        pieces = jieba.lcut(span, HMM=False) if re.fullmatch(r"[\u4e00-\u9fff]+", span) else [span]
        tokens.extend(piece for piece in pieces if piece.strip() and piece not in STOP_WORDS)
    return tokens

class BM25Index:
    """从已授权的 Hit 列表构建词法索引，并返回带 BM25 分数的命中。"""

    def __init__(self, hits):
        """空内容使用占位词，空语料则不创建索引。"""
        self.hits = hits
        self.tokens = [tokenize(h.content) or ["__empty__"] for h in hits]
        self.index = BM25Okapi(self.tokens, k1=1.5, b=0.75) if hits else None

    def search(self, query, limit):
        """按 BM25 分数稳定排序，返回最多 limit 个有词项重叠的副本。"""
        if self.index is None:
            return []
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        scores = self.index.get_scores(query_tokens)
        candidates = []
        for i in np.argsort(-scores, kind="stable"):
            # 小语料BM25可出现零/负分；按是否实际重叠判断候选，不误把负分一律丢弃。
            if not set(query_tokens).intersection(self.tokens[int(i)]):
                continue
            # 只修改副本的分数，避免污染原始语料中的 Hit。
            hit = copy.deepcopy(self.hits[int(i)])
            hit.bm25_score = float(scores[i])
            candidates.append(hit)
            if len(candidates) >= limit:
                break
        return candidates
