#!/usr/bin/env python3
"""
Integration Testing Framework for Master Orchestrator
Provides tools to test the integration between different components
"""

import asyncio
from typing import Dict, Any, List, Callable, Coroutine
import logging

logger = logging.getLogger(__name__)

class IntegrationTestFramework:
    """Framework for testing component integrations."""

    def __init__(self):
        self.test_results = {}

    def register_test(self, name: str, test_func: Callable[[Dict[str, Any]], Coroutine]):
        """Register a new integration test."""
        if name in self.test_results:
            logger.warning(f"Test '{name}' already registered. Overwriting.")
        self.test_results[name] = {"function": test_func, "status": None, "error": None}

    async def run_test(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific integration test."""
        if name not in self.test_results:
            logger.error(f"Test '{name}' not found.")
            return {"status": "failed", "error": f"Test '{name}' not registered"}

        try:
            result = await self.test_results[name]["function"](context)
            self.test_results[name]["status"] = "passed"
            return {"status": "passed", "result": result}
        except Exception as e:
            self.test_results[name]["status"] = "failed"
            self.test_results[name]["error"] = str(e)
            logger.error(f"Test '{name}' failed: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def run_all_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run all registered integration tests."""
        results = {}
        for name, test_info in self.test_results.items():
            try:
                result = await test_info["function"](context)
                test_info["status"] = "passed"
                results[name] = {"status": "passed", "result": result}
            except Exception as e:
                test_info["status"] = "failed"
                test_info["error"] = str(e)
                logger.error(f"Test '{name}' failed: {str(e)}")
                results[name] = {"status": "failed", "error": str(e)}

        # Generate summary
        passed = sum(1 for test in self.test_results.values() if test["status"] == "passed")
        failed = sum(1 for test in self.test_results.values() if test["status"] == "failed")

        summary = {
            "total_tests": len(self.test_results),
            "passed": passed,
            "failed": failed,
            "results": results
        }

        logger.info(f"Integration tests completed: {passed} passed, {failed} failed")
        return summary

# Example integration tests
async def test_frontend_backend_integration(context: Dict[str, Any]) -> bool:
    """Test the integration between frontend and backend components."""
    # This is a simplified example. In a real implementation, this would involve
    # setting up a test server, making API calls, and verifying responses.
    logger.info("Testing frontend-backend integration...")

    # Check if both frontend and backend files exist in the codebase
    has_frontend = any(file_path.endswith('.js') or file_path.endswith('.ts')
                       for file_path in context.get('codebase', {}).get('files', {}))
    has_backend = any(file_path.endswith('.py') or file_path.endswith('.java')
                      for file_path in context.get('codebase', {}).get('files', {}))

    # Check if there's a connection between frontend and backend
    has_api_call = False
    if has_frontend:
        for file_content in context.get('codebase', {}).get('files', {}).values():
            if '.js' in file_content or '.ts' in file_content:
                if 'fetch' in file_content or 'axios' in file_content:
                    has_api_call = True
                    break

    # Simple heuristic: frontend and backend exist AND there's an API call from frontend to backend
    result = has_frontend and has_backend and has_api_call
    logger.info(f"Frontend-backend integration test {'passed' if result else 'failed'}")
    return result

async def test_database_schema_integration(context: Dict[str, Any]) -> bool:
    """Test the database schema integration."""
    # This is a simplified example. In a real implementation, this would involve
    # setting up a test database and verifying schema integrity.
    logger.info("Testing database schema integration...")

    # Check if there's a database schema file in the codebase
    has_schema = any('schema' in file_path.lower() or 'migration' in file_path.lower()
                     for file_path in context.get('codebase', {}).get('files', {}))

    # Check if backend connects to the database
    has_db_connection = False
    if has_schema:
        for file_content in context.get('codebase', {}).get('files', {}).values():
            if '.py' in file_content or '.java' in file_content:
                if 'database' in file_content.lower() and ('connect' in file_content.lower() or
                                                               'sqlalchemy' in file_content.lower()):
                    has_db_connection = True
                    break

    # Simple heuristic: schema exists AND backend connects to it
    result = has_schema and has_db_connection
    logger.info(f"Database schema integration test {'passed' if result else 'failed'}")
    return result