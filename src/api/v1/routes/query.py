# from fastapi import APIRouter
# from src.api.v1.schemas.query_schema import QueryRequest, QueryResponse
# from src.api.v1.services.query_service import query_documents

# router = APIRouter(prefix="/api/v1/query")


# @router.post("/", response_model=QueryResponse)
# def query_endpoint(request: QueryRequest):
#     answer = query_documents(request.question)
#     return QueryResponse(
#         answer=answer["answer"],
#         query_type=answer["query_type"],
#         citations=answer.get("citations", []),
#         images=answer.get("images", []),
#         confidence_score=answer.get("confidence_score", 0.0),
#     )

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
from src.api.v1.schemas.query_schema import (
    QueryRequest,
    QueryResponse,
)
from src.api.v1.services.query_service import (
    query_documents,
    query_documents_stream,
)

router = APIRouter(
    prefix="/api/v1/query",
    tags=["Query"],
)


# NORMAL QUERY
@router.post(
    "/",
    response_model=QueryResponse,
)
async def query(request: QueryRequest):
    return query_documents(request.question)


# STREAMING QUERY
@router.post("/stream")
async def query_stream(
    request: QueryRequest,
):
    async def event_generator():
        try:
            async for event in query_documents_stream(request.question):
                yield (f"data: " f"{json.dumps(event)}" f"\n\n")
        except Exception as e:
            error_event = {
                "type": "error",
                "message": str(e),
            }
            yield (f"data: " f"{json.dumps(error_event)}" f"\n\n")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
