import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import json
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from orchestrator.master_agent import MasterOrchestrator, SaaSRequirements, ProjectType, DeploymentTarget

@pytest.fixture
def orchestrator():
    """Provides a MasterOrchestrator instance for tests."""
    # The config file is expected to be in ../../config/orchestrator.yml from this test file's perspective
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config/orchestrator.yml'))
    return MasterOrchestrator(config_path=config_path)

class MockChoice:
    def __init__(self, content):
        self.message = MagicMock(content=content)

class MockOpenAIResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

def mock_openai_completions(model, messages, **kwargs):
    """Mock for OpenAI chat completions create method."""
    
    system_prompt = ""
    user_prompt = ""

    for msg in messages:
        if msg.get('role') == 'system':
            system_prompt = msg.get('content', '')
        if msg.get('role') == 'user':
            user_prompt = msg.get('content', '')

    if 'expert system architect' in system_prompt:
        architecture = {
            "components": {
                "frontend": {"tech": "React", "framework": "Next.js"},
                "backend": {"tech": "Python", "framework": "FastAPI"},
                "database": {"tech": "PostgreSQL"}
            },
            "database_schema": "users(id, name, email)",
            "api_endpoints": "/api/users"
        }
        return MockOpenAIResponse(json.dumps(architecture))

    if "AGENT_TYPE: frontend" in system_prompt:
        return MockOpenAIResponse(json.dumps({"files": {"src/index.js": "console.log('hello frontend');"}, "dependencies": ["react"] }))
    if "AGENT_TYPE: backend" in system_prompt:
        return MockOpenAIResponse(json.dumps({"files": {"main.py": "print('hello backend')", "requirements.txt": "fastapi"}, "dependencies": ["fastapi"] }))
    if "AGENT_TYPE: database" in system_prompt:
        return MockOpenAIResponse(json.dumps({"files": {"db/schema.sql": "CREATE TABLE users;"}, "dependencies": [] }))
    if "AGENT_TYPE: devops" in system_prompt:
        return MockOpenAIResponse(json.dumps({"files": {"scripts/deploy.sh": "echo deploying..."}, "dependencies": [] }))
    if "AGENT_TYPE: testing" in system_prompt:
        return MockOpenAIResponse(json.dumps({"files": {"tests/test_main.py": "assert True"}, "dependencies": ["pytest"] }))
    if "AGENT_TYPE: security" in system_prompt:
        return MockOpenAIResponse(json.dumps({"files": {"security_report.md": "All good."}, "dependencies": [] }))
    if "AGENT_TYPE: ui_ux" in system_prompt:
        return MockOpenAIResponse(json.dumps({"files": {"design/wireframe.png": "content"}, "dependencies": [] }))

    # Default mock response for any other case
    return MockOpenAIResponse(json.dumps({"files": {"dummy.txt": "dummy content"}}))


@pytest.mark.asyncio
@patch('openai.resources.chat.completions.AsyncCompletions.create', new_callable=AsyncMock)
async def test_create_saas_application_e2e(mock_create_completion, orchestrator):
    """
    End-to-end test for creating a SaaS application.
    Mocks the LLM calls to simulate agent behavior.
    """
    mock_create_completion.side_effect = mock_openai_completions

    requirements = SaaSRequirements(
        description="A simple user management dashboard",
        project_type=ProjectType.WEB_APP,
        features=["user login", "display user list"],
        tech_stack_preferences={"frontend": "React", "backend": "Python"},
        deployment_target=DeploymentTarget.DOCKER,
        scale_requirements={"users": 1000}
    )

    result = await orchestrator.create_saas_application(requirements)

    assert result['status'] == 'success'
    assert result['application_info']['status'] == 'ready_for_deployment'
    assert result['application_info']['target'] == 'docker'
    assert "Dockerfile" in result['application_info']['files']
    assert "README.md" in result['application_info']['files']
    
    # Check that some files from agents are present
    assert "src/index.js" in orchestrator.project_state['codebase']['files']
    assert "main.py" in orchestrator.project_state['codebase']['files']

    # Check if the Dockerfile is generated for a Python project
    dockerfile_content = orchestrator.project_state['codebase']['files']['Dockerfile']
    assert "FROM python" in dockerfile_content
    
    # Check if architecture was created
    assert "architecture" in result
    assert result["architecture"]["components"]["frontend"]["tech"] == "React"

    # Verify that tasks were executed
    assert result["tasks_completed"] > 0
    for task in orchestrator.task_queue:
        assert task.status == 'completed'

if __name__ == "__main__":
    pytest.main(['-v', __file__]) 