# import os
# from langchain_core.prompts import ChatPromptTemplate
# from src.api.v1.schemas.query_schema import AgentResponse
# from src.api.v1.states.rag_state import RAGState
# from src.core.llm import get_llm
# from src.core.prompts import RESPONSE_GENERATOR_PROMPT


# def response_generator_tool(state: RAGState) -> RAGState:
#     reranked_chunks = state.get("reranked_chunks", [])
#     print("RERANKED CHUNKS:", len(reranked_chunks))
#     context = "\n\n".join(chunk["content"] for chunk in reranked_chunks)
#     print("CONTEXT LENGTH:", len(context))
#     print("SQL RESULT:", state.get("sql_result", []))
#     llm = get_llm()
#     structured_llm = llm.with_structured_output(AgentResponse)
#     prompt = ChatPromptTemplate.from_template(RESPONSE_GENERATOR_PROMPT)
#     response_chain = prompt | structured_llm
#     images = extract_image_urls(state)
#     state["response_sources"] = images
#     result = response_chain.invoke(
#         {
#             "question": state["question"],
#             "query_type": state["query_type"],
#             "context": context,
#             "sql_result": state.get("sql_result", []),
#         }
#     )
#     print("RAW RESULT:", result)
#     state["answer"] = result.answer
#     state["citations"] = result.citations
#     state["confidence_score"] = result.confidence_score
#     return state


# def extract_image_urls(state):
#     images = []
#     for chunk in state.get("reranked_chunks", []):
#         metadata = chunk.get("metadata", {})
#         # Only process image chunks
#         if metadata.get("type") != "image":
#             continue
#         image_path = metadata.get("image_path")
#         rerank_score = chunk.get("rerank_score", 0)
#         print("IMAGE CANDIDATE:", image_path, "RERANK SCORE:", rerank_score)
#         # Only include strongly relevant images
#         if rerank_score < 0.20:
#             continue
#         if image_path:
#             filename = os.path.basename(image_path)
#             image_url = f"/images/{filename}"
#             if image_url not in images:
#                 images.append(image_url)
#     return images


import os
from langchain_core.prompts import ChatPromptTemplate
from src.api.v1.schemas.query_schema import AgentResponse
from src.api.v1.states.rag_state import RAGState
from src.core.llm import get_llm
from src.core.prompts import RESPONSE_GENERATOR_PROMPT


def response_generator_tool(state: RAGState) -> RAGState:
    reranked_chunks = state.get("reranked_chunks", [])
    print("RERANKED CHUNKS:", len(reranked_chunks))
    context = "\n\n".join(chunk.get("content", "") for chunk in reranked_chunks)
    print("CONTEXT LENGTH:", len(context))
    print("SQL RESULT:", state.get("sql_result", []))
    # Extract related images
    images = extract_image_urls(state)
    print("\n IMAGE URLS ")
    print(images)
    state["response_sources"] = images
    # Generate final structured response
    llm = get_llm()
    structured_llm = llm.with_structured_output(AgentResponse)
    prompt = ChatPromptTemplate.from_template(RESPONSE_GENERATOR_PROMPT)
    response_chain = prompt | structured_llm
    result = response_chain.invoke(
        {
            "question": state["question"],
            "query_type": state["query_type"],
            "context": context,
            "sql_result": state.get("sql_result", []),
        }
    )
    print("RAW RESULT:", result)
    state["answer"] = result.answer
    state["citations"] = result.citations
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
            image_url = f"http://127.0.0.1:8000/images/{filename}"
            if image_url not in images:
                images.append(image_url)
    return images
