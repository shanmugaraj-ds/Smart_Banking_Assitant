from src.api.v1.states.rag_state import RAGState
from src.core.db import get_vector_engine, get_embeddings
from sqlalchemy import text
from collections import defaultdict
from src.core.llm import get_cohere_client, get_llm
from langchain_core.prompts import ChatPromptTemplate
from src.core.prompts import QUERY_REWRITE_PROMPT
import os

RRF_K = 60


def vector_search_tool(state: RAGState) -> RAGState:
    engine = get_vector_engine()
    embeddings = get_embeddings()
    query = state["search_query"]
    try:
        query_embedding = embeddings.embed_query(query)
        sql = text("""
            SELECT
                id,
                content,
                metadata,
                1 - (
                    embedding <=> CAST(
                        :embedding AS vector
                    )
                ) AS score
            FROM smart_banking_chunks
            ORDER BY
                embedding <=> CAST(
                    :embedding AS vector
                )
            LIMIT :k
            """)
        with engine.connect() as conn:
            result = conn.execute(
                sql,
                {
                    "embedding": str(query_embedding),
                    "k": 20,
                },
            )
            chunks = []
            for row in result:
                chunks.append(
                    {
                        "content": row.content,
                        "metadata": row.metadata,
                        "score": float(row.score),
                        "retrieval_method": "vector",
                    }
                )
        state["retrieved_chunks"] = chunks
    except Exception as e:
        print(f"Vector search error: {e}")
        state["retrieved_chunks"] = []
    return state


def fts_search_tool(state: RAGState) -> RAGState:
    """
    Performs PostgreSQL Full-Text Search.
    """
    engine = get_vector_engine()
    query = state["search_query"]
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
    try:
        with engine.connect() as conn:
            result = conn.execute(
                sql,
                {
                    "query": query,
                    "k": 20,
                },
            )
            state["fts_chunks"] = [
                {
                    "content": row.content,
                    "metadata": row.metadata,
                    "score": float(row.score),
                    "retrieval_method": "fts",
                }
                for row in result
            ]
    except Exception as e:
        print(f"FTS search error: {e}")
        state["fts_chunks"] = []
    return state


def hybrid_search_tool(state: RAGState) -> RAGState:
    """
    Combines Vector Search and FTS using Reciprocal Rank Fusion.
    Produces top 20 hybrid candidates.
    """
    fused_scores = defaultdict(float)
    chunk_lookup = {}
    for rank, chunk in enumerate(
        state.get("retrieved_chunks", []),
        start=1,
    ):
        key = chunk["content"]
        fused_scores[key] += 1 / (RRF_K + rank)
        chunk_lookup[key] = chunk.copy()
    for rank, chunk in enumerate(
        state.get("fts_chunks", []),
        start=1,
    ):
        key = chunk["content"]
        fused_scores[key] += 1 / (RRF_K + rank)
        if key not in chunk_lookup:
            chunk_lookup[key] = chunk.copy()
    ranked_chunks = sorted(
        fused_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )
    hybrid_chunks = []
    for content, score in ranked_chunks[:20]:
        chunk = chunk_lookup[content].copy()
        chunk["rrf_score"] = score
        chunk["retrieval_method"] = "hybrid"
        hybrid_chunks.append(chunk)
    state["hybrid_chunks"] = hybrid_chunks
    return state


def reranker_tool(state: RAGState) -> RAGState:
    """
    Re-ranks hybrid search results using Cohere Rerank.
    """
    chunks = state.get("hybrid_chunks", [])
    if isinstance(chunks, dict):
        chunks = chunks.get("chunks", [])
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
        chunk["retrieval_method"] = "reranked"
        reranked_chunks.append(chunk)
    state["reranked_chunks"] = reranked_chunks
    return state


RETRY_THRESHOLD = float(os.getenv("RETRY_THRESHOLD", "0.50"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))


def rewrite_query(state: RAGState) -> str:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(QUERY_REWRITE_PROMPT)
    chain = prompt | llm
    result = chain.invoke(
        {
            "question": state["question"],
            "search_query": state["search_query"],
        }
    )
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
        pass
    return state


def search_tool(state: RAGState) -> RAGState:
    """
    Complete hybrid retrieval pipeline.

    1. Vector Search -> Top 20
    2. FTS Search -> Top 20
    3. RRF Hybrid Fusion -> Top 20
    4. Cohere Reranker -> Top 5
    """
    state = vector_search_tool(state)
    print("VECTOR:", len(state.get("retrieved_chunks", [])))
    state = fts_search_tool(state)
    print("FTS:", len(state.get("fts_chunks", [])))
    state = hybrid_search_tool(state)
    print("HYBRID:", len(state.get("hybrid_chunks", [])))
    state = reranker_tool(state)
    print("RERANKED:", len(state.get("reranked_chunks", [])))
    print(
        "RERANK SCORES:",
        [
            round(chunk.get("rerank_score", 0.0), 4)
            for chunk in state.get("reranked_chunks", [])
        ],
    )
    return state
