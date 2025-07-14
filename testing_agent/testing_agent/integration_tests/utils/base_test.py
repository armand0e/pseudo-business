"""
Base Test Case for Integration Tests

This module provides the base test case class that all integration tests will inherit from.
It handles setup and teardown of the test environment, including Docker Compose management.
"""

import os
import json
import time
import pytest
import logging
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..config.config import config
from ..utils.test_client import IntegrationTestClient

logger = logging.getLogger(__name__)

class IntegrationTestBase:
    """Base class for all integration tests."""
    
    # Class variables for Docker environment
    docker_compose_file = Path(os.path.join(config.base_dir, "integration_tests", "config", "docker-compose.yml"))
    docker_env_up = False
    
    @classmethod
    def setup_class(cls):
        """Set up test environment once for all tests in the class."""
        if not cls.docker_env_up:
            cls.start_docker_environment()
        
        # Initialize test client
        cls.client = IntegrationTestClient()
        
        # Wait for all services to be available
        if not cls.client.wait_for_all_services():
            raise RuntimeError("Not all services are available. Check Docker environment.")
            
        logger.info("Test environment is ready.")
    
    @classmethod
    def teardown_class(cls):
        """Clean up after all tests in the class have run."""
        cls.client.close()
        # Optionally stop Docker environment if needed
        # cls.stop_docker_environment()
    
    @classmethod
    def start_docker_environment(cls):
        """Start Docker Compose environment."""
        logger.info(f"Starting Docker environment from {cls.docker_compose_file}")
        try:
            subprocess.run(
                ["docker-compose", "-f", str(cls.docker_compose_file), "up", "-d"],
                check=True
            )
            cls.docker_env_up = True
            logger.info("Docker environment started successfully.")
            
            # Give services time to initialize
            time.sleep(10)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Docker environment: {e}")
            raise
    
    @classmethod
    def stop_docker_environment(cls):
        """Stop Docker Compose environment."""
        if cls.docker_env_up:
            logger.info("Stopping Docker environment")
            try:
                subprocess.run(
                    ["docker-compose", "-f", str(cls.docker_compose_file), "down"],
                    check=True
                )
                cls.docker_env_up = False
                logger.info("Docker environment stopped successfully.")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to stop Docker environment: {e}")
    
    def setup_method(self):
        """Set up before each test method."""
        # Reset test data if needed
        pass
    
    def teardown_method(self):
        """Clean up after each test method."""
        # Clean up test data if needed
        pass
    
    def load_test_data(self, filename: str) -> Dict:
        """Load test data from a JSON file."""
        data_file = config.test_data_dir / filename
        if not data_file.exists():
            raise FileNotFoundError(f"Test data file not found: {data_file}")
        
        with open(data_file, 'r') as f:
            return json.load(f)
    
    def save_test_results(self, filename: str, data: Dict):
        """Save test results to a JSON file."""
        output_file = config.reports_dir / filename
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Test results saved to {output_file}")
    
    def assert_successful_response(self, response, message="Expected successful response"):
        """Assert that a response was successful."""
        assert 200 <= response.status_code < 300, \
            f"{message}: Status code {response.status_code}, Response: {response.text}"
    
    def assert_service_available(self, service_name: str):
        """Assert that a specific service is available."""
        service_client = self.client.get_service(service_name)
        assert service_client.health_check(), f"Service {service_name} is not available"