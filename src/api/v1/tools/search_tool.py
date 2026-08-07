from src.api.v1.states.rag_state import RAGState
from src.core.db import get_sql_database, get_vector_engine, get_vector_store
from sqlalchemy import text
from collections import defaultdict
from src.core.llm import get_cohere_client, get_llm
from langchain_core.prompts import ChatPromptTemplate
from src.core.prompts import QUERY_REWRITE_PROMPT
import os

RRF_K = 60


def vector_search_tool(state: RAGState) -> RAGState:
    """
    Performs semantic similarity search against PGVector.
    """
    vector_store = get_vector_store()
    try:
        docs = vector_store.similarity_search_with_score(
            query=state["search_query"],
            k=20,
        )
    except Exception:
        state["retrieved_chunks"] = []
        return state

    retrieved_chunks = []
    for doc, score in docs:
        retrieved_chunks.append(
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            }
        )
    state["retrieved_chunks"] = retrieved_chunks
    return state


def fts_search_tool(state: RAGState) -> RAGState:
    """
    Performs PostgreSQL Full-Text Search.
    """
    db = get_vector_engine()
    engine = get_vector_engine()
    sql = text("""
        SELECT
            content,
            metadata,
            ts_rank(search_vector,
                    plainto_tsquery(:query)) AS score
        FROM smart_banking_chunks
        WHERE search_vector @@ plainto_tsquery(:query)
        ORDER BY score DESC
        LIMIT :k
        """)
    with engine.connect() as conn:
        result = conn.execute(
            sql,
            {
                "query": state["search_query"],
                "k": 20,
            },
        )
        state["fts_chunks"] = [
            {
                "content": row.content,
                "metadata": row.metadata,
                "score": float(row.score),
            }
            for row in result
        ]
    return state


def hybrid_search_tool(state: RAGState) -> RAGState:
    """
    Combines vector search and FTS search results using
    Reciprocal Rank Fusion (RRF).
    """
    fused_scores = defaultdict(float)
    chunk_lookup = {}
    # Vector Search Results
    for rank, chunk in enumerate(state["retrieved_chunks"], start=1):
        key = chunk["content"]
        fused_scores[key] += 1 / (RRF_K + rank)
        chunk_lookup[key] = chunk
    # FTS Search Results
    for rank, chunk in enumerate(state["fts_chunks"], start=1):
        key = chunk["content"]
        fused_scores[key] += 1 / (RRF_K + rank)
        chunk_lookup[key] = chunk
    ranked_chunks = sorted(
        fused_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    hybrid_chunks = []
    for content, score in ranked_chunks[:20]:
        chunk = chunk_lookup[content]
        chunk["rrf_score"] = score
        chunk["retrieval_method"] = "hybrid"
        hybrid_chunks.append(chunk)
    state["hybrid_chunks"] = hybrid_chunks
    return state


def reranker_tool(state: RAGState) -> RAGState:
    """
    Re-ranks hybrid search results using Cohere Rerank.
    """
    chunks = state["hybrid_chunks"]
    if not chunks:
        state["reranked_chunks"] = []
        return state
    cohere_client = get_cohere_client()
    response = cohere_client.rerank(
        model="rerank-v3.5",
        query=state["question"],
        documents=[chunk["content"] for chunk in chunks],
        top_n=5,
    )
    reranked_chunks = []
    for result in response.results:
        chunk = chunks[result.index].copy()
        chunk["rerank_score"] = float(result.relevance_score)
        reranked_chunks.append(chunk)
    state["reranked_chunks"] = reranked_chunks
    return state


RETRY_THRESHOLD = float(os.getenv("RETRY_THRESHOLD", "0.50"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "1"))


def rewrite_query(state: RAGState) -> str:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(QUERY_REWRITE_PROMPT)

    chain = prompt | llm
    result = chain.invoke({"question": state["question"]})
    return result.content.strip()


def retry_tool(state: RAGState) -> RAGState:
    """
    Determines whether retrieval should be retried.
    """
    reranked_chunks = state["reranked_chunks"]
    if not reranked_chunks:
        should_retry = True
    else:
        best_score = max(chunk.get("rerank_score", 0.0) for chunk in reranked_chunks)
        should_retry = best_score < RETRY_THRESHOLD
    if should_retry and state["retry_count"] < MAX_RETRIES:
        rewritten_query = rewrite_query(state)
        state["rewritten_queries"].append(rewritten_query)
        state["retry_count"] += 1
        # Preserve the original question.
        state["search_query"] = rewritten_query
    else:
        state["search_query"] = state["question"]
    return state


def search_tool(state: RAGState) -> RAGState:
    while True:
        state = vector_search_tool(state)
        state = fts_search_tool(state)
        state = hybrid_search_tool(state)
        state = reranker_tool(state)
        previous_retry_count = state["retry_count"]
        state = retry_tool(state)
        if state["retry_count"] == previous_retry_count:
            break
    return state
