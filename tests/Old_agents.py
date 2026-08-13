import os
from langgraph.graph import StateGraph, START, END
from src.api.v1.states.rag_state import RAGState
from src.api.v1.tools.classifier_tool import classifier_tool
from src.api.v1.tools.search_tool import (
    search_tool,
    rewrite_query,
)
from src.api.v1.tools.response_tool import (
    response_generator_tool,
)
from src.api.v1.tools.sql_tool import (
    sql_generator_tool,
    sql_validator_tool,
    sql_executor_tool,
)

RETRY_THRESHOLD = 0.50


def route_query(state: RAGState):
    query_type = state.get("query_type", "out_of_scope")
    allowed_types = {
        "rag",
        "sql",
        "hybrid",
        "conversation",
        "out_of_scope",
    }
    if query_type not in allowed_types:
        return "out_of_scope"
    return query_type


def conversation_node(state: RAGState) -> RAGState:
    state["answer"] = """
    Hello! I can help you with Smart Banking related
        questions, including banking products, policies,
        customer accounts, transactions, loans, cards, 
        and related information."""
    return state


def out_of_scope_node(state: RAGState) -> RAGState:
    state["answer"] = """
        I can help with Smart Banking related questions, 
        including banking products, policies, customer accounts, 
        transactions, loans, cards, and related information."""
    return state


def check_retrieval(state: RAGState):
    chunks = state.get("reranked_chunks", [])
    print("RERANKED CHUNKS:", len(chunks))
    if not chunks:
        if state["retry_count"] < state["max_retries"]:
            print(f"NO CHUNKS -> RETRY " f"{state['retry_count'] + 1}")
            return "retry"
        print("MAX RETRIES REACHED")
        return "response"
    best_score = max(chunk.get("rerank_score", 0.0) for chunk in chunks)
    print("BEST RERANK SCORE:", round(best_score, 4))
    if best_score >= RETRY_THRESHOLD:
        print("RETRIEVAL ACCEPTED")
        return "response"
    if state["retry_count"] < state["max_retries"]:
        print(f"LOW CONFIDENCE -> RETRY " f"{state['retry_count'] + 1}")
        return "retry"
    print("MAX RETRIES REACHED")
    return "response"


def retry_search_node(state: RAGState) -> RAGState:
    """
    Generates an alternate search query.
    Important:
    - Original question remains unchanged.
    - Only search_query is replaced.
    - Maximum retries = max_retries.
    """
    if state["retry_count"] >= state["max_retries"]:
        return state
    rewritten_query = rewrite_query(state)
    if not rewritten_query:
        print("QUERY REWRITE FAILED")
        return state
    state["retry_count"] += 1
    state["rewritten_queries"].append(rewritten_query)
    state["search_query"] = rewritten_query
    print(f"RETRY #{state['retry_count']}: " f"{rewritten_query}")
    return state


def route_after_retry(state: RAGState):
    """
    After query rewriting, return to the appropriate
    retrieval pipeline.
    RAG:
        retry -> search
    HYBRID:
        retry -> hybrid_search
    """
    if state["query_type"] == "hybrid":
        return "hybrid_search"
    return "search"


def hybrid_search_node(state: RAGState) -> RAGState:
    """
    Executes the RAG portion of a hybrid query.
    Vector -> FTS -> RRF -> Reranker
    """
    return search_tool(state)


def sql_pipeline_node(state: RAGState) -> RAGState:
    """
    Executes:
    SQL generation - > SQL validation -> SQL execution
    """
    state = sql_generator_tool(state)
    state = sql_validator_tool(state)
    state = sql_executor_tool(state)
    return state


def route_after_sql(state: RAGState):
    if state["query_type"] == "hybrid":
        return "merge_context"
    return "response"


def merge_context_tool(state: RAGState) -> RAGState:
    """
    Combines RAG and SQL results for hybrid queries.
    """
    state["reranked_chunks"]
    return state


def build_graph():
    workflow = StateGraph(RAGState)
    workflow.add_node("classifier", classifier_tool)
    workflow.add_node("conversation", conversation_node)
    workflow.add_node("search", search_tool)
    workflow.add_node("retry_search", retry_search_node)
    workflow.add_node("hybrid_search", hybrid_search_node)
    workflow.add_node("sql_generator", sql_generator_tool)
    workflow.add_node("sql_validator", sql_validator_tool)
    workflow.add_node("sql_executor", sql_executor_tool)
    workflow.add_node("merge_context", merge_context_tool)
    workflow.add_node("response_generator", response_generator_tool)
    workflow.add_node("out_of_scope", out_of_scope_node)

    workflow.add_edge(START, "classifier")
    workflow.add_conditional_edges(
        "classifier",
        route_query,
        {
            "conversation": "conversation",
            "rag": "search",
            "sql": "sql_generator",
            "hybrid": "hybrid_search",
            "out_of_scope": "out_of_scope",
        },
    )
    workflow.add_conditional_edges(
        "search",
        check_retrieval,
        {
            "retry": "retry_search",
            "response": "response_generator",
        },
    )
    workflow.add_conditional_edges(
        "hybrid_search",
        check_retrieval,
        {
            "retry": "retry_search",
            "response": "sql_generator",
        },
    )
    workflow.add_conditional_edges(
        "retry_search",
        route_after_retry,
        {
            "search": "search",
            "hybrid_search": "hybrid_search",
        },
    )
    workflow.add_edge("sql_generator", "sql_validator")
    workflow.add_edge("sql_validator", "sql_executor")
    workflow.add_conditional_edges(
        "sql_executor",
        route_after_sql,
        {
            "merge_context": "merge_context",
            "response": "response_generator",
        },
    )
    workflow.add_edge("merge_context", "response_generator")
    workflow.add_edge("response_generator", END)
    workflow.add_edge("conversation", END)
    workflow.add_edge("out_of_scope", END)

    return workflow.compile()


banking_agent = build_graph()

graph_image = banking_agent.get_graph().draw_mermaid_png()
with open("banking_agent.png", "wb") as f:
    f.write(graph_image)


def invoke(question: str):
    state = RAGState(
        question=question,
        search_query=question,
        query_type="",
        retrieved_chunks=[],
        fts_chunks=[],
        hybrid_chunks=[],
        reranked_chunks=[],
        rewritten_queries=[],
        sql_query="",
        validated_sql="",
        sql_result=[],
        answer="",
        citations=[],
        response_sources=[],
        confidence_score=0.0,
        retry_count=0,
        trace_id="",
        max_retries=2,
        final_context=dict,
    )

    return banking_agent.invoke(state)
