import os
from langchain_core.prompts import ChatPromptTemplate
from src.api.v1.schemas.query_schema import AgentResponse
from src.api.v1.states.rag_state import RAGState
from src.core.llm import get_llm
from src.core.prompts import RESPONSE_GENERATOR_PROMPT


def response_generator_tool(state: RAGState) -> RAGState:
    """
    Generates the final grounded response.
    RAG:
        Uses reranked_chunks.
    SQL:
        Uses sql_result.
    Hybrid:
        Uses final_context containing both
        RAG and SQL context.
    """
    query_type = state.get("query_type", "")
    print("RESPONSE QUERY TYPE:", query_type)
    reranked_chunks = state.get("reranked_chunks", [])
    print("RERANKED CHUNKS:", len(reranked_chunks))
    rag_context = "\n\n".join(chunk.get("content", "") for chunk in reranked_chunks)
    print("RAG CONTEXT LENGTH:", len(rag_context))
    sql_result = state.get("sql_result", [])
    print("SQL RESULT:", sql_result)
    final_context = state.get("final_context", {})
    if query_type == "hybrid":
        hybrid_rag_context = final_context.get("rag_context", reranked_chunks)
        hybrid_sql_context = final_context.get("sql_context", sql_result)
        rag_context = "\n\n".join(
            chunk.get("content", "") for chunk in hybrid_rag_context
        )
        sql_result = hybrid_sql_context
        print("HYBRID RAG CONTEXT LENGTH:", len(rag_context))
        print("HYBRID SQL RESULT:", sql_result)
    images = extract_image_urls(state)
    print("\nIMAGE URLS:")
    print(images)
    state["response_sources"] = images
    llm = get_llm()
    structured_llm = llm.with_structured_output(AgentResponse)
    prompt = ChatPromptTemplate.from_template(RESPONSE_GENERATOR_PROMPT)
    response_chain = prompt | structured_llm
    result = response_chain.invoke(
        {
            "question": state["question"],
            "query_type": query_type,
            "context": rag_context,
            "sql_result": sql_result,
        }
    )
    print("RAW RESULT:", result)
    state["answer"] = result.answer
    state["citations"] = result.citations
    if reranked_chunks:
        best_rerank_score = max(
            chunk.get("rerank_score", 0.0) for chunk in reranked_chunks
        )
    else:
        best_rerank_score = 0.0
    state["confidence_score"] = result.confidence_score
    return state


def extract_image_urls(state: RAGState):
    images = []
    for chunk in state.get("reranked_chunks", []):
        metadata = chunk.get("metadata", {})
        content_type = metadata.get("content_type")
        image_type = metadata.get("type")
        if content_type == "image" or image_type == "image":
            image_path = metadata.get("image_path")
            if not image_path:
                continue
            filename = os.path.basename(image_path)
            image_url = "http://127.0.0.1:8000/" f"images/{filename}"
            if image_url not in images:
                images.append(image_url)
    return images
