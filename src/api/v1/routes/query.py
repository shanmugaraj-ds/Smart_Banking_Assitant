from fastapi import APIRouter
from src.api.v1.schemas.query_schema import QueryRequest, QueryResponse
from src.api.v1.services.query_service import query_documents
from src.api.v1.states.rag_state import RAGState

router = APIRouter(prefix="/api/v1/query")


@router.post("/", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    answer = query_documents(request.question)
    return QueryResponse(answer=answer["answer"], query_type=answer["query_type"])


