from langchain_core.prompts import ChatPromptTemplate
from src.api.v1.schemas.query_schema import SQLQuery, SQLValidation
from src.api.v1.states.rag_state import RAGState
from src.core.db import get_sql_database
from src.core.llm import get_llm
from sqlalchemy import text
from src.core.prompts import SQL_GENERATOR_PROMPT, SQL_VALIDATOR_PROMPT

llm = get_llm()

structured_llm = llm.with_structured_output(SQLQuery)
prompt = ChatPromptTemplate.from_template(SQL_GENERATOR_PROMPT)
sql_chain = prompt | structured_llm


def sql_generator_tool(state: RAGState) -> RAGState:
    """
    Converts a natural language question into a PostgreSQL SELECT statement.
    """
    db = get_sql_database()
    schema = db.get_table_info()
    result = sql_chain.invoke(
        {
            "question": state["question"],
            "schema": schema,
        }
    )
    state["sql_query"] = result.sql_query
    return state


structured_llm = llm.with_structured_output(SQLValidation)
prompt = ChatPromptTemplate.from_template(SQL_VALIDATOR_PROMPT)
validator_chain = prompt | structured_llm


def sql_validator_tool(state: RAGState) -> RAGState:
    """
    Validates SQL before execution.
    """
    result = validator_chain.invoke({"sql_query": state["sql_query"]})
    state["validated_sql"] = result.validated_sql
    return state


def sql_executor_tool(state: RAGState) -> RAGState:
    """
    Executes validated SQL against the read-only database.
    """
    db = get_sql_database()
    engine = db._engine
    try:
        with engine.connect() as conn:
            result = conn.execute(text(state["validated_sql"]))
            state["sql_result"] = [dict(row._mapping) for row in result]
    except Exception as error:
        state["sql_result"] = []
        state["answer"] = f"SQL Execution Error: {str(error)}"
    return state
