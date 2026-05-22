# ruff: noqa: S101


from utils.database import Message
from utils.message_vector_index import (
    DEFAULT_EMBEDDING_MODEL,
    MessageVectorIndex,
    MessageVectorIndexConfig,
    build_chroma_where,
    message_metadata,
)


class FakeEmbeddings:
    def __init__(self):
        self.documents = []
        self.queries = []

    def embed_documents(self, texts):
        self.documents.extend(texts)
        return [[float(len(text)), 1.0, 0.0] for text in texts]

    def embed_query(self, text):
        self.queries.append(text)
        return [float(len(text)), 1.0, 0.0]


class FakeCollection:
    def __init__(self):
        self.added = {}
        self.queries = []

    def add(self, ids, documents, embeddings, metadatas):
        for i, item_id in enumerate(ids):
            self.added[item_id] = {
                "document": documents[i],
                "embedding": embeddings[i],
                "metadata": metadatas[i],
            }

    def query(self, query_embeddings, n_results, where=None):
        self.queries.append({"query_embeddings": query_embeddings, "n_results": n_results, "where": where})
        ids = list(self.added.keys())[:n_results]
        distances = [float(i) for i, _ in enumerate(ids)]
        return {"ids": [ids], "distances": [distances]}


def test_default_vector_config_uses_harrier_model():
    config = MessageVectorIndexConfig.from_mapping({})

    assert config.enabled is True
    assert config.embedding_model == DEFAULT_EMBEDDING_MODEL
    assert config.persist_path == "cache/chroma"


def test_message_metadata_normalizes_private_and_group_scope():
    private = message_metadata(
        Message(time=1, msg_id=10, user_id=100, group_id=None, user_name="Alice", role="user", content="hello")
    )
    group = message_metadata(
        Message(time=2, msg_id=11, user_id=101, group_id=123, user_name=None, role="assistant", content="world")
    )

    assert private["scope"] == "private"
    assert private["group_id"] == -1
    assert group["scope"] == "group"
    assert group["group_id"] == 123


def test_vector_index_adds_and_queries_messages_with_scope_filter():
    collection = FakeCollection()
    embeddings = FakeEmbeddings()
    index = MessageVectorIndex(
        MessageVectorIndexConfig(enabled=True),
        collection_factory=lambda _config: collection,
        embeddings_factory=lambda _config: embeddings,
    )
    message = Message(
        time=1000,
        msg_id=10,
        user_id=1,
        group_id=123,
        user_name="Alice",
        role="user",
        content="SQLite 性能优化",
    )

    assert index.add_message(message) is True
    results = index.search(query="数据库性能", group_id=123, user_id=1, limit=5)

    assert collection.added["1000"]["document"] == "SQLite 性能优化"
    assert collection.added["1000"]["metadata"]["group_id"] == 123
    assert collection.queries[0]["where"] == {"group_id": 123}
    assert results == [(1000, 0.0)]


def test_build_chroma_where_uses_private_scope_for_private_search():
    assert build_chroma_where(group_id=None, user_id=456, target_user_id=None) == {
        "$and": [{"scope": "private"}, {"user_id": 456}]
    }
    assert build_chroma_where(group_id=123, user_id=456, target_user_id=789) == {
        "$and": [{"group_id": 123}, {"user_id": 789}]
    }


def test_vector_index_disables_itself_when_initialization_fails():
    index = MessageVectorIndex(
        MessageVectorIndexConfig(enabled=True),
        collection_factory=lambda _config: (_ for _ in ()).throw(RuntimeError("boom")),
        embeddings_factory=lambda _config: FakeEmbeddings(),
    )
    message = Message(time=1, msg_id=1, user_id=1, group_id=None, user_name=None, role="user", content="hello")

    assert index.available is False
    assert index.add_message(message) is False
    assert index.search(query="hello", group_id=None, user_id=1, limit=5) == []
