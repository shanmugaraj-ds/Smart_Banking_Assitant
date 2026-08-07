from langchain_core.prompts import ChatPromptTemplate
from src.api.v1.schemas.query_schema import AgentResponse
from src.api.v1.states.rag_state import RAGState
from src.core.llm import get_llm
from src.core.prompts import RESPONSE_GENERATOR_PROMPT

llm = get_llm()

structured_llm = llm.with_structured_output(AgentResponse)
prompt = ChatPromptTemplate.from_template(RESPONSE_GENERATOR_PROMPT)
response_chain = prompt | structured_llm


def response_generator_tool(
    state: RAGState,
) -> RAGState:
    """
    Generates the final grounded response.
    """
    context = ""
    if state["reranked_chunks"]:
        context = "\n\n".join(chunk["content"] for chunk in state["reranked_chunks"])
    result = response_chain.invoke(
        {
            "question": state["question"],
            "sql_result": state["sql_result"],
            "context": context,
        }
    )
    state["answer"] = result.answer
    state["citations"] = result.citations
    state["confidence_score"] = result.confidence_score
    return state
