"""
Component Integration Tests

This module tests interactions between specific components of the
Agentic AI Development Platform to verify they integrate correctly.
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

class TestComponentIntegrations(IntegrationTestBase):
    """Test integrations between specific platform components."""
    
    def test_master_orchestrator_agent_coordination(self):
        """
        Test the interaction between Master Orchestrator and all agent components.
        
        Flow: Master Orchestrator → Agent Coordinator → All Agents
        """
        orchestrator_client = self.client.get_service("master_orchestrator")
        
        # Create a test requirement
        requirements_data = self.load_test_data("requirements.json")
        req_text = requirements_data["basic_webapp"]["text"]
        
        # Send to orchestrator
        response = orchestrator_client.post("/process", json_data={"text": req_text})
        self.assert_successful_response(response)
        
        result = response.json()
        assert "tasks" in result, "No tasks returned from orchestrator"
        
        # Verify tasks were assigned to the correct agents
        tasks = result["tasks"]
        agent_assignments = {}
        
        for task in tasks:
            agent_type = task.get("agent_type")
            if agent_type:
                agent_assignments.setdefault(agent_type, []).append(task)
        
        # Verify all expected agent types received tasks
        expected_agents = ["frontend", "backend", "database", "testing", "devops"]
        for agent in expected_agents:
            assert agent in agent_assignments, f"No tasks assigned to {agent} agent"
            assert len(agent_assignments[agent]) > 0, f"Empty task list for {agent} agent"
        
        # Verify task completion
        project_id = result.get("project_id")
        assert project_id, "No project ID returned"
        
        # Wait for tasks to complete
        max_retries = 12
        tasks_completed = False
        
        for i in range(max_retries):
            status_response = orchestrator_client.get(f"/projects/{project_id}/status")
            self.assert_successful_response(status_response)
            status = status_response.json()
            
            if status.get("tasks_completed", 0) == status.get("total_tasks", 1):
                tasks_completed = True
                break
            
            logger.info(f"Waiting for tasks to complete (attempt {i+1}/{max_retries})")
            time.sleep(5)
        
        assert tasks_completed, "Tasks did not complete in the expected time"
        
        # Save test results
        self.save_test_results("master_orchestrator_agent_integration.json", {
            "project_id": project_id,
            "requirements": req_text,
            "agent_assignments": {agent: len(tasks) for agent, tasks in agent_assignments.items()},
            "tasks_completed": tasks_completed
        })
    
    def test_api_gateway_backend_integration(self):
        """
        Test the interaction between API Gateway and Backend Services.
        
        Flow: API Gateway → Backend Services
        """
        api_client = self.client.get_service("api_gateway")
        backend_client = self.client.get_service("backend_agent")
        
        # 1. Register and authenticate a user
        user_data = {
            "username": f"gateway_test_{int(time.time())}",
            "email": f"gateway_{int(time.time())}@example.com",
            "password": "Gateway@123"
        }
        
        # Register user through gateway
        register_response = api_client.post("/auth/register", json_data=user_data)
        self.assert_successful_response(register_response)
        
        # Login to get token
        login_response = api_client.post("/auth/login", 
                                        json_data={
                                            "username": user_data["username"],
                                            "password": user_data["password"]
                                        })
        self.assert_successful_response(login_response)
        
        token = login_response.json().get("access_token")
        assert token, "No access token returned"
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create project through gateway
        project_data = {
            "name": "Gateway-Backend Test",
            "description": "Project to test gateway-backend integration",
            "tech_stack": {
                "frontend": "React",
                "backend": "FastAPI",
                "database": "PostgreSQL"
            }
        }
        
        gateway_project_response = api_client.post(
            "/api/v1/projects",
            json_data=project_data,
            headers=headers
        )
        self.assert_successful_response(gateway_project_response)
        
        project_id = gateway_project_response.json().get("id")
        assert project_id, "No project ID returned"
        
        # 3. Verify the project exists in backend
        backend_project_response = backend_client.get(f"/projects/{project_id}")
        self.assert_successful_response(backend_project_response)
        
        backend_project = backend_project_response.json()
        assert backend_project["name"] == project_data["name"], "Project name mismatch between gateway and backend"
        
        # 4. Add task through gateway
        task_data = {
            "title": "Integration Test Task",
            "description": "Task created via gateway for backend integration test",
            "priority": "high"
        }
        
        gateway_task_response = api_client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json_data=task_data,
            headers=headers
        )
        self.assert_successful_response(gateway_task_response)
        
        task_id = gateway_task_response.json().get("id")
        assert task_id, "No task ID returned"
        
        # 5. Verify task exists in backend
        backend_task_response = backend_client.get(f"/tasks/{task_id}")
        self.assert_successful_response(backend_task_response)
        
        backend_task = backend_task_response.json()
        assert backend_task["title"] == task_data["title"], "Task title mismatch between gateway and backend"
        
        # Save test results
        self.save_test_results("api_gateway_backend_integration.json", {
            "user": user_data["username"],
            "project_id": project_id,
            "task_id": task_id,
            "data_consistency_verified": True
        })
    
    def test_backend_database_integration(self):
        """
        Test the interaction between Backend Agent and Database Agent.
        
        Flow: Backend Agent → Database Agent
        """
        backend_client = self.client.get_service("backend_agent")
        database_client = self.client.get_service("database_agent")
        
        # 1. Create a project via backend
        project_data = {
            "name": "DB Integration Test",
            "description": "Project to test backend-database integration",
            "tech_stack": {
                "frontend": "Vue",
                "backend": "Django",
                "database": "MySQL"
            }
        }
        
        project_response = backend_client.post("/projects", json_data=project_data)
        self.assert_successful_response(project_response)
        
        project_id = project_response.json().get("id")
        assert project_id, "No project ID returned"
        
        # 2. Verify project exists in database
        db_project_response = database_client.get(f"/projects/{project_id}")
        self.assert_successful_response(db_project_response)
        
        db_project = db_project_response.json()
        assert db_project["name"] == project_data["name"], "Project name mismatch in database"
        
        # 3. Create a user
        user_data = {
            "username": f"db_test_{int(time.time())}",
            "email": f"db_{int(time.time())}@example.com",
            "password": "Db@123456"
        }
        
        user_response = backend_client.post("/users", json_data=user_data)
        self.assert_successful_response(user_response)
        
        user_id = user_response.json().get("id")
        assert user_id, "No user ID returned"
        
        # 4. Verify user exists in database
        db_user_response = database_client.get(f"/users/{user_id}")
        self.assert_successful_response(db_user_response)
        
        # 5. Update project via backend
        updated_project_data = {
            "name": "Updated DB Integration Test",
            "description": "Updated description for integration test"
        }
        
        update_response = backend_client.put(
            f"/projects/{project_id}",
            json_data=updated_project_data
        )
        self.assert_successful_response(update_response)
        
        # 6. Verify update is reflected in database
        updated_db_response = database_client.get(f"/projects/{project_id}")
        self.assert_successful_response(updated_db_response)
        
        updated_db_project = updated_db_response.json()
        assert updated_db_project["name"] == updated_project_data["name"], "Updated project name not in database"
        
        # 7. Delete project via backend
        delete_response = backend_client.delete(f"/projects/{project_id}")
        self.assert_successful_response(delete_response)
        
        # 8. Verify project is deleted in database
        deleted_db_response = database_client.get(f"/projects/{project_id}/exists")
        self.assert_successful_response(deleted_db_response)
        assert not deleted_db_response.json().get("exists", True), "Project still exists in database after deletion"
        
        # Save test results
        self.save_test_results("backend_database_integration.json", {
            "project_id": project_id,
            "user_id": user_id,
            "create_verified": True,
            "read_verified": True,
            "update_verified": True,
            "delete_verified": True
        })
    
    def test_frontend_ui_integration(self):
        """
        Test the interaction between Frontend Agent and UI Components.
        
        Flow: Frontend Agent → UI Components
        """
        frontend_client = self.client.get_service("frontend_agent")
        ui_client = self.client.get_service("user_interface")
        
        # 1. Generate UI components via Frontend Agent
        ui_spec = {
            "components": [
                {
                    "type": "form",
                    "name": "UserForm",
                    "fields": [
                        {"name": "username", "type": "text", "required": True},
                        {"name": "email", "type": "email", "required": True},
                        {"name": "password", "type": "password", "required": True}
                    ]
                },
                {
                    "type": "table",
                    "name": "TaskTable",
                    "columns": [
                        {"name": "title", "type": "text"},
                        {"name": "status", "type": "text"},
                        {"name": "priority", "type": "text"},
                        {"name": "actions", "type": "actions"}
                    ]
                }
            ]
        }
        
        generate_response = frontend_client.post("/generate", json_data=ui_spec)
        self.assert_successful_response(generate_response)
        
        generation_id = generate_response.json().get("id")
        assert generation_id, "No generation ID returned"
        
        # 2. Wait for component generation to complete
        max_retries = 10
        components_generated = False
        
        for i in range(max_retries):
            status_response = frontend_client.get(f"/generate/{generation_id}/status")
            
            if status_response.status_code == 200 and status_response.json().get("status") == "completed":
                components_generated = True
                break
            
            logger.info(f"Waiting for component generation (attempt {i+1}/{max_retries})")
            time.sleep(3)
        
        assert components_generated, "Component generation did not complete in time"
        
        # 3. Retrieve generated components
        components_response = frontend_client.get(f"/generate/{generation_id}/components")
        self.assert_successful_response(components_response)
        
        components = components_response.json()
        assert len(components) > 0, "No components were generated"
        
        # 4. Verify UI can render the components
        ui_render_response = ui_client.post("/api/render", json_data={"components": components})
        self.assert_successful_response(ui_render_response)
        
        render_result = ui_render_response.json()
        assert render_result.get("success"), "UI failed to render components"
        assert "rendered_components" in render_result, "No rendered components returned"
        
        # Save test results
        self.save_test_results("frontend_ui_integration.json", {
            "generation_id": generation_id,
            "components_count": len(components),
            "component_types": [comp.get("type") for comp in components if "type" in comp],
            "rendering_success": render_result.get("success", False)
        })
    
    def test_devops_services_integration(self):
        """
        Test the interaction between DevOps Agent and all services for deployment.
        
        Flow: DevOps Agent → All Services
        """
        devops_client = self.client.get_service("devops_agent")
        
        # 1. Create a simple deployment config
        deployment_config = {
            "project_id": f"test_{int(time.time())}",
            "environment": "testing",
            "services": [
                {"name": "frontend", "port": 3000, "replicas": 1},
                {"name": "backend", "port": 8000, "replicas": 1},
                {"name": "database", "port": 5432, "replicas": 1}
            ],
            "deployment_type": "docker-compose"
        }
        
        # 2. Start deployment
        deploy_response = devops_client.post("/deploy", json_data=deployment_config)
        self.assert_successful_response(deploy_response)
        
        deployment_id = deploy_response.json().get("id")
        assert deployment_id, "No deployment ID returned"
        
        # 3. Wait for deployment completion
        max_retries = 15
        deployment_completed = False
        
        for i in range(max_retries):
            status_response = devops_client.get(f"/deploy/{deployment_id}/status")
            
            if status_response.status_code == 200 and status_response.json().get("status") == "completed":
                deployment_completed = True
                break
            
            logger.info(f"Waiting for deployment completion (attempt {i+1}/{max_retries})")
            time.sleep(5)
        
        assert deployment_completed, "Deployment did not complete in time"
        
        # 4. Verify each service was deployed
        services_response = devops_client.get(f"/deploy/{deployment_id}/services")
        self.assert_successful_response(services_response)
        
        services = services_response.json()
        assert len(services) == len(deployment_config["services"]), "Not all services were deployed"
        
        # 5. Verify services are running
        for service in services:
            status_response = devops_client.get(f"/services/{service['id']}/status")
            self.assert_successful_response(status_response)
            assert status_response.json().get("running"), f"Service {service['name']} is not running"
        
        # 6. Test health of all deployed services
        for service in services:
            health_response = devops_client.get(f"/services/{service['id']}/health")
            self.assert_successful_response(health_response)
            assert health_response.json().get("healthy"), f"Service {service['name']} is not healthy"
        
        # 7. Cleanup deployment
        cleanup_response = devops_client.delete(f"/deploy/{deployment_id}")
        self.assert_successful_response(cleanup_response)
        
        # Save test results
        self.save_test_results("devops_services_integration.json", {
            "deployment_id": deployment_id,
            "services_deployed": len(services),
            "service_names": [service["name"] for service in services],
            "deployment_success": deployment_completed,
            "cleanup_success": cleanup_response.status_code == 200
        })
    
    def test_testing_components_integration(self):
        """
        Test the interaction between Testing Agent and all other components.
        
        Flow: Testing Agent → All Components
        """
        testing_client = self.client.get_service("testing_agent")
        
        # 1. Create a testing configuration
        test_config = {
            "project_id": f"test_{int(time.time())}",
            "components": ["frontend", "backend", "database", "api"],
            "test_types": ["unit", "integration", "e2e"],
            "coverage_threshold": 80.0,
            "security_scan": True
        }
        
        # 2. Start the testing process
        test_response = testing_client.post("/test", json_data=test_config)
        self.assert_successful_response(test_response)
        
        test_run_id = test_response.json().get("id")
        assert test_run_id, "No test run ID returned"
        
        # 3. Wait for testing completion
        max_retries = 15
        testing_completed = False
        
        for i in range(max_retries):
            status_response = testing_client.get(f"/test/{test_run_id}/status")
            
            if status_response.status_code == 200 and status_response.json().get("status") == "completed":
                testing_completed = True
                break
            
            logger.info(f"Waiting for testing completion (attempt {i+1}/{max_retries})")
            time.sleep(5)
        
        assert testing_completed, "Testing did not complete in time"
        
        # 4. Get test results
        results_response = testing_client.get(f"/test/{test_run_id}/results")
        self.assert_successful_response(results_response)
        
        test_results = results_response.json()
        
        # 5. Verify results for each component
        for component in test_config["components"]:
            assert component in test_results, f"No test results for {component}"
            component_results = test_results[component]
            
            # Verify test counts
            assert "tests" in component_results, f"No tests count for {component}"
            assert component_results["tests"] > 0, f"No tests run for {component}"
            
            # Verify coverage
            assert "coverage" in component_results, f"No coverage data for {component}"
            assert component_results["coverage"] >= 0, f"Invalid coverage for {component}"
        
        # 6. Verify security scan results
        security_response = testing_client.get(f"/test/{test_run_id}/security")
        self.assert_successful_response(security_response)
        
        security_results = security_response.json()
        assert "scan_completed" in security_results, "No security scan status"
        assert security_results["scan_completed"], "Security scan did not complete"
        
        # Save test results
        self.save_test_results("testing_components_integration.json", {
            "test_run_id": test_run_id,
            "components_tested": test_config["components"],
            "overall_success": test_results.get("success", False),
            "coverage": {comp: results.get("coverage", 0) for comp, results in test_results.items() 
                        if comp in test_config["components"]},
            "security_issues_found": len(security_results.get("issues", []))
        })