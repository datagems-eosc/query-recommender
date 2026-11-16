from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from qr_api.resources import security
from qr_api.resources.data_models import QueryRequest, QueryResponse
from qr_api.resources.LLM_tools import generate_next_queries
from qr_api.resources.user_tools import notify_query
import os, logging

router = APIRouter()

# configure logging to track requests and errors
logger = logging.getLogger(__name__)

@router.post("/recommend-next-queries", response_model=QueryResponse, 
             summary="Get next query suggestions based on the current query and the user's profile")
def recommend_next_queries(
    request: QueryRequest,
    token: str = Depends(security.oauth2_scheme),
    token_payload: dict[str, Any] = Depends(security.require_app_scope),
):
    context = request.context if isinstance(request.context, dict) else {}
    logger.info("Recommendation request: user=%s query=%r", context.get("user_id"), request.current_query[:80])
    # The sub is the ID the DMM logs the queries under, and the one UP accepts for creating new users
    user_id = token_payload.get("sub") or context.get("user_id")

    # 1. Start the keyword refresh on UP (used from the next query on)
    notify_query(user_id, request.current_query, token)

    # 2. Suggestions from the current query + the profile as it is now
    next_queries = generate_next_queries(request.current_query, {**context, "user_id": user_id}, token=token)
    if next_queries is None:
        raise HTTPException(status_code=502, detail="The LLM could not be reached or returned an invalid response")
    return QueryResponse(next_queries=next_queries)