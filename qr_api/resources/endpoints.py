from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from qr_api.resources import security
from qr_api.resources.data_models import QueryRequest, QueryResponse
from qr_api.resources.LLM_tools import generate_next_queries
import os

router = APIRouter()

@router.post("/recommend-next-queries", response_model=QueryResponse)
async def recommend_next_queries(
    request: QueryRequest,
    token: str = Depends(security.oauth2_scheme),
    token_payload: dict[str, Any] = Depends(security.require_valid_token),
):
    # The caller's token is passed on to the User Profiler (never to the LLM)
    next_queries = generate_next_queries(request.current_query, request.context, token=token)
    if next_queries is None:
        raise HTTPException(status_code=502, detail="The LLM could not be reached or returned an invalid response")
    return QueryResponse(next_queries=next_queries)
