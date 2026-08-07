from langgraph.graph import StateGraph, START, END
from src.api.v1.states.rag_state import RAGState
from src.api.v1.tools.classifier_tool import classifier_tool
from src.api.v1.tools.search_tool import vector_search_tool, search_tool
from src.api.v1.tools.response_tool import response_generator_tool
from src.api.v1.tools.sql_tool import (
    sql_generator_tool,
    sql_validator_tool,
    sql_executor_tool,
)

# def rag_node(state: RAGState) -> RAGState:
#     state["answer"] = "RAG pipeline will be implemented."
#     return state


# def sql_node(state: RAGState) -> RAGState:
#     state["answer"] = "SQL pipeline will be implemented."
#     return state


def hybrid_node(state: RAGState) -> RAGState:
    state["answer"] = "Hybrid pipeline will be implemented."
    return state


def route_query(state: RAGState):
    """
    Routes execution based on query classification.
    """
    return state["query_type"]


def build_graph():
    workflow = StateGraph(RAGState)

    workflow.add_node("classifier", classifier_tool)
    workflow.add_node(
        "search",
        search_tool,
    )
    workflow.add_node(
        "vector_search",
        vector_search_tool,
    )
    workflow.add_node(
        "sql_generator",
        sql_generator_tool,
    )
    workflow.add_node(
        "sql_validator",
        sql_validator_tool,
    )
    workflow.add_node(
        "sql_executor",
        sql_executor_tool,
    )
    workflow.add_node(
        "response_generator",
        response_generator_tool,
    )
    workflow.add_node("hybrid", hybrid_node)

    workflow.add_edge(START, "classifier")
    workflow.add_conditional_edges(
        "classifier",
        route_query,
        {
            "rag": "vector_search",
            "sql": "sql_generator",
            "hybrid": "hybrid",
        },
    )
    workflow.add_edge(
        "vector_search",
        "response_generator",
    )
    workflow.add_edge(
        "sql_generator",
        "sql_validator",
    )
    workflow.add_edge(
        "sql_validator",
        "sql_executor",
    )
    workflow.add_edge(
        "sql_executor",
        END,
    )
    workflow.add_edge(
        "sql_executor",
        "response_generator",
    )
    workflow.add_edge(
        "response_generator",
        END,
    )
    workflow.add_edge(
        "hybrid",
        "response_generator",
    )

    return workflow.compile()


graph = build_graph()


def invoke(question: str):
    state = RAGState(
        question=question,
        query_type="",
        retrieved_chunks=[],
        reranked_chunks=[],
        rewritten_queries=[],
        sql_query="",
        sql_result=[],
        answer="",
        citations=[],
        confidence_score=0.0,
        retry_count=0,
        trace_id="",
    )

    return graph.invoke(state)
