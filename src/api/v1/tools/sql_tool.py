import re
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import text
from src.api.v1.schemas.query_schema import (
    SQLQuery,
    SQLValidation,
)
from src.api.v1.states.rag_state import RAGState
from src.core.db import get_sql_database
from src.core.llm import get_llm
from src.core.prompts import (
    SQL_GENERATOR_PROMPT,
    SQL_VALIDATOR_PROMPT,
)
from langchain_community.tools.sql_database.tool import (
    QuerySQLDatabaseTool,
    InfoSQLDatabaseTool,
)

db = get_sql_database()
sql_query_tool = QuerySQLDatabaseTool(db=db)
schema_tool = InfoSQLDatabaseTool(db=db)


FORBIDDEN_SQL_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
}


def sql_generator_tool(state: RAGState) -> RAGState:
    """
    Converts a natural language question into a
    PostgreSQL SELECT statement.
    """
    db = get_sql_database()
    schema = db.get_table_info()
    llm = get_llm()
    structured_llm = llm.with_structured_output(SQLQuery)
    prompt = ChatPromptTemplate.from_template(SQL_GENERATOR_PROMPT)
    sql_chain = prompt | structured_llm
    result = sql_chain.invoke(
        {
            "question": state["question"],
            "schema": schema,
        }
    )
    state["sql_query"] = result.sql_query
    return state


def sql_validator_tool(state: RAGState) -> RAGState:
    """
    Validates generated SQL using the LLM validator
    and deterministic safety checks.
    """
    llm = get_llm()
    structured_llm = llm.with_structured_output(SQLValidation)
    prompt = ChatPromptTemplate.from_template(SQL_VALIDATOR_PROMPT)
    validator_chain = prompt | structured_llm
    result = validator_chain.invoke({"sql_query": state["sql_query"]})
    validated_sql = result.validated_sql.strip()
    # Remove trailing semicolon for consistent validation.
    normalized_sql = validated_sql.rstrip(";").strip()
    # Only SELECT statements are permitted.
    if not re.match(
        r"^SELECT\b",
        normalized_sql,
        flags=re.IGNORECASE,
    ):
        raise ValueError("Only SELECT statements are permitted.")
    # Block potentially destructive SQL.
    sql_upper = normalized_sql.upper()
    for keyword in FORBIDDEN_SQL_KEYWORDS:
        if re.search(
            rf"\b{keyword}\b",
            sql_upper,
        ):
            raise ValueError(f"Forbidden SQL operation detected: {keyword}")
    state["validated_sql"] = normalized_sql
    return state


def sql_executor_tool(state: RAGState) -> RAGState:
    """
    Executes validated SQL against the read-only
    core banking database.
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
