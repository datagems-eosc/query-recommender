from fastapi import APIRouter
from qr_api.resources.data_models import QueryRequest, QueryResponse, UserProfile
import json
from pathlib import Path

router = APIRouter()

def generate_next_queries(previous_query: str, context: dict) -> str:
    """
    Inputs:
    previous_query  <- a string that contains the previous NL query submitted by the user
    context         <- a dictionary (for now) containing:
                        - user_id <- ID of the user submitting the query
                        - results <- not sure yet, possibly a NL summary of the results

    Outputs:
    next_queries    <- a list of next queries (strings) based on the previous query and context
    """
    user_id = context['user_id']

    #all of this is instantly obsolete when we integrate with WP5
    user_profile_file_path = './qr_api/tests/' + user_id + '_profile.json'
    user_profile = load_user_profile_from_json(user_profile_file_path)
    
    return [previous_query, 'next query']


def load_user_profile_from_json(file_path: str) -> UserProfile:
    """
    Loads a user profile from a JSON file and returns a UserProfile object.
    This whole function will be gone once we integrate with WP5.
    """
    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return UserProfile(**data)


@router.post("/recommend-next-query", response_model=QueryResponse)
async def recommend_next_query(request: QueryRequest):
    next_queries = generate_next_queries(request.previous_query, request.context)
    return QueryResponse(next_queries=next_queries)
