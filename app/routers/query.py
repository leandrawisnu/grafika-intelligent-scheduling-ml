from fastapi import APIRouter
from app.models.schemas import QueryRequest, QueryResponse
from app.services.nl_query import nl_query

router = APIRouter()


@router.post("/query/nl", response_model=QueryResponse)
def query(request: QueryRequest):
    return nl_query(request)
