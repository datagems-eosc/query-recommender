
from pathlib import Path
import json, requests, os
from qr_api.resources.data_models import UserProfile

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

def check_user_existence(user_id: str) -> bool:
    user_profile_file_path = build_user_path(user_id)
    return os.path.exists(user_profile_file_path)

def build_user_path(user_id:str) -> str:
    return user_profiles_path + user_id + '_profile.json'

def get_user_previous_queries(context: dict) -> str:
    user_id = 'user1'
    if 'user_id' in context and check_user_existence(context['user_id']):
        user_id = context['user_id']

    #all of this is instantly obsolete when we integrate with WP5
    user_profile_file_path =  build_user_path(user_id)
    user_profile = load_user_profile_from_json(user_profile_file_path)
    previous_queries =  user_profile.previous_queries
    return '|'.join(previous_queries)

