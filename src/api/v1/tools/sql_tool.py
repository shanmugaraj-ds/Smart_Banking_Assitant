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
            "account_id": state.get("account_id", ""),
        }
    )
    state["sql_query"] = result.sql_query
    print("QUESTION:", state.get("question"))
    print("ACCOUNT ID FROM STATE:", repr(state.get("account_id")))
    print("GENERATED SQL:", state.get("sql_query"))
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


def sql_validator_tool(state: RAGState) -> RAGState:
    """
    Validates generated SQL using the LLM validator
    and deterministic safety checks.
    Allows:
    - SELECT
    - WITH ... SELECT (CTEs)
    Blocks all write/destructive operations.
    """
    llm = get_llm()
    structured_llm = llm.with_structured_output(SQLValidation)
    prompt = ChatPromptTemplate.from_template(SQL_VALIDATOR_PROMPT)
    validator_chain = prompt | structured_llm
    result = validator_chain.invoke(
        {
            "sql_query": state["sql_query"],
        }
    )
    validated_sql = result.validated_sql.strip()
    # Remove trailing semicolon
    normalized_sql = validated_sql.rstrip(";").strip()
    if not normalized_sql:
        raise ValueError("Generated SQL is empty.")
    sql_upper = normalized_sql.upper()
    is_select = re.match(
        r"^SELECT\b",
        normalized_sql,
        flags=re.IGNORECASE,
    )
    is_cte_select = re.match(
        r"^WITH\b",
        normalized_sql,
        flags=re.IGNORECASE,
    )
    if not is_select and not is_cte_select:
        raise ValueError(
            "Only SELECT statements or WITH ... SELECT " "statements are permitted."
        )
    for keyword in FORBIDDEN_SQL_KEYWORDS:
        if re.search(
            rf"\b{keyword}\b",
            sql_upper,
        ):
            raise ValueError(f"Forbidden SQL operation detected: {keyword}")
    if ";" in normalized_sql:
        raise ValueError("Multiple SQL statements are not permitted.")
    state["validated_sql"] = normalized_sql
    print("VALIDATED SQL:")
    print(state["validated_sql"])
    return state
