"""
End-to-End Workflow Integration Tests

This module tests complete user workflows that span all components of the
Agentic AI Development Platform, from user input to final code generation and deployment.
"""

import os
import time
import pytest
import logging
import json
from typing import Dict, List, Any
from pathlib import Path

from ..utils.base_test import IntegrationTestBase
from ..config.config import config

logger = logging.getLogger(__name__)

class TestEndToEndWorkflows(IntegrationTestBase):
    """Test complete end-to-end workflows across all platform components."""
    
    def test_ui_requirements_to_deployment_workflow(self):
        """
        Test the complete workflow from user submitting requirements via UI to code generation and deployment.
        
        Flow: User submits requirements via UI → Master Orchestrator processes → Agents generate code → 
              Evolution Engine optimizes → DevOps deploys
        """
        # 1. Load test requirements
        requirements_data = self.load_test_data("requirements.json")
        req_text = requirements_data["basic_webapp"]["text"]
        
        # 2. Submit requirements through UI (simulated via API)
        ui_client = self.client.get_service("user_interface")
        requirements_response = ui_client.post("/api/requirements", json_data={"text": req_text})
        self.assert_successful_response(requirements_response)
        
        # Get the project ID from the response
        project_id = requirements_response.json().get("project_id")
        assert project_id, "Project ID not returned in response"
        
        # 3. Verify Master Orchestrator processed the requirements
        orchestrator_client = self.client.get_service("master_orchestrator")
        max_retries = 10
        processed = False
        
        for i in range(max_retries):
            status_response = orchestrator_client.get(f"/projects/{project_id}/status")
            self.assert_successful_response(status_response)
            status = status_response.json()
            
            if status.get("status") == "completed":
                processed = True
                break
            
            logger.info(f"Waiting for requirements processing (attempt {i+1}/{max_retries})")
            time.sleep(5)
        
        assert processed, "Requirements processing did not complete in time"
        
        # 4. Verify agents generated code artifacts
        backend_client = self.client.get_service("backend_agent")
        artifacts_response = backend_client.get(f"/projects/{project_id}/artifacts")
        self.assert_successful_response(artifacts_response)
        
        artifacts = artifacts_response.json()
        assert len(artifacts) > 0, "No code artifacts were generated"
        
        # Verify artifacts from different agents
        agent_types = set(artifact["agent_type"] for artifact in artifacts)
        expected_agents = {"frontend", "backend", "database"}
        assert expected_agents.issubset(agent_types), f"Missing artifacts from required agents: {expected_agents - agent_types}"
        
        # 5. Verify Evolution Engine optimized the code
        evolution_client = self.client.get_service("evolution_engine")
        optimization_response = evolution_client.get(f"/projects/{project_id}/optimization")
        self.assert_successful_response(optimization_response)
        
        optimization = optimization_response.json()
        assert optimization.get("optimized"), "Code was not optimized"
        assert optimization.get("fitness_improvement") > 0, "No fitness improvement in code optimization"
        
        # 6. Verify DevOps Agent deployment
        devops_client = self.client.get_service("devops_agent")
        deployment_response = devops_client.get(f"/projects/{project_id}/deployment")
        self.assert_successful_response(deployment_response)
        
        deployment = deployment_response.json()
        assert deployment.get("status") == "success", "Deployment was not successful"
        assert "deployment_url" in deployment, "No deployment URL returned"
        
        # Save test results
        self.save_test_results(f"ui_workflow_{project_id}.json", {
            "project_id": project_id,
            "requirements": req_text,
            "artifacts_count": len(artifacts),
            "agent_types": list(agent_types),
            "optimization": optimization,
            "deployment": deployment
        })
    
    def test_cli_project_creation_workflow(self):
        """
        Test the workflow starting from CLI project creation through backend processing and frontend generation.
        
        Flow: CLI user creates project → Backend processes → Database stores → Frontend generates → Testing validates
        """
        # 1. Create project via CLI (simulated)
        cli_client = self.client.get_service("cli_tool")
        project_data = {
            "name": "test-cli-project",
            "description": "Test project created via CLI",
            "tech_stack": {
                "frontend": "React",
                "backend": "FastAPI",
                "database": "PostgreSQL"
            }
        }
        
        create_response = cli_client.post("/projects", json_data=project_data)
        self.assert_successful_response(create_response)
        
        project_id = create_response.json().get("id")
        assert project_id, "Project ID not returned in response"
        
        # 2. Verify Backend processed the project
        backend_client = self.client.get_service("backend_agent")
        project_response = backend_client.get(f"/projects/{project_id}")
        self.assert_successful_response(project_response)
        
        project = project_response.json()
        assert project["name"] == project_data["name"], "Project name mismatch"
        
        # 3. Verify Database stored the project
        database_client = self.client.get_service("database_agent")
        db_response = database_client.get(f"/projects/{project_id}/exists")
        self.assert_successful_response(db_response)
        assert db_response.json().get("exists"), "Project not stored in database"
        
        # 4. Add requirements to the project
        requirements_data = self.load_test_data("requirements.json")
        req_text = requirements_data["microservice"]["text"]
        
        requirements_response = cli_client.post(f"/projects/{project_id}/requirements", 
                                              json_data={"text": req_text})
        self.assert_successful_response(requirements_response)
        
        # 5. Verify Frontend generated UI components
        frontend_client = self.client.get_service("frontend_agent")
        
        # Wait for frontend generation to complete
        max_retries = 10
        components_generated = False
        
        for i in range(max_retries):
            components_response = frontend_client.get(f"/projects/{project_id}/components")
            
            if components_response.status_code == 200 and len(components_response.json()) > 0:
                components_generated = True
                break
            
            logger.info(f"Waiting for UI component generation (attempt {i+1}/{max_retries})")
            time.sleep(3)
        
        assert components_generated, "UI components were not generated in time"
        
        components = components_response.json()
        assert len(components) > 0, "No UI components were generated"
        
        # 6. Verify Testing Agent validated the project
        testing_client = self.client.get_service("testing_agent")
        validation_response = testing_client.post(f"/projects/{project_id}/validate")
        self.assert_successful_response(validation_response)
        
        validation = validation_response.json()
        assert validation.get("status") == "success", "Project validation failed"
        assert validation.get("coverage", 0) > 80, "Test coverage below threshold"
        
        # Save test results
        self.save_test_results(f"cli_workflow_{project_id}.json", {
            "project_id": project_id,
            "project_data": project_data,
            "requirements": req_text,
            "components": components,
            "validation": validation
        })
    
    def test_api_gateway_authentication_workflow(self):
        """
        Test the authentication and data flow through API Gateway to backend services.
        
        Flow: API Gateway authentication → Backend operations → Database transactions → Real-time UI updates
        """
        # 1. Register a test user
        api_gateway_client = self.client.get_service("api_gateway")
        user_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "Test@password123"
        }
        
        register_response = api_gateway_client.post("/auth/register", json_data=user_data)
        self.assert_successful_response(register_response)
        
        # 2. Authenticate via API Gateway
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        login_response = api_gateway_client.post("/auth/login", json_data=login_data)
        self.assert_successful_response(login_response)
        
        token = login_response.json().get("access_token")
        assert token, "No access token returned from login"
        
        # 3. Create project through API Gateway
        headers = {"Authorization": f"Bearer {token}"}
        project_data = {
            "name": "auth-flow-test-project",
            "description": "Test project for auth workflow",
            "tech_stack": {
                "frontend": "React",
                "backend": "FastAPI",
                "database": "PostgreSQL"
            }
        }
        
        project_response = api_gateway_client.post(
            "/api/v1/projects", 
            json_data=project_data,
            headers=headers
        )
        self.assert_successful_response(project_response)
        
        project_id = project_response.json().get("id")
        assert project_id, "Project ID not returned in response"
        
        # 4. Verify Backend processed the project
        backend_client = self.client.get_service("backend_agent")
        project_get_response = backend_client.get(f"/projects/{project_id}")
        self.assert_successful_response(project_get_response)
        
        # 5. Verify Database transaction
        database_client = self.client.get_service("database_agent")
        db_response = database_client.get(f"/projects/{project_id}")
        self.assert_successful_response(db_response)
        
        # 6. Add a task to trigger real-time updates
        task_data = {
            "title": "Test Task",
            "description": "Task for testing real-time updates",
            "priority": "high"
        }
        
        task_response = api_gateway_client.post(
            f"/api/v1/projects/{project_id}/tasks", 
            json_data=task_data,
            headers=headers
        )
        self.assert_successful_response(task_response)
        
        task_id = task_response.json().get("id")
        assert task_id, "Task ID not returned in response"
        
        # 7. Verify real-time updates via a separate connection
        # This would typically be verified through websocket connection
        # For simplicity, we'll check if the task is immediately available
        task_get_response = api_gateway_client.get(
            f"/api/v1/tasks/{task_id}", 
            headers=headers
        )
        self.assert_successful_response(task_get_response)
        
        # Save test results
        self.save_test_results(f"auth_workflow_{project_id}.json", {
            "user": user_data["username"],
            "project_id": project_id,
            "task_id": task_id,
            "auth_success": bool(token),
            "real_time_update_verified": task_get_response.status_code == 200
        })