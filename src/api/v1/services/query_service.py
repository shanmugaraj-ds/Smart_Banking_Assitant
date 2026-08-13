import json
from src.api.v1.agents.agents import banking_agent


def build_initial_state(
    question: str,
    account_id: str | None = None,
    chat_history: list | None = None,
):
    return {
        "question": question,
        "search_query": question,
        "query_type": "",
        "account_id": account_id,
        "retrieved_chunks": [],
        "fts_chunks": [],
        "hybrid_chunks": [],
        "chat_history": chat_history or [],
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


def query_documents(
    question: str,
    account_id: str | None = None,
    chat_history: list | None = None,
):
    response = banking_agent.invoke(
        build_initial_state(
            question,
            account_id=account_id,
            chat_history=chat_history,
        )
    )
    return {
        "answer": response.get("answer", ""),
        "query_type": response.get("query_type", ""),
        "citations": response.get("citations", []),
        "images": response.get("response_sources", []),
        "confidence_score": response.get("confidence_score", 0),
    }


async def query_documents_stream(
    question: str,
    account_id: str | None = None,
    chat_history: list | None = None,
):
    initial_state = build_initial_state(
        question,
        account_id=account_id,
        chat_history=chat_history,
    )
    yield {"type": "status", "message": "Understanding your query..."}
    final_state = initial_state.copy()
    async for update in banking_agent.astream(
        initial_state,
        stream_mode="updates",
    ):
        if not update:
            continue
        for node_name, node_state in update.items():
            if isinstance(node_state, dict):
                final_state.update(node_state)
            yield {
                "type": "status",
                "node": node_name,
                "message": get_node_message(node_name),
            }
    # Final response
    yield {
        "type": "complete",
        "answer": final_state.get("answer", ""),
        "query_type": final_state.get("query_type", ""),
        "citations": final_state.get("citations", []),
        "images": final_state.get("response_sources", []),
        "confidence_score": final_state.get("confidence_score", 0),
    }


def get_node_message(node_name: str):
    messages = {
        "vector_search": ("Searching the knowledge base..."),
        "fts_search": ("Running keyword search..."),
        "hybrid_search": ("Combining search results..."),
        "rerank": ("Reranking the most relevant information..."),
        "reranker": ("Reranking the most relevant information..."),
        "retry": ("Refining the search query..."),
        "sql": ("Checking banking database records..."),
        "sql_generation": ("Preparing database query..."),
        "sql_execution": ("Executing database query..."),
        "response_generator": ("Generating the final answer..."),
        "generate_final_answer": ("Generating the final answer..."),
    }
    return messages.get(node_name, f"Processing: {node_name}")
