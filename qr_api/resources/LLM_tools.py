import json, requests, os
from urllib.parse import urlsplit
from qr_api.resources.user_tools import get_user_keywords

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
    keywords = get_user_keywords(context)
    keywords_str = ', '.join(keywords) if keywords else 'none'

    # getting the model among those available
    model_available = get_available_models(model_choice)

    payload = {
            "model": model_available,
            "messages": [
                {
                    "role":"system",
                    "content": '''
                    You are an AI assistant whose primary goal is to suggest the next search queries,
                    in order to help a user search and find information better on a search engine.
                    You are going to suggest 3 search queries that the user would search next based on the current query
                    and the user's interest keywords. These keywords should indicate the user's preferences.
                    Only suggest a list of the next 3 (maximum) queries, in the format: ['query1', 'query2', 'query3'].
                    Make them short (close to the current query). Do not repeat or summarize the current query.
                    '''

                },
                {
                    "role":"user",
                    "content":f'''Current query: {current_query}
                                  User interest keywords: {keywords_str}'''
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
    

def generate_user_description(context: dict, model_choice: str = "glm-5.3-flash") -> str:
    keywords = get_user_keywords(context)
    keywords_str = ', '.join(keywords) if keywords else 'none'

    # getting the model among those available
    model_available = get_available_models(model_choice)

    payload = {
            "model": model_available,
            "messages": [
                {
                    "role":"system",
                    "content": '''You are an AI assistant whose primary goal is to provide the summary of a user profile.
                    The user profile is defined by the user's interest keywords, extracted from queries performed in a data analytics app.
                    Provide a brief description of this user based on their keywords.
                    '''

                },
                {
                    "role":"user",
                    "content":f'''User's interest keywords: {keywords_str}'''
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



# function to automatically retrive the list of available LLMs' ID
def get_available_models(model_choice) -> str:
    '''
    This function will retrive via http request the available models to use inside
    the keywords generation function

    input:
        - model_choice model selected by user or defualt model

    Return:
        - ID of the available model: either the first available or the one selected
    '''

    # models endpoint lives at <scheme>://<host[:port]>/api/models, whatever the chat path is
    parts = urlsplit(LLM_API_URL)
    url = f"{parts.scheme}://{parts.netloc}/api/models"

    try:
        response = requests.get(
        url,
        headers= HEADERS,
        verify=False,
        timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        models = [model["id"] for model in data["data"]]
        model_available = model_choice if model_choice in models else (models[0] if models else model_choice)
        return model_available
    
        
    except requests.exceptions.RequestException as e:
        print(f"Could not reach models endpoint: {e}")
        return model_choice