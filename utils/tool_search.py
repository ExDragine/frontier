from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

try:
    from langchain.agents.middleware import AgentMiddleware
except ImportError, AttributeError:  # pragma: no cover - test stubs may omit middleware base classes

    class AgentMiddleware:  # type: ignore[no-redef]
        pass


try:
    from langchain.messages import ToolMessage
except ImportError, AttributeError:  # pragma: no cover - lightweight fallback for tests/stubs

    @dataclass
    class ToolMessage:  # type: ignore[no-redef]
        content: str
        tool_call_id: str


logger = logging.getLogger(__name__)

_ASCII_RE = re.compile(r"[a-zA-Z0-9]+")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")

_ALIASES_BY_GROUP = {
    "research": ("搜索", "检索", "论文", "paper", "arxiv", "百科", "wikipedia", "bilibili", "网页"),
    "astro": ("天文", "空间站", "卫星", "火箭", "极光", "太阳", "彗星", "aurora", "rocket", "satellite"),
    "earth": ("天气", "地震", "雷达", "云图", "earthquake", "weather", "radar"),
    "memory": ("记忆", "聊天记录", "历史消息", "搜索消息", "回忆"),
    "divination": ("占卜", "塔罗", "易经", "卦", "tarot", "iching"),
    "media": ("图片", "绘图", "视频", "生成", "paint", "video"),
    "external": ("外部", "mcp", "connector", "插件"),
}

_ALIASES_BY_MODULE = {
    "arxiv": ("论文", "paper", "学术", "预印本"),
    "aurora": ("极光", "aurora"),
    "comet": ("彗星", "comet"),
    "earthquake": ("地震", "震中", "震级"),
    "heavens_above": ("空间站", "iss", "过境", "卫星观测"),
    "rocket": ("火箭", "发射", "launch"),
    "satellite": ("卫星", "云图", "遥感"),
    "space_weather": ("太阳风", "太阳耀斑", "空间天气"),
    "tavily": ("网页", "联网", "搜索"),
    "tarot": ("塔罗", "牌阵"),
    "iching": ("易经", "卦象"),
    "weather": ("天气", "风场", "火星天气"),
}


@dataclass(slots=True)
class ToolSearchConfig:
    enabled: bool = False
    top_k: int = 8
    expanded_top_k: int = 20
    semantic_enabled: bool = True
    bm25_weight: float = 0.65
    vector_weight: float = 0.35
    embedding_model: str = "microsoft/harrier-oss-v1-0.6b"
    embedding_device: str | None = "cpu"
    embedding_batch_size: int = 1

    @classmethod
    def from_env(cls) -> ToolSearchConfig:
        from utils.configs import EnvConfig

        return cls(
            enabled=EnvConfig.TOOL_SEARCH_ENABLED,
            top_k=EnvConfig.TOOL_SEARCH_TOP_K,
            expanded_top_k=EnvConfig.TOOL_SEARCH_EXPANDED_TOP_K,
            semantic_enabled=EnvConfig.TOOL_SEARCH_SEMANTIC_ENABLED,
            embedding_model=EnvConfig.VECTOR_MEMORY_EMBEDDING_MODEL,
            embedding_device=EnvConfig.VECTOR_MEMORY_EMBEDDING_DEVICE or None,
            embedding_batch_size=EnvConfig.VECTOR_MEMORY_EMBEDDING_BATCH_SIZE,
        )

    def to_vector_config(self):
        from utils.message_vector_index import MessageVectorIndexConfig

        return MessageVectorIndexConfig(
            enabled=True,
            embedding_model=self.embedding_model,
            embedding_batch_size=max(1, self.embedding_batch_size),
            embedding_device=self.embedding_device,
        )


@dataclass(slots=True)
class ToolMetadata:
    tool: Any
    module: str = ""
    group: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)
    name: str = ""
    description: str = ""
    argument_names: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name:
            self.name = self.name_for(self.tool)
        if not self.description:
            self.description = str(getattr(self.tool, "description", None) or getattr(self.tool, "__doc__", "") or "")
        if not self.argument_names:
            args = getattr(self.tool, "args", None)
            schema_fields = getattr(getattr(self.tool, "args_schema", None), "model_fields", None)
            self.argument_names = tuple(args if isinstance(args, dict) else schema_fields or ())

    @staticmethod
    def name_for(tool: Any) -> str:
        return str(getattr(tool, "name", None) or getattr(tool, "__name__", ""))

    @property
    def document(self) -> str:
        parts = (
            self.name,
            self.name.replace("_", " "),
            self.description,
            self.module,
            self.module.replace("_", " "),
            self.group,
            *_ALIASES_BY_GROUP.get(self.group, ()),
            *_ALIASES_BY_MODULE.get(self.module, ()),
            *self.aliases,
            *self.argument_names,
        )
        return " ".join(str(part) for part in parts if part)

    @classmethod
    def from_tool(cls, tool: Any, value: Any | None = None) -> ToolMetadata:
        if isinstance(value, ToolMetadata):
            return cls(tool=tool, module=value.module, group=value.group, aliases=value.aliases)
        if not isinstance(value, dict):
            return cls(tool=tool)

        aliases = value.get("aliases", ())
        if isinstance(aliases, str):
            aliases = (aliases,)
        return cls(
            tool=tool,
            module=str(value.get("module", "") or ""),
            group=str(value.get("group", "") or ""),
            aliases=tuple(str(alias) for alias in aliases),
        )


@dataclass(slots=True)
class ToolSearchResult:
    metadata: ToolMetadata
    score: float
    bm25_score: float = 0.0
    vector_score: float = 0.0

    @property
    def tool(self) -> Any:
        return self.metadata.tool


class ToolSearchIndex:
    def __init__(
        self,
        tools: list[Any] | list[ToolMetadata],
        *,
        metadata_by_name: dict[str, Any] | None = None,
        config: ToolSearchConfig | None = None,
        embeddings: Any | None = None,
    ):
        metadata_by_name = metadata_by_name or {}
        self.config = config or ToolSearchConfig()
        self._metadata = [
            tool
            if isinstance(tool, ToolMetadata)
            else ToolMetadata.from_tool(tool, metadata_by_name.get(ToolMetadata.name_for(tool)))
            for tool in tools
        ]
        self._tools_by_name = {item.name: item.tool for item in self._metadata}
        self._documents = [item.document for item in self._metadata]
        self._tokens = [self._tokenize(document) for document in self._documents]
        self._doc_lengths = [len(tokens) for tokens in self._tokens]
        self._avg_doc_length = sum(self._doc_lengths) / len(self._doc_lengths) if self._doc_lengths else 0.0
        self._idf = {
            token: math.log(1 + (len(self._tokens) - count + 0.5) / (count + 0.5))
            for token, count in Counter(token for tokens in self._tokens for token in set(tokens)).items()
        }
        self._embeddings = embeddings
        self._document_embeddings: list[list[float]] = []
        self.semantic_available = False
        self._init_semantic_index()

    def get_tool(self, name: str) -> Any | None:
        return self._tools_by_name.get(name)

    def search(self, query: str, *, top_k: int | None = None, expanded: bool = False) -> list[ToolSearchResult]:
        limit = top_k or (self.config.expanded_top_k if expanded else self.config.top_k)
        query_tokens = self._tokenize(query)
        if not self._metadata or not query_tokens or limit <= 0:
            return []

        bm25_scores = self._bm25_scores(Counter(query_tokens))
        vector_scores = self._vector_scores(query) if self.semantic_available else [0.0] * len(self._metadata)
        bm25_max = max(bm25_scores, default=0.0)
        vector_max = max(vector_scores, default=0.0)
        query_set = set(query_tokens)

        results = []
        for index, metadata in enumerate(self._metadata):
            bm25_score = bm25_scores[index]
            vector_score = vector_scores[index]
            score = (
                self.config.bm25_weight * (max(0.0, bm25_score) / bm25_max if bm25_max > 0 else 0.0)
                + self.config.vector_weight * (max(0.0, vector_score) / vector_max if vector_max > 0 else 0.0)
                + self._alias_boost(metadata, query_set)
            )
            results.append(ToolSearchResult(metadata, score, bm25_score=bm25_score, vector_score=vector_score))

        if max((item.score for item in results), default=0.0) <= 0:
            return []
        if not self.semantic_available:
            results = [item for item in results if item.score > 0]
        return sorted(results, key=lambda item: (-item.score, item.metadata.group, item.metadata.name))[:limit]

    def _bm25_scores(self, query_counts: Counter[str]) -> list[float]:
        k1 = 1.5
        b = 0.75
        scores = []
        for index, doc_tokens in enumerate(self._tokens):
            term_counts = Counter(doc_tokens)
            doc_length = self._doc_lengths[index]
            score = 0.0
            for token, query_count in query_counts.items():
                frequency = term_counts.get(token, 0)
                if not frequency:
                    continue
                denominator = frequency + k1 * (1 - b + b * doc_length / (self._avg_doc_length or 1))
                score += self._idf.get(token, 0.0) * frequency * (k1 + 1) / denominator * query_count
            scores.append(score)
        return scores

    def _init_semantic_index(self) -> None:
        if not self.config.semantic_enabled or not self._documents:
            return
        try:
            if self._embeddings is None:
                from utils.message_vector_index import get_shared_embeddings

                self._embeddings = get_shared_embeddings(self.config.to_vector_config())
            self._document_embeddings = self._embeddings.embed_documents(self._documents)
            self.semantic_available = True
        except Exception as exc:
            self.semantic_available = False
            self._document_embeddings = []
            logger.warning("Tool semantic search unavailable; falling back to BM25: %s", exc)

    def _vector_scores(self, query: str) -> list[float]:
        try:
            query_embedding = self._embeddings.embed_query(query)
        except Exception as exc:
            self.semantic_available = False
            logger.warning("Tool semantic query failed; falling back to BM25: %s", exc)
            return [0.0] * len(self._metadata)

        scores = []
        for embedding in self._document_embeddings:
            length = min(len(query_embedding), len(embedding))
            dot = sum(float(query_embedding[i]) * float(embedding[i]) for i in range(length))
            query_norm = math.sqrt(sum(float(value) ** 2 for value in query_embedding[:length]))
            document_norm = math.sqrt(sum(float(value) ** 2 for value in embedding[:length]))
            scores.append(max(0.0, dot / (query_norm * document_norm)) if query_norm and document_norm else 0.0)
        return scores

    def _alias_boost(self, metadata: ToolMetadata, query_tokens: set[str]) -> float:
        aliases = (*_ALIASES_BY_GROUP.get(metadata.group, ()), *_ALIASES_BY_MODULE.get(metadata.module, ()))
        boost = 0.04 if any(query_tokens.intersection(self._tokenize(alias)) for alias in aliases) else 0.0
        if metadata.group and metadata.group in query_tokens:
            boost += 0.05
        if metadata.module and query_tokens.intersection(self._tokenize(metadata.module)):
            boost += 0.05
        return boost

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        normalized = text.replace("_", " ").replace("-", " ").lower()
        tokens: list[str] = []
        for match in _ASCII_RE.finditer(normalized):
            token = match.group(0)
            tokens.append(token)
            if len(token) > 3 and token.endswith("s"):
                tokens.append(token[:-1])
        for match in _CJK_RE.finditer(normalized):
            segment = match.group(0)
            for size in (2, 3, 4):
                tokens.extend(segment[index : index + size] for index in range(0, max(0, len(segment) - size + 1)))
            if len(segment) == 1:
                tokens.append(segment)
        return tokens


class DynamicToolSearchMiddleware(AgentMiddleware):
    def __init__(self, index: ToolSearchIndex):
        self.index = index

    def _model_request_with_dynamic_tools(self, request):
        query = build_tool_search_query(getattr(request, "messages", []), state=getattr(request, "state", None))
        selected = self.index.search(query) or self.index.search(query, expanded=True)
        tools = list(getattr(request, "tools", []) or [])
        seen = {ToolMetadata.name_for(tool) for tool in tools}
        for result in selected:
            name = result.metadata.name
            if name and name not in seen:
                tools.append(result.tool)
                seen.add(name)
        return request.override(tools=tools)

    def _tool_request_or_error(self, request):
        tool_call = getattr(request, "tool_call", {}) or {}
        name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", "")
        resolved_tool = self.index.get_tool(str(name)) if name else None
        if resolved_tool is not None:
            return request.override(tool=resolved_tool), None
        if getattr(request, "tool", None) is not None:
            return request, None

        tool_call_id = tool_call.get("id", "") if isinstance(tool_call, dict) else getattr(tool_call, "id", "")
        return None, ToolMessage(content=f"动态工具检索未找到可执行工具：{name}", tool_call_id=str(tool_call_id))

    def wrap_model_call(self, request, handler):
        return handler(self._model_request_with_dynamic_tools(request))

    async def awrap_model_call(self, request, handler):
        return await handler(self._model_request_with_dynamic_tools(request))

    def wrap_tool_call(self, request, handler):
        resolved_request, error = self._tool_request_or_error(request)
        return error if error is not None else handler(resolved_request)

    async def awrap_tool_call(self, request, handler):
        resolved_request, error = self._tool_request_or_error(request)
        return error if error is not None else await handler(resolved_request)


def build_tool_search_query(messages: list[Any], *, state: Any | None = None, max_messages: int = 6) -> str:
    def content_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return " ".join(
                str(item.get("text", "")) if isinstance(item, dict) and item.get("type") == "text" else item
                for item in content
                if isinstance(item, str) or (isinstance(item, dict) and item.get("type") == "text")
            )
        return str(content) if content is not None else ""

    parts = [
        content_text(message.get("content") if isinstance(message, dict) else getattr(message, "content", ""))
        for message in list(messages)[-max_messages:]
    ]

    if isinstance(state, dict):
        user_id, group_id = state.get("user_id"), state.get("group_id")
    else:
        user_id, group_id = getattr(state, "user_id", None), getattr(state, "group_id", None)
    if group_id is not None:
        parts.append(f"group_id:{group_id}")
    if user_id is not None:
        parts.append(f"user_id:{user_id}")
    return "\n".join(part for part in parts if part)
