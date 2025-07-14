"""
Integration Testing Framework Configuration

This module defines the configuration settings for the integration testing framework,
including service endpoints, test data paths, and test environment settings.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

@dataclass
class ServiceConfig:
    """Configuration for individual service components."""
    name: str
    host: str
    port: int
    url_prefix: str = ""
    
    @property
    def base_url(self) -> str:
        """Get the base URL for the service."""
        return f"http://{self.host}:{self.port}{self.url_prefix}"


@dataclass
class IntegrationTestConfig:
    """Configuration for the integration testing framework."""
    # Base directories
    base_dir: Path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    test_data_dir: Path = Path(os.path.join(base_dir, "integration_tests", "fixtures", "data"))
    reports_dir: Path = Path(os.path.join(base_dir, "integration_tests", "reports"))
    
    # Test environment settings
    environment: str = "test"
    log_level: str = "INFO"
    timeout: int = 30
    retries: int = 3
    
    # Performance thresholds
    performance_thresholds: Dict[str, float] = None
    
    # Services configuration
    services: Dict[str, ServiceConfig] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.performance_thresholds is None:
            self.performance_thresholds = {
                "request_time_ms": 500,
                "workflow_time_sec": 10
            }
        
        if self.services is None:
            # Default service configurations
            self.services = {
                "master_orchestrator": ServiceConfig(
                    name="master_orchestrator",
                    host="localhost",
                    port=8000,
                    url_prefix="/api"
                ),
                "backend_agent": ServiceConfig(
                    name="backend_agent",
                    host="localhost",
                    port=8001,
                    url_prefix="/api/v1"
                ),
                "database_agent": ServiceConfig(
                    name="database_agent",
                    host="localhost",
                    port=8002,
                    url_prefix="/api"
                ),
                "frontend_agent": ServiceConfig(
                    name="frontend_agent",
                    host="localhost",
                    port=8003,
                    url_prefix="/api"
                ),
                "testing_agent": ServiceConfig(
                    name="testing_agent",
                    host="localhost",
                    port=8005,
                    url_prefix="/api"
                ),
                "devops_agent": ServiceConfig(
                    name="devops_agent",
                    host="localhost",
                    port=8004,
                    url_prefix="/api"
                ),
                "api_gateway": ServiceConfig(
                    name="api_gateway",
                    host="localhost",
                    port=3000,
                    url_prefix=""
                ),
                "evolution_engine": ServiceConfig(
                    name="evolution_engine",
                    host="localhost",
                    port=8006,
                    url_prefix="/api"
                ),
                "cli_tool": ServiceConfig(
                    name="cli_tool",
                    host="localhost",
                    port=8007,
                    url_prefix="/api"
                ),
                "user_interface": ServiceConfig(
                    name="user_interface",
                    host="localhost",
                    port=3001,
                    url_prefix=""
                ),
            }
        
        # Ensure directories exist
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)


# Default configuration instance
config = IntegrationTestConfig()