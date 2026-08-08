from langchain_core.prompts import ChatPromptTemplate
from src.api.v1.schemas.query_schema import AgentResponse
from src.api.v1.states.rag_state import RAGState
from src.core.llm import get_llm
from src.core.prompts import RESPONSE_GENERATOR_PROMPT


def response_generator_tool(state: RAGState) -> RAGState:
    """
    Generates the grounded response using:
    - RAG context for RAG queries
    - SQL results for SQL queries
    - Both for hybrid queries
    """
    context = ""
    reranked_chunks = state.get("reranked_chunks", [])
    if reranked_chunks:
        context = "\n\n".join(chunk["content"] for chunk in reranked_chunks)
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
    print("QUERY TYPE:", state["query_type"])
    print("QUESTION:", state["question"])
    print("CONTEXT LENGTH:", len(context))
    print("SQL RESULT:", state.get("sql_result", []))
    print("RAG RESULT:", result)
    print("RESULT ANSWER:", repr(result.answer))
    print("RESULT CITATIONS:", result.citations)
    print("RESULT CONFIDENCE:", result.confidence_score)
    state["answer"] = result.answer
    generated_answer = result.answer.strip()
    # Store according to query type
    if state["query_type"] == "rag":
        state["rag_answer"] = generated_answer
    elif state["query_type"] == "sql":
        state["sql_answer"] = generated_answer
    elif state["query_type"] == "hybrid":
        # For hybrid, the LLM receives both RAG + SQL
        # and generates one combined answer.
        state["rag_answer"] = generated_answer
    state["citations"] = result.citations
    state["confidence_score"] = result.confidence_score
    return state
