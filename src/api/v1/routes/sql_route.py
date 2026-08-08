from fastapi import APIRouter
from src.api.v1.schemas.query_schema import QueryRequest, QueryResponse
from src.api.v1.services.query_service import SQLService

router = APIRouter(prefix="/api/v1/sql", tags=["SQL Banking"])


sql_service = SQLService()


@router.post("/query", response_model=QueryResponse)
def sql_query(request: QueryRequest):
    result = sql_service.execute_query(request.question)
    return result
