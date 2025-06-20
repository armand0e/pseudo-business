#!/usr/bin/env python3
"""
Master Orchestrator Agent for Agentic AI Full-Stack Tech Company

This agent coordinates all specialized agents to create end-to-end SaaS applications
based on user input. It integrates OpenHands, OpenEvolve, and LocalAI.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, is_dataclass
from enum import Enum
import requests
from pathlib import Path

# # OpenHands integration
# from openhands.controller.state.state import State
# from openhands.core.config import AppConfig, SandboxConfig
# from openhands.core.main import create_runtime, run_controller
# from openhands.events.action import CmdRunAction, MessageAction
# from openhands.events.observation import CmdOutputObservation
# from openhands.agenthub.codeact_agent import CodeActAgent

# LocalAI integration
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class ProjectType(Enum):
    WEB_APP = "web_app"
    API_SERVICE = "api_service"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    MICROSERVICE = "microservice"
    FULL_STACK = "full_stack"

class DeploymentTarget(Enum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    VERCEL = "vercel"
    HEROKU = "heroku"
    SELF_HOSTED = "self_hosted"

@dataclass
class SaaSRequirements:
    """User requirements for SaaS application"""
    description: str
    project_type: ProjectType
    features: List[str]
    tech_stack_preferences: Dict[str, str]
    deployment_target: DeploymentTarget
    scale_requirements: Dict[str, Any]
    budget_constraints: Optional[Dict[str, Any]] = None
    timeline: Optional[str] = None

@dataclass
class AgentTask:
    """Task for specialized agent"""
    task_id: str
    agent_type: str
    task_description: str
    dependencies: List[str] # list of task_ids
    priority: int
    estimated_time: int  # minutes
    status: str = "pending"  # pending, in_progress, completed, failed

class MasterOrchestrator:
    """
    Master orchestrator that coordinates all specialized agents
    to create full-stack SaaS applications autonomously.
    """
    
    def __init__(self, config_path: str = "config/orchestrator.yml"):
        self.config = self._load_config(config_path)
        self.local_ai_client = AsyncOpenAI(
            base_url="http://localhost:8080/v1",
            api_key="not-needed"
        )
        self.openhands_agents = {}
        self.specialized_agents = {
            "frontend": FrontendAgent(self.local_ai_client),
            "backend": BackendAgent(self.local_ai_client),
            "database": DatabaseAgent(self.local_ai_client),
            "devops": DevOpsAgent(self.local_ai_client),
            "testing": TestingAgent(self.local_ai_client),
            "security": SecurityAgent(self.local_ai_client),
            "ui_ux": UIUXAgent(self.local_ai_client)
        }
        self.task_queue: List[AgentTask] = []
        self.project_state = {}
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load orchestrator configuration"""
        try:
            with open(config_path, 'r') as f:
                import yaml
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            "max_concurrent_agents": 5,
            "timeout_minutes": 120,
            "retry_attempts": 3,
            "quality_threshold": 0.85,
            "enable_evolution": True,
            "enable_testing": True,
            "enable_security_scan": True
        }
    
    async def create_saas_application(self, requirements: SaaSRequirements) -> Dict[str, Any]:
        """
        Main orchestration method to create a complete SaaS application
        """
        logger.info(f"Starting SaaS application creation: {requirements.description}")
        self.project_state = {'requirements': requirements}

        try:
            # Phase 1: Requirements Analysis & Architecture Design
            architecture = await self._design_architecture(requirements)
            self.project_state['architecture'] = architecture
            
            # Phase 2: Task Decomposition
            tasks = await self._decompose_tasks(requirements, architecture)
            
            # Phase 3: Agent Coordination & Execution
            results = await self._execute_tasks(tasks)
            
            # Phase 4: Integration & Testing
            integration_result = await self._integrate_components(results)
            
            # Phase 5: Quality Assurance & Evolution
            if self.config["enable_evolution"]:
                evolved_result = await self._evolve_solution(integration_result)
            else:
                evolved_result = integration_result
            
            # Phase 6: Deployment
            deployment_result = await self._deploy_application(
                evolved_result, requirements.deployment_target
            )
            
            return {
                "status": "success",
                "application_info": deployment_result,
                "architecture": architecture,
                "tasks_completed": len(tasks),
                "quality_score": await self._calculate_quality_score(evolved_result),
                "deployment_url": deployment_result.get("url"),
                "project_files": evolved_result.get("files", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to create SaaS application: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "partial_results": self.project_state
            }
    
    async def _design_architecture(self, requirements: SaaSRequirements) -> Dict[str, Any]:
        """Design system architecture using Devstral model"""
        prompt = f"""
        Design a comprehensive system architecture for the following SaaS application:
        
        Description: {requirements.description}
        Project Type: {requirements.project_type.value}
        Features: {', '.join(requirements.features)}
        Tech Stack Preferences: {requirements.tech_stack_preferences}
        Scale Requirements: {requirements.scale_requirements}
        
        Provide a detailed architecture including:
        1. System components and their relationships
        2. Database schema design
        3. API endpoints and data flow
        4. Infrastructure requirements
        5. Security considerations
        6. Scalability patterns
        7. Technology recommendations
        
        Format the response as JSON with clear sections.
        """
        
        response = await self.local_ai_client.chat.completions.create(
            model="devstral-small-agentic",
            messages=[
                {"role": "system", "content": "You are an expert system architect."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # Fallback to structured parsing
            return self._parse_architecture_response(response.choices[0].message.content)
    
    async def _decompose_tasks(self, requirements: SaaSRequirements, architecture: Dict[str, Any]) -> List[AgentTask]:
        """Decompose project into specific agent tasks"""
        tasks = []
        
        # Frontend tasks
        if "frontend" in architecture.get("components", {}):
            setup_task = AgentTask("frontend-1", "frontend", "Setup project structure and build tools", [], 1, 30)
            ui_task = AgentTask("frontend-2", "frontend", "Implement UI components", [setup_task.task_id], 2, 120)
            api_task = AgentTask("frontend-3", "frontend", "Integrate with backend APIs", [ui_task.task_id], 3, 60)
            responsive_task = AgentTask("frontend-4", "frontend", "Add responsive design", [api_task.task_id], 4, 45)
            tasks.extend([setup_task, ui_task, api_task, responsive_task])
        
        # Backend tasks
        if "backend" in architecture.get("components", {}):
            setup_api = AgentTask("backend-1", "backend", "Setup API framework", [], 1, 30)
            business_logic = AgentTask("backend-2", "backend", "Implement core business logic", [setup_api.task_id], 2, 180)
            auth_task = AgentTask("backend-3", "backend", "Add authentication & authorization", [business_logic.task_id], 3, 90)
            endpoints_task = AgentTask("backend-4", "backend", "Implement API endpoints", [auth_task.task_id], 4, 120)
            tasks.extend([setup_api, business_logic, auth_task, endpoints_task])
        
        # Database tasks
        if "database" in architecture.get("components", {}):
            schema_task = AgentTask("database-1", "database", "Design database schema", [], 1, 45)
            setup_db_task = AgentTask("database-2", "database", "Setup database with migrations", [schema_task.task_id], 2, 30)
            optimize_db_task = AgentTask("database-3", "database", "Optimize queries and indexing", [setup_db_task.task_id], 3, 60)
            tasks.extend([schema_task, setup_db_task, optimize_db_task])
        
        # DevOps tasks
        container_task = AgentTask("devops-1", "devops", "Setup containerization", [], 2, 45)
        cicd_task = AgentTask("devops-2", "devops", "Configure CI/CD pipeline", [container_task.task_id], 3, 90)
        monitoring_task = AgentTask("devops-3", "devops", "Setup monitoring and logging", [cicd_task.task_id], 4, 60)
        tasks.extend([container_task, cicd_task, monitoring_task])
        
        # Testing tasks
        if self.config["enable_testing"]:
            testing_deps = []
            if "frontend-2" in [t.task_id for t in tasks]:
                testing_deps.append("frontend-2")
            if "backend-4" in [t.task_id for t in tasks]:
                testing_deps.append("backend-4")

            setup_test = AgentTask("testing-1", "testing", "Setup testing framework", [], 2, 30)
            unit_test = AgentTask("testing-2", "testing", "Write unit tests", [setup_test.task_id] + testing_deps, 3, 120)
            integration_test = AgentTask("testing-3", "testing", "Write integration tests", [unit_test.task_id], 4, 90)
            e2e_test = AgentTask("testing-4", "testing", "Setup E2E testing", [integration_test.task_id], 5, 60)
            tasks.extend([setup_test, unit_test, integration_test, e2e_test])

        # Security tasks
        if self.config["enable_security_scan"]:
            security_audit = AgentTask("security-1", "security", "Security audit and recommendations", [], 4, 45)
            implement_security = AgentTask("security-2", "security", "Implement security measures", [security_audit.task_id], 5, 60)
            tasks.extend([security_audit, implement_security])

        self.task_queue = tasks
        return tasks
    
    async def _execute_tasks(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """Execute all tasks in an order that respects dependencies."""
        completed_tasks = set()
        results = {}
        semaphore = asyncio.Semaphore(self.config["max_concurrent_agents"])
        
        while len(completed_tasks) < len(tasks):
            tasks_to_run = [
                task for task in tasks
                if task.status == "pending" and all(dep in completed_tasks for dep in task.dependencies)
            ]

            if not tasks_to_run:
                # Handle deadlock or cycle
                pending_tasks = [t.task_id for t in tasks if t.status == "pending"]
                logger.error(f"Cannot execute more tasks. Check for dependency cycles. Pending tasks: {pending_tasks}")
                # Mark remaining tasks as failed
                for task in tasks:
                    if task.status == "pending":
                        task.status = "failed"
                        results[task.task_id] = {"error": "Dependency cycle or unresolved dependency"}
                break

            async def execute_task(task: AgentTask):
                async with semaphore:
                    agent = self.specialized_agents.get(task.agent_type)
                    if not agent:
                        logger.error(f"No agent found for type: {task.agent_type}")
                        task.status = "failed"
                        results[task.task_id] = {"error": f"Agent {task.agent_type} not found."}
                        return

                    try:
                        task.status = "in_progress"
                        logger.info(f"Executing task: {task.task_description} with {task.agent_type} agent")
                        
                        context = {
                            "requirements": self.project_state.get("requirements"),
                            "architecture": self.project_state.get("architecture"),
                            "dependencies_results": {dep: results.get(dep) for dep in task.dependencies}
                        }
                        
                        result = await agent.execute_task(task.task_description, context)
                        
                        task.status = "completed"
                        results[task.task_id] = result
                        completed_tasks.add(task.task_id)
                        logger.info(f"Task '{task.task_description}' completed successfully")

                    except Exception as e:
                        task.status = "failed"
                        logger.error(f"Task '{task.task_description}' failed: {str(e)}")
                        results[task.task_id] = {"error": str(e)}

            await asyncio.gather(*(execute_task(task) for task in tasks_to_run))

        if any(t.status == 'failed' for t in tasks):
            # This is a simplification. A real implementation might have more sophisticated error handling.
            raise Exception("One or more tasks failed. See logs for details.")

        return results
    
    async def _integrate_components(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate all generated code components into a final project structure."""
        logger.info("Integrating all components into a cohesive codebase.")
        
        final_codebase = {"files": {}}
        all_dependencies = set()

        for task_id, result in results.items():
            if "files" in result:
                for file_path, content in result["files"].items():
                    # Simple merge, last write wins. A more sophisticated strategy may be needed.
                    final_codebase["files"][file_path] = content
            if "dependencies" in result:
                all_dependencies.update(result["dependencies"])

        final_codebase["dependencies"] = list(all_dependencies)
        
        # Add a README file summarizing the project
        final_codebase["files"]["README.md"] = self._generate_readme(final_codebase)

        logger.info(f"Integration complete. Codebase has {len(final_codebase['files'])} files.")
        self.project_state['codebase'] = final_codebase
        return final_codebase
    
    def _generate_readme(self, codebase: Dict[str, Any]) -> str:
        """Generate a README.md for the project."""
        readme_content = f"# {self.project_state['requirements'].description}\n\n"
        readme_content += "This project was automatically generated by the Agentic AI platform.\n\n"
        readme_content += "## Architecture\n\n"
        readme_content += f"```json\n{json.dumps(self.project_state.get('architecture', {}), indent=2)}\n```\n\n"
        readme_content += "## Files\n\n"
        for f in codebase['files']:
            readme_content += f"- `{f}`\n"
        return readme_content

    async def _evolve_solution(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Use an LLM to suggest and apply improvements."""
        logger.info("Starting solution evolution phase.")
        if not self.config.get("enable_evolution", False):
            logger.info("Evolution is disabled. Skipping.")
            return solution

        improvements = await self._generate_improvements(solution)
        
        # For now, we'll just log the improvements.
        # A full implementation would use OpenHands to apply them.
        logger.info(f"Generated improvements:\n{json.dumps(improvements, indent=2)}")
        
        solution["improvements"] = improvements
        return solution

    async def _deploy_application(self, solution: Dict[str, Any], target: DeploymentTarget) -> Dict[str, Any]:
        """Prepare application for deployment."""
        logger.info(f"Preparing deployment for target: {target.value}")

        if target == DeploymentTarget.DOCKER:
            dockerfile_content = self._generate_dockerfile(solution)
            solution["files"]["Dockerfile"] = dockerfile_content
            logger.info("Generated Dockerfile.")

        # In a real scenario, this would trigger a CI/CD pipeline
        # For now, we return the solution with deployment artifacts
        deployment_info = {
            "status": "ready_for_deployment",
            "target": target.value,
            "url": f"http://localhost:3000/{self.project_state['requirements'].description.replace(' ', '-').lower()}",
            "files": list(solution["files"].keys())
        }
        return deployment_info
    
    def _generate_dockerfile(self, solution: Dict[str, Any]) -> str:
        """Generates a basic Dockerfile based on the project."""
        # This is a very basic heuristic. A real implementation would be more robust.
        if "package.json" in solution["files"]: # NodeJS
            return """
FROM node:18-alpine
WORKDIR /usr/src/app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD [ "node", "index.js" ]
"""
        elif "requirements.txt" in solution["files"]: # Python
            return """
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD [ "python", "main.py" ]
"""
        else:
            return "# Could not determine project type to generate Dockerfile."

    async def _calculate_quality_score(self, solution: Dict[str, Any]) -> float:
        """Calculate a quality score for the generated solution."""
        # Implement quality metrics calculation
        # This would include code quality, test coverage, performance, security, etc.
        return 0.9  # Placeholder
    
    async def _generate_improvements(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Generate improvements using evolutionary approach"""
        # Placeholder for OpenEvolve integration
        return solution
    
    def _parse_architecture_response(self, response: str) -> Dict[str, Any]:
        """Parse architecture response when JSON parsing fails"""
        # Implement robust parsing for non-JSON responses
        return {
            "components": {"frontend": {}, "backend": {}, "database": {}},
            "raw_response": response
        }

# Specialized Agent Classes
class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, Enum):
            return o.value
        return super().default(o)

class BaseSpecializedAgent:
    """Base class for all specialized agents"""
    
    def __init__(self, llm_client: AsyncOpenAI):
        self.llm_client = llm_client

    async def execute_task(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using the LLM"""
        prompt = self._build_prompt(task_description, context)
        
        response = await self.llm_client.chat.completions.create(
            model="devstral-small-agentic",
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(response.choices[0].message.content)

    def _get_system_prompt(self) -> str:
        raise NotImplementedError

    def _build_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """Build a detailed prompt for the LLM"""
        return f"""
        Task: {task}
        Context: {json.dumps(context, indent=2, cls=CustomEncoder)}
        """

class FrontendAgent(BaseSpecializedAgent):
    def __init__(self, llm_client: AsyncOpenAI):
        super().__init__(llm_client)
        self.agent_type = "frontend"
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent"""
        return """AGENT_TYPE: frontend
        You are an expert frontend developer. Your goal is to create high-quality,
        maintainable, and responsive user interfaces based on the given requirements.
        """

class BackendAgent(BaseSpecializedAgent):
    def __init__(self, llm_client: AsyncOpenAI):
        super().__init__(llm_client)
        self.agent_type = "backend"
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent"""
        return """AGENT_TYPE: backend
        You are an expert backend developer. Your goal is to create robust, scalable,
        and secure server-side applications and APIs.
        
        Provide your output as a JSON object with a "files" key, where each key
        """

class DatabaseAgent(BaseSpecializedAgent):
    def __init__(self, llm_client: AsyncOpenAI):
        super().__init__(llm_client)
        self.agent_type = "database"
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent"""
        return """AGENT_TYPE: database
        You are an expert database administrator. Your goal is to design, implement,
        and maintain efficient and secure database schemas.
        
        Provide your output as a JSON object with a "files" key, where each key
        """

class DevOpsAgent(BaseSpecializedAgent):
    def __init__(self, llm_client: AsyncOpenAI):
        super().__init__(llm_client)
        self.agent_type = "devops"
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent"""
        return """AGENT_TYPE: devops
        You are an expert DevOps engineer. Your goal is to automate the build, test,
        and deployment pipeline to ensure continuous integration and delivery.
        
        Provide your output as a JSON object with a "files" key, where each key
        """

class TestingAgent(BaseSpecializedAgent):
    def __init__(self, llm_client: AsyncOpenAI):
        super().__init__(llm_client)
        self.agent_type = "testing"
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent"""
        return """AGENT_TYPE: testing
        You are an expert QA engineer. Your goal is to ensure the quality of the
        application by writing and executing unit, integration, and end-to-end tests.
        
        Provide your output as a JSON object with a "files" key, where each key
        """

class SecurityAgent(BaseSpecializedAgent):
    def __init__(self, llm_client: AsyncOpenAI):
        super().__init__(llm_client)
        self.agent_type = "security"
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent"""
        return """AGENT_TYPE: security
        You are a cybersecurity expert. Your goal is to identify and mitigate
        security vulnerabilities in the application and infrastructure.
        
        Provide your output as a JSON object with a "files" key, where each key
        """

class UIUXAgent(BaseSpecializedAgent):
    def __init__(self, llm_client: AsyncOpenAI):
        super().__init__(llm_client)
        self.agent_type = "ui_ux"
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent"""
        return """AGENT_TYPE: ui_ux
        You are an expert UI/UX designer. Your goal is to create intuitive,
        user-friendly, and visually appealing user interfaces.
        
        Provide your output as a JSON object with a "files" key, where each key
        """

# Main execution function
async def main():
    """Main execution function for testing"""
    orchestrator = MasterOrchestrator()
    
    # Example SaaS requirements
    requirements = SaaSRequirements(
        description="A project management SaaS with team collaboration features",
        project_type=ProjectType.FULL_STACK,
        features=[
            "User authentication",
            "Project creation and management",
            "Task assignment and tracking",
            "Real-time collaboration",
            "File sharing",
            "Reporting dashboard"
        ],
        tech_stack_preferences={
            "frontend": "React with TypeScript",
            "backend": "FastAPI with Python",
            "database": "PostgreSQL",
            "deployment": "Docker + Kubernetes"
        },
        deployment_target=DeploymentTarget.KUBERNETES,
        scale_requirements={
            "concurrent_users": 1000,
            "data_storage": "100GB",
            "response_time": "< 200ms"
        }
    )
    
    # Create the SaaS application
    result = await orchestrator.create_saas_application(requirements)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 