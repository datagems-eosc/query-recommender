import os
import requests
import logging


# congigure logging to track requests and errors
logger = logging.getLogger(__name__)

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
        logger.info("No user_id in the context: no personalisation")
        return empty
    if not token:
        logger.warning("No token to forward to the User Profiler for %s", user_id)

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.get(f"{USER_PROFILER_API_URL}/user/{user_id}/profile", headers=headers, timeout=5)
        if response.status_code == 404:
            logger.info("User %s not in the User Profiler: no personalisation", user_id)
            return empty
        if response.status_code in (401, 403):
            # Loud on purpose: otherwise a token/audience misconfiguration only shows up as worse recommendations
            logger.warning("User Profiler rejected the token for %s (%s): %s",
                           user_id, response.status_code, response.text[:200])
            return empty
        response.raise_for_status()
        profile = response.json()
        logger.info("Profile of %s fetched: %d keywords", user_id, len(profile.get("keywords") or []))
        return profile
    except requests.exceptions.RequestException as e:
        logger.warning("User Profiler unreachable for %s: %s", user_id, e)
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
        if r.status_code == 202:
            logger.info("Query notified to the User Profiler for %s", user_id)
        else:
            logger.warning("User Profiler did not accept the query for %s (%s): %s",
                           user_id, r.status_code, r.text[:200])
    except requests.exceptions.RequestException as e:
        logger.warning("Could not notify the User Profiler for %s: %s", user_id, e)