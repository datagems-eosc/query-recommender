from fastapi import APIRouter
from qr_api.resources.data_models import QueryRequest, QueryResponse
from qr_api.resources.LLM_tools import generate_next_queries
import os

router = APIRouter()

@router.post("/recommend-next-queries", response_model=QueryResponse)
async def recommend_next_queries(request: QueryRequest):
    next_queries = generate_next_queries(request.current_query, request.context)
    return QueryResponse(next_queries=next_queries)