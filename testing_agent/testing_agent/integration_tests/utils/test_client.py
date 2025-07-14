"""
Integration Test Client

This module provides client classes for interacting with the various services
in the Agentic AI Development Platform during integration testing.
"""

import json
import time
import asyncio
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import httpx

from ..config.config import config, ServiceConfig

logger = logging.getLogger(__name__)

class ServiceClient:
    """Base client for interacting with service APIs."""
    
    def __init__(self, service_config: ServiceConfig):
        """Initialize service client with configuration."""
        self.config = service_config
        self.base_url = service_config.base_url
        self.session = requests.Session()
        self.async_client = httpx.AsyncClient(timeout=config.timeout)
        
    def get(self, endpoint: str, params: Dict = None, headers: Dict = None) -> requests.Response:
        """Send a GET request to the service."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"GET {url}")
        return self.session.get(url, params=params, headers=headers, timeout=config.timeout)
    
    def post(self, endpoint: str, data: Dict = None, json_data: Dict = None, 
             headers: Dict = None) -> requests.Response:
        """Send a POST request to the service."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"POST {url}")
        return self.session.post(url, data=data, json=json_data, headers=headers, timeout=config.timeout)
    
    def put(self, endpoint: str, data: Dict = None, json_data: Dict = None, 
            headers: Dict = None) -> requests.Response:
        """Send a PUT request to the service."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"PUT {url}")
        return self.session.put(url, data=data, json=json_data, headers=headers, timeout=config.timeout)
    
    def delete(self, endpoint: str, params: Dict = None, headers: Dict = None) -> requests.Response:
        """Send a DELETE request to the service."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"DELETE {url}")
        return self.session.delete(url, params=params, headers=headers, timeout=config.timeout)
    
    async def async_get(self, endpoint: str, params: Dict = None, headers: Dict = None) -> httpx.Response:
        """Send an asynchronous GET request to the service."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"ASYNC GET {url}")
        return await self.async_client.get(url, params=params, headers=headers)
    
    async def async_post(self, endpoint: str, data: Dict = None, json_data: Dict = None, 
                         headers: Dict = None) -> httpx.Response:
        """Send an asynchronous POST request to the service."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"ASYNC POST {url}")
        return await self.async_client.post(url, data=data, json=json_data, headers=headers)
    
    def health_check(self) -> bool:
        """Check if the service is healthy."""
        try:
            response = self.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {str(e)}")
            return False
    
    def wait_for_service(self, max_retries: int = 10, retry_interval: int = 2) -> bool:
        """Wait for the service to become available."""
        for i in range(max_retries):
            if self.health_check():
                logger.info(f"Service {self.config.name} is available")
                return True
            logger.info(f"Waiting for service {self.config.name} (attempt {i+1}/{max_retries})")
            time.sleep(retry_interval)
        logger.error(f"Service {self.config.name} not available after {max_retries} attempts")
        return False
    
    def close(self):
        """Close the session."""
        self.session.close()
        asyncio.run(self.async_client.aclose())


class IntegrationTestClient:
    """Client for performing integration tests across multiple services."""
    
    def __init__(self):
        """Initialize clients for all services."""
        self.services = {}
        for service_name, service_config in config.services.items():
            self.services[service_name] = ServiceClient(service_config)
    
    def get_service(self, service_name: str) -> ServiceClient:
        """Get a client for a specific service."""
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")
        return self.services[service_name]
    
    def wait_for_all_services(self, required_services: List[str] = None) -> bool:
        """Wait for all required services to become available."""
        if required_services is None:
            required_services = list(self.services.keys())
        
        logger.info(f"Waiting for services: {', '.join(required_services)}")
        all_available = True
        
        for service_name in required_services:
            service_client = self.get_service(service_name)
            if not service_client.wait_for_service():
                all_available = False
        
        return all_available
    
    def close(self):
        """Close all service clients."""
        for service in self.services.values():
            service.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Additional specialized clients for specific services

class MasterOrchestratorClient(ServiceClient):
    """Client for interacting with the Master Orchestrator."""
    
    def process_requirements(self, requirements_text: str) -> Dict:
        """Process natural language requirements."""
        return self.post("/process", json_data={"text": requirements_text}).json()


class BackendAgentClient(ServiceClient):
    """Client for interacting with the Backend Agent."""
    
    def get_tasks(self) -> List[Dict]:
        """Get all tasks."""
        return self.get("/tasks").json()
    
    def create_task(self, task_data: Dict) -> Dict:
        """Create a new task."""
        return self.post("/tasks", json_data=task_data).json()


class FrontendAgentClient(ServiceClient):
    """Client for interacting with the Frontend Agent."""
    
    def generate_ui_components(self, spec: Dict) -> Dict:
        """Generate UI components based on specification."""
        return self.post("/generate", json_data=spec).json()