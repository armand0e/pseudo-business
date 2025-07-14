"""API client for interacting with the Agentic AI Development Platform."""

import requests
from typing import Dict, Any, Optional
from .config import get_config
from .auth import get_auth_headers

class APIClient:
    """Client for interacting with the API Gateway."""

    def __init__(self):
        self.config = get_config()
        self.base_url = self.config['api_url']

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {**get_auth_headers(), **kwargs.pop('headers', {})}
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    def init_project(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a new project."""
        return self._request('POST', '/projects', json={
            'name': name,
            'config': config
        }).json()

    def submit_requirements(self, project_id: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Submit requirements for a project."""
        return self._request('POST', f'/projects/{project_id}/requirements', 
            json=requirements).json()

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get the status of a project."""
        return self._request('GET', f'/projects/{project_id}').json()

    def list_projects(self) -> Dict[str, Any]:
        """List all projects."""
        return self._request('GET', '/projects').json()

    def batch_process(self, batch_config: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a batch processing request."""
        return self._request('POST', '/batch', json=batch_config).json()

    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Get the status of a batch processing request."""
        return self._request('GET', f'/batch/{batch_id}').json()