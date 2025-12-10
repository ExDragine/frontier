import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


class MemoryStore:
    def __init__(self) -> None:
        self.embeddings = HuggingFaceEmbeddings(model_name="")
        self.persistent_client = chromadb.PersistentClient("./caches/chroma")

    async def add(self, collection_name: str, documents: list, uuids: list):
        docs_iter = (Document(page_content=text) for text in documents)
        memory_store = Chroma(
            client=self.persistent_client,
            collection_name=collection_name,
            embedding_function=self.embeddings,
        )
        await memory_store.aadd_documents(documents=list(docs_iter), ids=uuids)

    async def delete(self, collection_name: str, ids: list):
        memory_store = Chroma(
            client=self.persistent_client,
            collection_name=collection_name,
            embedding_function=self.embeddings,
        )
        await memory_store.adelete(ids=ids)

    async def similarity_search(self, collection_name: str, query: str, filter: dict):
        memory_store = Chroma(
            client=self.persistent_client,
            collection_name=collection_name,
            embedding_function=self.embeddings,
        )

        results = await memory_store.asimilarity_search(query=query, k=2, filter=filter)
        return "".join(f"* {res.page_content}\n" for res in results)

    async def mmr_search(self, collection_name: str, query: str, result_number: int, filter: dict):
        memory_store = Chroma(
            client=self.persistent_client,
            collection_name=collection_name,
            embedding_function=self.embeddings,
        )

        retriever = memory_store.as_retriever(search_type="mmr", search_kwargs={"k": result_number, "fetch_k": 5})
        results = await retriever.ainvoke(query, filter=filter)
        return "".join(f"* {res.page_content}\n" for res in results)
