import os
import requests

USER_PROFILER_API_URL = os.getenv("USER_PROFILER_API_URL", "http://localhost:8000")


def fetch_user_interest_profile(user_id: str | None) -> dict:
    """
    Fetch the portable interest profile for a user from the User Profiler API.
    Degrades to an anonymous/empty profile on any failure - missing user_id,
    network error, or unknown user - so callers never need to handle errors.
    """
    empty = {"userId": user_id, "keywords": [], "location": None, "affiliation": None, "orcid": None}
    if not user_id:
        return empty

    try:
        response = requests.get(f"{USER_PROFILER_API_URL}/user/{user_id}/profile", timeout=5)
        response.raise_for_status()
        data = response.json()
        if "keywords" not in data:
            # User Profiler's "no such user" convention: HTTP 200 + {"message": ...}
            return empty
        return data
    except requests.exceptions.RequestException as e:
        print("Error while calling User Profiler API:", e)
        return empty


def get_user_keywords(context: dict | None) -> list[str]:
    user_id = (context or {}).get("user_id")
    return fetch_user_interest_profile(user_id).get("keywords") or []
