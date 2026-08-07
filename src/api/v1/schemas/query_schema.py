from typing import Literal, List, Dict, Any
from pydantic import BaseModel


class QueryClassification(BaseModel):
    query_type: Literal[
        "rag",
        "sql",
        "hybrid",
    ]


class SQLQuery(BaseModel):
    sql_query: str


class SQLValidation(BaseModel):
    validated_sql: str


class AgentResponse(BaseModel):
    answer: str
    citations: List[str] = []
    confidence_score: float


class RetrievedChunk(BaseModel):
    content: str
    score: float
    metadata: dict[str, Any]
