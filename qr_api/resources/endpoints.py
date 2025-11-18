from fastapi import APIRouter
from qr_api.resources.data_models import QueryRequest, QueryResponse, UserProfile
import json, requests
from pathlib import Path
import os

router = APIRouter()

def local_generate_next_queries(current_query: str, context: dict) -> str:
    """
    Inputs:
    current_query  <- a string that contains the current NL query submitted by the user
    context         <- a dictionary (for now) containing:
                        - user_id <- ID of the user submitting the query
                        - results <- not sure yet, possibly a NL summary of the results

    Outputs:
    next_queries    <- a list of next queries (strings) based on the current query and context
    """
    user_id = context['user_id']

    #all of this is instantly obsolete when we integrate with WP5
    user_profile_file_path = './qr_api/tests/' + user_id + '_profile.json'
    user_profile = load_user_profile_from_json(user_profile_file_path)
    
    return [current_query, 'next query']

def generate_next_queries(current_query: str, context: dict) -> list[str]:
    payload = {
            "model": "llama-4-maverick",
            "messages": [
                {
                    "role":"system",
                    "content": '''You are an AI assistant whose primary goal is to suggest the next search queries, in order to help a user search and find information better on a search engine. 
                    Two different queries and entities are separated by the token '|'. For example,'Microsoft' and 'Google' would appear as 'Microsoft' | 'Google'.
                    Only suggest a list of the next 3 (maximum) queries, in the format: ['query1', 'query2', 'query3']. Make them as short as possible. Do not repeat or summarize the current query.
                    '''
    
                },
                {
                    "role":"user",
                    "content":f'''Current query: {current_query}'''
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
    #print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    
    #send POST request to the FastAPI endpoint
    try:
        response = requests.post(url=LLM_API_URL, headers=HEADERS, data=json_data, verify=False)
        response.raise_for_status()
        res = response.json()['choices'][0]['message']['content']
        
        res = res.replace('[', '').replace(']', '').replace("'", '').split(',')
        print('RESPONSE:', res)
        print('TYPE:', type(res))
        return res
    
    except requests.exceptions.RequestException as e:
        print("Error while calling API:", e)
        return None


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
    next_queries = generate_next_queries(request.current_query, request.context)
    print('TYPE next queries', type(next_queries))
    return QueryResponse(next_queries=next_queries)
