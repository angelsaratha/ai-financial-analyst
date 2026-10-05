"""
RAG tool: retrieves relevant chunks from indexed financial documents and
asks the LLM to answer using ONLY that retrieved text, with a citation.
This is what stops the model from answering from its own memory.
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from backend.config import OPENAI_CHAT_MODEL, require_api_key
from backend.rag.vector_store import similarity_search

ANSWER_PROMPT = ChatPromptTemplate.from_template(
    """You are a financial analyst. Answer the question using ONLY the
context below, which comes from a company's financial report. If the
context does not contain the answer, say you don't have enough
information in the uploaded documents — do not guess.

Context:
{context}

Question: {question}

Give a concise, specific answer (2-4 sentences)."""
)


def answer_from_documents(question: str, k: int = 4) -> dict:
    require_api_key()
    results = similarity_search(question, k=k)

    if not results:
        return {
            "answer": "No documents have been uploaded/indexed yet, so I can't "
                      "answer from the report. Upload a document first.",
            "sources": [],
        }

    context = "\n\n---\n\n".join(doc.page_content for doc, _score in results)
    llm = ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=0)
    chain = ANSWER_PROMPT | llm
    response = chain.invoke({"context": context, "question": question})

    sources = [
        {
            "source_file": doc.metadata.get("source_file"),
            "page": doc.metadata.get("page"),
            "score": round(float(score), 4),
        }
        for doc, score in results
    ]
    return {"answer": response.content.strip(), "sources": sources}
