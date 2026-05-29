import json, requests, os
from qr_api.resources.user_tools import get_user_previous_queries

TOKEN = os.getenv('LLM_TOKEN', '')
LLM_API_URL = os.getenv('LLM_API_URL', '')
HEADERS = {
"User-Agent": "Python API Sample",
"Authorization": "Bearer " + TOKEN,
"Content-Type": "application/json"
}

def generate_next_queries(current_query: str, context: dict, model_choice: str = "llama-3.3") -> list[str]:
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
    #context could be null
    if not context:
        #default user 
        context = {'user_id':'user1'}

    previous_queries = get_user_previous_queries(context)

    payload = {
            "model": model_choice,
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
        
    json_data = json.dumps(payload).encode('utf8')
    
    #send POST request to the FastAPI endpoint
    try:
        response = requests.post(url=LLM_API_URL, headers=HEADERS, data=json_data, verify=False)
        response.raise_for_status()

        #TODO should check if new recommendations are not in query log, to avoid loops
        #easy: equivalence (not very good)
        #harder: token similarity (X% of same tokens as one of previous suggestions)
        res = response.json()['choices'][0]['message']['content']
        
        #TODO this assumes the LLM replies with the right format, consistently
        res = res.replace('[', '').replace(']', '').replace("'", '').split(',')
        return res
    
    except requests.exceptions.RequestException as e:
        print("Error while calling API:", e)
        return None
    

def generate_user_description(context: dict, model_choice: str = "llama-3.3") -> str:
    previous_queries = get_user_previous_queries(context)
    payload = {
            "model": model_choice,
            "messages": [
                {
                    "role":"system",
                    "content": '''You are an AI assistant whose primary goal is to provide the summary of a user profile.
                    The user profile is defined by the previous queries that the user performed in a data analytics app.
                    Two different queries and entities are separated by the token '|'. For example,'Microsoft' and 'Google' would appear as 'Microsoft' | 'Google'.
                    Provide a brief description of this user based on their queries.
                    '''
    
                },
                {
                    "role":"user",
                    "content":f'''User's previous queries: {previous_queries}'''
                }
            ]
        }

    json_data = json.dumps(payload).encode('utf8')
    #print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    # Send POST request to the FastAPI endpoint
    try:
        response = requests.post(url=LLM_API_URL, headers=HEADERS, data=json_data, verify=False)
        response.raise_for_status()
        res = response.json()['choices'][0]['message']['content']
        return res
    except requests.exceptions.RequestException as e:
        print("Error while calling API:", e)
        return None