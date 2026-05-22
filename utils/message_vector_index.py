import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from utils.database import Message

DEFAULT_EMBEDDING_MODEL = "microsoft/harrier-oss-v1-0.6b"
DEFAULT_CHROMA_PATH = "cache/chroma"
DEFAULT_COLLECTION_NAME = "frontier_messages"

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MessageVectorIndexConfig:
    enabled: bool = True
    persist_path: str = DEFAULT_CHROMA_PATH
    collection_name: str = DEFAULT_COLLECTION_NAME
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    top_k: int = 30

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> MessageVectorIndexConfig:
        return cls(
            enabled=bool(value.get("semantic_search_enabled", value.get("enabled", True))),
            persist_path=str(value.get("chroma_path", DEFAULT_CHROMA_PATH)),
            collection_name=str(value.get("chroma_collection", DEFAULT_COLLECTION_NAME)),
            embedding_model=str(value.get("embedding_model", DEFAULT_EMBEDDING_MODEL)),
            top_k=int(value.get("semantic_top_k", 30)),
        )


def message_metadata(message: Message) -> dict[str, int | str]:
    return {
        "time": int(message.time),
        "msg_id": int(message.msg_id) if message.msg_id is not None else -1,
        "user_id": int(message.user_id),
        "group_id": int(message.group_id) if message.group_id is not None else -1,
        "scope": "group" if message.group_id is not None else "private",
        "role": message.role,
        "user_name": message.user_name or "",
    }


def build_chroma_where(
    *,
    group_id: int | None,
    user_id: int | None,
    target_user_id: int | None,
) -> dict[str, Any] | None:
    if group_id is None:
        if user_id is None:
            return None
        return {"$and": [{"scope": "private"}, {"user_id": int(user_id)}]}
    if target_user_id is not None:
        return {"$and": [{"group_id": int(group_id)}, {"user_id": int(target_user_id)}]}
    return {"group_id": int(group_id)}


def _default_embeddings_factory(config: MessageVectorIndexConfig):
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=config.embedding_model)


def _default_collection_factory(config: MessageVectorIndexConfig):
    import chromadb

    client = chromadb.PersistentClient(path=config.persist_path)
    return client.get_or_create_collection(name=config.collection_name)


class MessageVectorIndex:
    def __init__(
        self,
        config: MessageVectorIndexConfig,
        *,
        collection_factory: Callable[[MessageVectorIndexConfig], Any] | None = None,
        embeddings_factory: Callable[[MessageVectorIndexConfig], Any] | None = None,
    ):
        self.config = config
        self._collection = None
        self._embeddings = None
        self.available = False
        if not config.enabled:
            return
        try:
            self._embeddings = (embeddings_factory or _default_embeddings_factory)(config)
            self._collection = (collection_factory or _default_collection_factory)(config)
            self.available = True
        except Exception as exc:
            logger.warning("Chroma message vector index unavailable: %s", exc)

    def add_message(self, message: Message) -> bool:
        if not self.available or self._collection is None or self._embeddings is None:
            return False
        try:
            embedding = self._embeddings.embed_documents([message.content])[0]
            self._write(
                ids=[str(message.time)],
                documents=[message.content],
                embeddings=[embedding],
                metadatas=[message_metadata(message)],
            )
            return True
        except Exception as exc:
            logger.warning("Failed to add message to Chroma index: %s", exc)
            return False

    def add_messages(self, messages: list[Message]) -> int:
        if not self.available or self._collection is None or self._embeddings is None or not messages:
            return 0
        try:
            documents = [message.content for message in messages]
            self._write(
                ids=[str(message.time) for message in messages],
                documents=documents,
                embeddings=self._embeddings.embed_documents(documents),
                metadatas=[message_metadata(message) for message in messages],
            )
            return len(messages)
        except Exception as exc:
            logger.warning("Failed to add message batch to Chroma index: %s", exc)
            return 0

    def _write(self, *, ids: list[str], documents: list[str], embeddings: list, metadatas: list[dict]) -> None:
        writer = getattr(self._collection, "upsert", None) or self._collection.add
        writer(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def search(
        self,
        *,
        query: str,
        group_id: int | None,
        user_id: int | None,
        target_user_id: int | None = None,
        limit: int | None = None,
    ) -> list[tuple[int, float]]:
        if not self.available or self._collection is None or self._embeddings is None:
            return []
        where = build_chroma_where(group_id=group_id, user_id=user_id, target_user_id=target_user_id)
        if where is None:
            return []
        try:
            result = self._collection.query(
                query_embeddings=[self._embeddings.embed_query(query)],
                n_results=max(1, min(limit or self.config.top_k, 500)),
                where=where,
            )
        except Exception as exc:
            logger.warning("Chroma message vector search failed: %s", exc)
            return []

        ids = result.get("ids", [[]])[0] if isinstance(result, dict) else []
        distances = result.get("distances", [[]])[0] if isinstance(result, dict) else []
        return [(int(item_id), float(distances[i] if i < len(distances) else 0.0)) for i, item_id in enumerate(ids)]
