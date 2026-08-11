from typing import Literal, List, Dict, Any
from pydantic import BaseModel, Field


class QueryClassification(BaseModel):
    query_type: Literal[
        "rag",
        "sql",
        "hybrid",
        "conversation",
        "out_of_scope",
    ]


class SQLQuery(BaseModel):
    sql_query: str


class SQLValidation(BaseModel):
    validated_sql: str


class AgentResponse(BaseModel):
    answer: str
    citations: List[str] = Field(default_factory=list)
    confidence_score: float


class RetrievedChunk(BaseModel):
    content: str
    score: float
    metadata: dict[str, Any]


class QueryRequest(BaseModel):
    question: str
    chat_history: list = []


class QueryResponse(BaseModel):
    answer: str
    query_type: str
