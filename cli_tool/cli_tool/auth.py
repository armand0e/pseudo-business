"""Authentication module for the CLI tool."""

import keyring
import requests
from typing import Optional, Dict
from .config import get_config

SERVICE_NAME = "agentic-cli"

def store_token(token: str):
    """Store the authentication token securely."""
    keyring.set_password(SERVICE_NAME, "auth_token", token)

def get_token() -> Optional[str]:
    """Retrieve the stored authentication token."""
    return keyring.get_password(SERVICE_NAME, "auth_token")

def delete_token():
    """Delete the stored authentication token."""
    keyring.delete_password(SERVICE_NAME, "auth_token")

def login(username: str, password: str) -> bool:
    """Authenticate with the API and store the token."""
    config = get_config()
    try:
        response = requests.post(
            f"{config['api_url']}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        token = response.json()["token"]
        store_token(token)
        return True
    except requests.exceptions.RequestException:
        return False

def get_auth_headers() -> Dict[str, str]:
    """Get the authentication headers for API requests."""
    token = get_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def is_authenticated() -> bool:
    """Check if the user is authenticated."""
    return get_token() is not None