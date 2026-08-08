import os
from langchain_openai import ChatOpenAI
from src.core.llm import get_llm
from langgraph.graph import StateGraph, START, END
from src.api.v1.states.rag_state import RAGState
from src.api.v1.tools.classifier_tool import classifier_tool
from src.api.v1.tools.search_tool import (
    vector_search_tool,
    fts_search_tool,
    search_tool,
    reranker_tool,
    rewrite_query,
    hybrid_search_tool,
    retry_tool,
)
from src.api.v1.tools.response_tool import response_generator_tool
from src.api.v1.tools.sql_tool import (
    sql_generator_tool,
    sql_validator_tool,
    sql_executor_tool,
)


def route_query(state: RAGState):
    """
    Routes execution based on the query classification.
    """
    return state["query_type"]


def route_after_retrieval(state: RAGState):
    if state["query_type"] == "hybrid":
        return "merge_context"
    return "response"


def check_retrieval(state: RAGState):
    chunks = state.get("reranked_chunks", [])
    if not chunks:
        if state["retry_count"] < state["max_retries"]:
            return "retry"
        return "response"
    best_score = max(chunk.get("rerank_score", 0.0) for chunk in chunks)
    if best_score < 0.50:
        if state["retry_count"] < state["max_retries"]:
            return "retry"
    return "response"


def hybrid_node(state: RAGState) -> RAGState:
    """
    Executes the SQL pipeline for hybrid queries.
    RAG retrieval is handled separately by the search/retry nodes.
    """
    state = sql_generator_tool(state)
    state = sql_validator_tool(state)
    state = sql_executor_tool(state)
    return state


def retry_search_node(state: RAGState) -> RAGState:
    """
    Generates one alternate search phrase and retries retrieval.
    The original user question remains unchanged.
    """
    if state["retry_count"] >= state["max_retries"]:
        return state
    rewritten_query = rewrite_query(state)
    if not rewritten_query:
        return state
    state["retry_count"] += 1
    state["rewritten_queries"].append(rewritten_query)
    state["search_query"] = rewritten_query
    print(f"RETRY #{state['retry_count']}: " f"{rewritten_query}")
    return state


def direct_response_node(state: RAGState) -> RAGState:
    query_type = state.get("query_type")
    if query_type == "out_of_scope":
        state["answer"] = (
            "I don't have answer for this query as it is "
            "out of scope from smart banking assistant."
        )
        state["citations"] = []
        state["confidence_score"] = 1.0
        return state
    if query_type == "chitchat":
        question = state["question"].strip().lower()
        if question in {"hi", "hello", "hey"}:
            state["answer"] = "Hello! How can I help you with your banking query?"
        elif "how are you" in question:
            state["answer"] = (
                "I'm doing well, thank you! "
                "How can I help you with your banking query?"
            )
        elif "thank" in question:
            state["answer"] = "You're welcome! I'm happy to help."
        elif question in {"bye", "goodbye"}:
            state["answer"] = "Goodbye! Have a great day."
        else:
            state["answer"] = (
                "I'm here to help with your banking queries. " "How can I assist you?"
            )
        state["citations"] = []
        state["confidence_score"] = 1.0
        return state
    return state


def build_graph():
    workflow = StateGraph(RAGState)

    workflow.add_node("classifier", classifier_tool)
    workflow.add_node("search", search_tool)
    workflow.add_node("retry_search", retry_search_node)
    workflow.add_node("sql_generator", sql_generator_tool)
    workflow.add_node("sql_validator", sql_validator_tool)
    workflow.add_node("sql_executor", sql_executor_tool)
    workflow.add_node("hybrid", hybrid_node)
    workflow.add_node("response_generator", response_generator_tool)
    workflow.add_node("direct_response", direct_response_node)

    workflow.add_edge(START, "classifier")
    workflow.add_conditional_edges(
        "classifier",
        route_query,
        {
            "rag": "search",
            "sql": "sql_generator",
            "hybrid": "hybrid",
            "chitchat": "direct_response",
            "out_of_scope": "direct_response",
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
    workflow.add_edge("retry_search", "search")
    workflow.add_edge("sql_generator", "sql_validator")
    workflow.add_edge("sql_validator", "sql_executor")
    workflow.add_edge("sql_executor", "response_generator")
    workflow.add_edge("hybrid", "search")
    workflow.add_edge("response_generator", END)
    workflow.add_edge("direct_response", END)

    return workflow.compile()

    graph_image = banking_agent.get_graph().draw_mermaid_png()
    with open("banking_agent.png", "wb") as f:
        f.write(graph_image)


banking_agent = build_graph()


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
        rag_answer="",
        sql_answer="",
    )

    return banking_agent.invoke(state)
