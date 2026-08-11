from langchain_core.prompts import ChatPromptTemplate
from src.api.v1.schemas.query_schema import AgentResponse
from src.api.v1.states.rag_state import RAGState
from src.core.llm import get_llm
from src.core.prompts import RESPONSE_GENERATOR_PROMPT


def response_generator_tool(state: RAGState) -> RAGState:
    reranked_chunks = state.get("reranked_chunks", [])
    print("RERANKED CHUNKS:", len(reranked_chunks))
    context = "\n\n".join(chunk["content"] for chunk in reranked_chunks)
    print("CONTEXT LENGTH:", len(context))
    print("SQL RESULT:", state.get("sql_result", []))
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
