from collections import defaultdict
import os
from sqlalchemy import text
from src.api.v1.states.rag_state import RAGState
from src.core.db import get_vector_engine, get_embeddings
from src.core.llm import get_cohere_client, get_llm
from src.core.prompts import QUERY_REWRITE_PROMPT
from langchain_core.prompts import ChatPromptTemplate

RRF_K = 60
RETRY_THRESHOLD = float(os.getenv("RETRY_THRESHOLD", "0.50"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))


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
                        "metadata": row.metadata or {},
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
    engine = get_vector_engine()
    query = state["search_query"]
    sql = text("""
        SELECT
            id,
            content,
            metadata,
            ts_rank(
                search_vector,
                plainto_tsquery(
                    'english',
                    :query
                )
            ) AS score
        FROM smart_banking_chunks
        WHERE search_vector @@
            plainto_tsquery(
                'english',
                :query
            )
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
                    "metadata": row.metadata or {},
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
    chunks = state.get(
        "hybrid_chunks",
        [],
    )
    if isinstance(chunks, dict):
        chunks = chunks.get(
            "chunks",
            [],
        )
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


def rewrite_query(state: RAGState) -> str:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(QUERY_REWRITE_PROMPT)
    chain = prompt | llm
    previous_queries = state.get("rewritten_queries", [])
    result = chain.invoke(
        {
            "question": state["question"],
            "search_query": state["search_query"],
            "previous_queries": "\n".join(previous_queries),
        }
    )
    return result.content.strip()


def retry_tool(state: RAGState) -> RAGState:
    reranked_chunks = state.get(
        "reranked_chunks",
        [],
    )
    if not reranked_chunks:
        should_retry = True
    else:
        best_score = max(
            chunk.get(
                "rerank_score",
                0.0,
            )
            for chunk in reranked_chunks
        )
        print(
            "BEST RERANK SCORE:",
            round(best_score, 4),
        )
        should_retry = best_score < RETRY_THRESHOLD
    if should_retry and state["retry_count"] < MAX_RETRIES:
        state["retry_count"] += 1
        rewritten_query = rewrite_query(state)
        state["rewritten_queries"].append(rewritten_query)
        state["search_query"] = rewritten_query
        print(f"RETRY #{state['retry_count']}: " f"{rewritten_query}")
    return state


def search_tool(state: RAGState) -> RAGState:
    state = vector_search_tool(state)
    state = fts_search_tool(state)
    state = hybrid_search_tool(state)
    state = reranker_tool(state)
    print(
        "VECTOR:",
        len(
            state.get(
                "retrieved_chunks",
                [],
            )
        ),
    )
    print(
        "FTS:",
        len(
            state.get(
                "fts_chunks",
                [],
            )
        ),
    )
    print(
        "HYBRID:",
        len(
            state.get(
                "hybrid_chunks",
                [],
            )
        ),
    )
    print(
        "RERANKED:",
        len(
            state.get(
                "reranked_chunks",
                [],
            )
        ),
    )
    print(
        "RERANK SCORES:",
        [
            round(
                c.get(
                    "rerank_score",
                    0,
                ),
                4,
            )
            for c in state.get(
                "reranked_chunks",
                [],
            )
        ],
    )
    return state
