from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_docling.loader import DoclingLoader, ExportType
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from langchain_core.tools import tool, create_retriever_tool
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


async def base_web_extract(url):
    docs = WebBaseLoader(url).load()
    docs_list = [item for item in docs]
    text_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        tokenizer=HuggingFaceTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2"),
        chunk_size=1024,
        chunk_overlap=50,
    )
    doc_splites = text_splitter.split_documents(docs_list)
    vectorstore = Chroma.from_documents(
        doc_splites,
        collection_name="rag-chroma",
        embedding=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
    )
    retriever = vectorstore.as_retriever()
    retriever_tool = create_retriever_tool(retriever, "retriever_web_page", "Page result")
    return retriever_tool


@tool(response_format="content")
async def web_extract(url: str) -> str:
    """
    从网页提取基本信息

    Args:
        url: 网页URL

    Returns:
        提取的信息
    """
    if not url:
        return "❌ URL不能为空"

    loader = DoclingLoader(
        url,
        export_type=ExportType.MARKDOWN,
        chunker=HybridChunker(
            tokenizer=HuggingFaceTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
        ),
    )
    docs = loader.load()
    texts = "".join([doc.page_content for doc in docs])
    return texts
