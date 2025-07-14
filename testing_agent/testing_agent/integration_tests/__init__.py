"""
Comprehensive Integration Testing Framework
for the Agentic AI Development Platform

This package provides a complete integration testing framework that validates
the entire system workflow from user input to final code generation and deployment
across all 10 components of the platform.

Components tested:
1. Master Orchestrator
2. Database Agent  
3. API Gateway
4. Backend Agent
5. Evolution Engine
6. Frontend Agent
7. User Interface
8. CLI Tool
9. Testing Agent
10. DevOps Agent

Features:
- End-to-end workflow testing
- Component integration testing
- Performance monitoring and benchmarking
- Docker-based test environment
- Comprehensive reporting and analytics
- Automated test execution and CI/CD integration

Usage:
    # Run all integration tests
    python -m testing_agent.integration_tests.test_runner --suite all
    
    # Run specific test suite
    python -m testing_agent.integration_tests.test_runner --suite workflow
    
    # Use automation script
    ./testing_agent/testing_agent/integration_tests/run_tests.sh --suite all --verbose
"""

__version__ = "1.0.0"
__author__ = "Agentic AI Development Platform Team"

from .config.config import config
from .utils import IntegrationTestBase, IntegrationTestClient, performance_monitor
from .test_runner import IntegrationTestRunner

__all__ = [
    'config',
    'IntegrationTestBase',
    'IntegrationTestClient', 
    'performance_monitor',
    'IntegrationTestRunner'
]

# Framework metadata
FRAMEWORK_INFO = {
    'name': 'Agentic AI Integration Testing Framework',
    'version': __version__,
    'description': 'Comprehensive end-to-end integration testing framework',
    'components_tested': 10,
    'test_types': ['workflow', 'component', 'performance'],
    'environments': ['docker', 'local'],
    'coverage_target': 90.0
}