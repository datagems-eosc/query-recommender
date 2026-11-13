import os
import requests

USER_PROFILER_API_URL = os.getenv("USER_PROFILER_API_URL", "http://localhost:8000")


def fetch_user_interest_profile(user_id: str | None, token: str | None = None) -> dict:
    """
    Fetch the portable interest profile for a user from the User Profiler API,
    forwarding the caller's bearer token.
    Degrades to an anonymous/empty profile on any failure - missing user_id,
    network error, unknown user or rejected token - so callers never need to handle errors.
    """
    empty = {"userId": user_id, "keywords": [], "location": None, "affiliation": None, "orcid": None}
    if not user_id:
        return empty

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.get(f"{USER_PROFILER_API_URL}/user/{user_id}/profile", headers=headers, timeout=5)
        if response.status_code == 404:
            # Unknown user: not an error, just no profile to personalise with
            return empty
        if response.status_code in (401, 403):
            # Loud on purpose: otherwise a token/audience misconfiguration only shows up as worse recommendations
            print(f"User Profiler rejected the token ({response.status_code}): {response.text}")
            return empty
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error while calling User Profiler API:", e)
        return empty


def get_user_keywords(context: dict | None, token: str | None = None) -> list[str]:
    user_id = (context or {}).get("user_id")
    return fetch_user_interest_profile(user_id, token).get("keywords") or []



#=================================
# Notification of user's query

def notify_query(user_id: str | None, query: str, token: str | None) -> None:
    '''
    Tells the User Profiler about the new query
        --> triggers UP keywords refresh in background
    '''
    if not user_id or not token:
        return
    try:
        r = requests.post(f"{USER_PROFILER_API_URL}/user/{user_id}/queries", json={"query": query},
                          headers={"Authorization": f"Bearer {token}"}, timeout=3)
        if r.status_code != 202:
            print(f"User Profiler did not accept the query ({r.status_code}): {r.text[:200]}")
    except requests.exceptions.RequestException as e:
        print("Error while notifying the User Profiler:", e)