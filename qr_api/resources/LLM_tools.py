import json, requests, os
from urllib.parse import urlsplit
import urllib3
from pydantic import ValidationError
from qr_api.resources.data_models import LLMQuerySuggestions
from qr_api.resources.user_tools import get_user_keywords

MAX_SUGGESTIONS = 3
# The User Profiler returns keywords strongest (most recently seen) first: keep the top ones
MAX_KEYWORDS = 15

# Asks OpenAI-compatible backends to constrain the reply to this schema
SUGGESTIONS_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "query_suggestions",
        "strict": True,
        "schema": LLMQuerySuggestions.model_json_schema() | {"additionalProperties": False},
    },
}


# =========================
# LLM API CONFIGURATION

# LLM Token
TOKEN = os.getenv('LLM_TOKEN', '')
# LLM API URL
LLM_API_URL = os.getenv('LLM_API_URL', '')
# LLM Model List URL
LLM_MODEL_LIST = os.getenv('LLM_MODEL_LIST', '')

HEADERS = {
"User-Agent": "Python API Sample",
"Authorization": "Bearer " + TOKEN,
"Content-Type": "application/json"
}
# ========================


def _ssl_verify_setting() -> bool | str:
    """
    Reads LLM_SSL_VERIFY: "true" (default) verifies against the system CAs,
    a file path verifies against that CA bundle / certificate, and "false"
    disables verification (e.g. for an endpoint with a self-signed certificate).
    """
    value = os.getenv('LLM_SSL_VERIFY', 'true').strip()
    if value.lower() in ('false', '0', 'no'):
        # Explicit opt-out: warn once here instead of on every request
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        print("WARNING: TLS certificate verification for the LLM API is disabled (LLM_SSL_VERIFY=false)")
        return False
    if value.lower() in ('true', '1', 'yes', ''):
        return True
    return value

SSL_VERIFY = _ssl_verify_setting()

def generate_next_queries(current_query: str, context: dict, model_choice: str = "llama-3.3", token: str | None = None) -> list[str]:
    """
    Inputs:
    current_query   <- a string that contains the current NL query submitted by the user
    context         <- a dictionary (for now) containing:
                        - user_id <- ID of the user submitting the query
                        - results <- possibly a NL summary of the query results
    token           <- the caller's bearer token, forwarded to the User Profiler

    Outputs:
    next_queries    <- a list of next queries (strings) based on the current query and context,
                       or None if the LLM could not be reached or replied with invalid output
    """
    keywords = get_user_keywords(context, token)[:MAX_KEYWORDS]
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
                    The keywords are listed from most to least relevant: favour the first ones.
                    Make them short (close to the current query). Do not repeat or summarize the current query.
                    Reply ONLY with a JSON object of this exact form, with no other text:
                    {"queries": ["query1", "query2", "query3"]}
                    '''

                },
                {
                    "role":"user",
                    "content":f'''Current query: {current_query}
                                  User interest keywords (most relevant first): {keywords_str}'''
                }
            ],
            "response_format": SUGGESTIONS_RESPONSE_FORMAT,
        }

    #send POST request to the FastAPI endpoint
    try:
        response = requests.post(url=LLM_API_URL, headers=HEADERS, data=json.dumps(payload).encode('utf8'), verify=SSL_VERIFY)
        if response.status_code == 400:
            # Some backends/models reject response_format: retry relying on the prompt alone
            del payload["response_format"]
            response = requests.post(url=LLM_API_URL, headers=HEADERS, data=json.dumps(payload).encode('utf8'), verify=SSL_VERIFY)
        response.raise_for_status()

        #TODO should check if new recommendations are not in query log, to avoid loops
        #easy: equivalence (not very good)
        #harder: token similarity (X% of same tokens as one of previous suggestions)
        content = response.json()['choices'][0]['message']['content']

    except requests.exceptions.RequestException as e:
        print("Error while calling API:", e)
        return None

    return parse_suggestions(content, current_query)


def parse_suggestions(content: str, current_query: str) -> list[str] | None:
    """
    Validates the LLM reply against LLMQuerySuggestions and cleans the queries:
    strips whitespace, drops empty ones, duplicates and repeats of the current query,
    and keeps at most MAX_SUGGESTIONS. Returns None if the reply is not valid JSON
    of the expected shape.
    """
    # Tolerate replies wrapped in ```json fences or surrounded by extra text
    start, end = content.find('{'), content.rfind('}')
    if start == -1 or end == -1:
        print("LLM reply contains no JSON object:", content)
        return None

    try:
        suggestions = LLMQuerySuggestions.model_validate_json(content[start:end + 1])
    except ValidationError as e:
        print("LLM reply does not match the expected schema:", e)
        return None

    seen = {current_query.strip().lower()}
    queries = []
    for q in suggestions.queries:
        q = q.strip()
        if q and q.lower() not in seen:
            seen.add(q.lower())
            queries.append(q)
    return queries[:MAX_SUGGESTIONS]
    

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
        response = requests.post(url=LLM_API_URL, headers=HEADERS, data=json_data, verify=SSL_VERIFY)
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
        verify=SSL_VERIFY,
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