from langchain_core.prompts import ChatPromptTemplate
from src.api.v1.schemas.query_schema import QueryClassification
from src.api.v1.states.rag_state import RAGState
from src.core.llm import get_llm
from src.core.prompts import CLASSIFIER_PROMPT


def classifier_tool(state: RAGState) -> RAGState:
    """
    Classifies the user's query as:
    conversation, out of scope, rag, sql, or hybrid.
    """
    llm = get_llm()
    structured_llm = llm.with_structured_output(QueryClassification)
    prompt = ChatPromptTemplate.from_template(CLASSIFIER_PROMPT)
    classifier_chain = prompt | structured_llm
    chain = prompt | structured_llm
    result = classifier_chain.invoke(
        {
            "question": state["question"],
            "chat_history": state.get("chat_history", []),
        }
    )
    state["query_type"] = result.query_type
    return state
