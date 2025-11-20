from fastapi import APIRouter
from qr_api.resources.data_models import QueryRequest, QueryResponse, UserProfile
import json, requests
from pathlib import Path
import os

router = APIRouter()
user_profiles_path = './qr_api/tests/'

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

def get_user_previous_queries(context: dict) -> str:
    user_id = context['user_id']

    #all of this is instantly obsolete when we integrate with WP5
    user_profile_file_path =  user_profiles_path + user_id + '_profile.json'
    user_profile = load_user_profile_from_json(user_profile_file_path)
    previous_queries =  user_profile.previous_queries
    return '|'.join(previous_queries)

def generate_next_queries(current_query: str, context: dict) -> list[str]:
    """
    Inputs:
    current_query   <- a string that contains the current NL query submitted by the user
    context         <- a dictionary (for now) containing:
                        - user_id <- ID of the user submitting the query
                        - results <- possibly a NL summary of the query results

    Outputs:
    next_queries    <- a list of next queries (strings) based on the current query and context
    """
    #this should get the user keywords (we need a function to build those)
    previous_queries = get_user_previous_queries(context)

    payload = {
            "model": "llama-4-maverick",
            "messages": [
                {
                    "role":"system",
                    "content": '''
                    You are an AI assistant whose primary goal is to suggest the next search queries, 
                    in order to help a user search and find information better on a search engine. 
                    You are going to suggest 3 search queries that the user would search next based on the current query
                    and the user's previous queries. These previous queries should indicate the user's preferences.
                    Two different queries are separated by the token '|'. 
                    For example,'Microsoft' and 'Google' would appear as 'Microsoft' | 'Google'.
                    Only suggest a list of the next 3 (maximum) queries, in the format: ['query1', 'query2', 'query3']. 
                    Make them short (close to the previous queries). Do not repeat or summarize the current query.
                    '''
    
                },
                {
                    "role":"user",
                    "content":f'''Current query: {current_query}
                                  Previous queries: {previous_queries}'''
                }
            ]
        }
        
    TOKEN = os.getenv('LLM_TOKEN', '')
    LLM_API_URL = os.getenv('LLM_API_URL', '')
    HEADERS = {
    "User-Agent": "Python API Sample",
    "Authorization": "Bearer " + TOKEN,
    "Content-Type": "application/json"
    }
    json_data = json.dumps(payload).encode('utf8')
    
    #send POST request to the FastAPI endpoint
    try:
        response = requests.post(url=LLM_API_URL, headers=HEADERS, data=json_data, verify=False)
        response.raise_for_status()
        res = response.json()['choices'][0]['message']['content']
        
        #TODO this assumes the LLM replies with the right format, consistently
        res = res.replace('[', '').replace(']', '').replace("'", '').split(',')
        return res
    
    except requests.exceptions.RequestException as e:
        print("Error while calling API:", e)
        return None

@router.post("/recommend-next-query", response_model=QueryResponse)
async def recommend_next_query(request: QueryRequest):
    next_queries = generate_next_queries(request.current_query, request.context)
    return QueryResponse(next_queries=next_queries)
