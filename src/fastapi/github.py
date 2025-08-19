import os
import time
import jwt
import requests

GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY")

def get_github_app_jwt():
    """Create a JWT for the GitHub App"""
    if not GITHUB_APP_ID or not GITHUB_PRIVATE_KEY:
        raise ValueError("GITHUB_APP_ID and GITHUB_PRIVATE_KEY must be set")

    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),  # 10 minutes
        "iss": GITHUB_APP_ID,
    }
    
    return jwt.encode(
        payload,
        GITHUB_PRIVATE_KEY,
        algorithm="RS256"
    )

def get_installation_access_token(installation_id: int):
    """Get an installation access token"""
    jwt_token = get_github_app_jwt()
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    return data["token"]
