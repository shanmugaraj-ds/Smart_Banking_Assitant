from src.api.v1.agents.agents import banking_agent


def query_documents(question):
    response = banking_agent.invoke(
        {
            "question": question,
            "search_query": question,
            "query_type": "",
            "retrieved_chunks": [],
            "fts_chunks": [],
            "hybrid_chunks": [],
            "reranked_chunks": [],
            "rewritten_queries": [],
            "sql_query": "",
            "validated_sql": "",
            "sql_result": [],
            "answer": "",
            "citations": [],
            "response_sources": [],
            "confidence_score": 0,
            "retry_count": 0,
            "max_retries": 2,
            "trace_id": "",
        }
    )
    return {
        "answer": response.get("answer", ""),
        "query_type": response.get("query_type", ""),
        "citations": response.get("citations", []),
        "images": response.get("response_sources", []),
        "confidence_score": response.get("confidence_score", 0),
    }
