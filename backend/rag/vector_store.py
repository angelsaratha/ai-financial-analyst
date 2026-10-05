"""
Builds/loads a FAISS index over document chunks and exposes similarity
search. This is the retrieval half of RAG: chunk text -> embeddings ->
FAISS -> top-k relevant chunks for a question.
"""
import os
import pickle
from typing import List

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from backend.config import VECTOR_STORE_DIR, OPENAI_EMBEDDING_MODEL, require_api_key
from backend.rag.chunking import Chunk

INDEX_PATH = os.path.join(VECTOR_STORE_DIR, "faiss_index")
METADATA_PATH = os.path.join(VECTOR_STORE_DIR, "chunks.pkl")


def _get_embeddings():
    require_api_key()
    return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)


def build_or_update_index(chunks: List[Chunk]) -> int:
    """Embeds the given chunks and adds them to the FAISS index on disk,
    creating the index if it doesn't exist yet. Returns number of chunks added."""
    if not chunks:
        return 0

    documents = [
        Document(
            page_content=c.text,
            metadata={"source_file": c.source_file, "page": c.page, "chunk_id": c.chunk_id},
        )
        for c in chunks
    ]

    embeddings = _get_embeddings()

    if os.path.exists(INDEX_PATH):
        store = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        store.add_documents(documents)
    else:
        store = FAISS.from_documents(documents, embeddings)

    store.save_local(INDEX_PATH)

    # keep a flat log of what's indexed, mainly for the /documents endpoint
    existing = []
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "rb") as f:
            existing = pickle.load(f)
    existing.extend([c.source_file for c in chunks])
    with open(METADATA_PATH, "wb") as f:
        pickle.dump(existing, f)

    return len(documents)


def similarity_search(query: str, k: int = 4):
    """Returns top-k (Document, score) pairs, or [] if nothing indexed yet."""
    if not os.path.exists(INDEX_PATH):
        return []
    embeddings = _get_embeddings()
    store = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    return store.similarity_search_with_score(query, k=k)


def indexed_documents() -> List[str]:
    if not os.path.exists(METADATA_PATH):
        return []
    with open(METADATA_PATH, "rb") as f:
        sources = pickle.load(f)
    return sorted(set(sources))
