#!/usr/bin/env python3
"""
Master Orchestrator Agent for Agentic AI Full-Stack Tech Company

This agent coordinates all specialized agents to create end-to-end SaaS applications
based on user input.
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

# NLP Processor integration
from agentic_ai_company.src.orchestrator.nlp_processor import NLPProcessor

# Integration testing framework
from agentic_ai_company.src.orchestrator.integration_testing import (
    IntegrationTestFramework,
    test_frontend_backend_integration,
    test_database_schema_integration
)

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
        # Initialize NLP processor
        self.nlp_processor = NLPProcessor()

        # Initialize integration testing framework
        self.integration_tests = IntegrationTestFramework()
        self._register_default_tests()

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
        """Main orchestration method to create a complete SaaS application"""
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
        """Decompose project into specific agent tasks using NLP and task analysis"""
        tasks = []

        # Analyze requirements with NLP for better task decomposition
        nlp_analysis = self.nlp_processor.analyze_text(requirements.description)
        key_features = self.nlp_processor.extract_key_phrases(requirements.description)

        logger.info(f"NLP Analysis: {nlp_analysis}")
        logger.info(f"Key Features extracted: {key_features}")

        # Frontend tasks
        if "frontend" in architecture.get("components", {}):
            setup_task = AgentTask("frontend-1", "frontend", "Setup project structure and build tools", [], 1, 30)
            ui_task = AgentTask("frontend-2", "frontend", f"Implement UI components for {key_features}", [setup_task.task_id], 2, 120)
            api_task = AgentTask("frontend-3", "frontend", "Integrate with backend APIs", [ui_task.task_id], 3, 60)
            responsive_task = AgentTask("frontend-4", "frontend", "Add responsive design", [api_task.task_id], 4, 45)
            tasks.extend([setup_task, ui_task, api_task, responsive_task])

        # Backend tasks
        if "backend" in architecture.get("components", {}):
            setup_api = AgentTask("backend-1", "backend", "Setup API framework", [], 1, 30)
            business_logic = AgentTask("backend-2", "backend", f"Implement core business logic for {key_features}", [setup_api.task_id], 2, 180)
            auth_task = AgentTask("backend-3", "backend", "Add authentication & authorization", [business_logic.task_id], 3, 90)
            endpoints_task = AgentTask("backend-4", "backend", f"Implement API endpoints for {key_features}", [auth_task.task_id], 4, 120)
            tasks.extend([setup_api, business_logic, auth_task, endpoints_task])

        # Database tasks
        if "database" in architecture.get("components", {}):
            schema_task = AgentTask("database-1", "database", f"Design database schema for {key_features}", [], 1, 45)
            setup_db_task = AgentTask("database-2", "database", "Setup database with migrations", [schema_task.task_id], 2, 30)
            optimize_db_task = AgentTask("database-3", "database", f"Optimize queries and indexing for {key_features}", [setup_db_task.task_id], 3, 60)
            tasks.extend([schema_task, setup_db_task, optimize_db_task])

        # DevOps tasks
        container_task = AgentTask("devops-1", "devops", "Setup containerization", [], 2, 45)
        cicd_task = AgentTask("devops-2", "devops", f"Configure CI/CD pipeline for {key_features}", [container_task.task_id], 3, 90)
        monitoring_task = AgentTask("devops-3", "devops", "Setup monitoring and logging", [cicd_task.task_id], 4, 60)
        tasks.extend([container_task, cicd_task, monitoring_task])

        # Testing tasks
        if self.config["enable_testing"]:
            testing_deps = []
            if "frontend-2" in [t.task_id for t in tasks]:
                testing_deps.append("frontend-2")
            if "backend-4" in [t.task_id for t in tasks]:
                testing_deps.append("backend-4")

            setup_test = AgentTask("testing-1", "testing", f"Setup testing framework for {key_features}", [], 2, 30)
            unit_test = AgentTask("testing-2", "testing", f"Write unit tests for {key_features}", [setup_test.task_id] + testing_deps, 3, 120)
            integration_test = AgentTask("testing-3", "testing", f"Write integration tests for {key_features}", [unit_test.task_id], 4, 90)
            e2e_test = AgentTask("testing-4", "testing", f"Setup E2E testing for {key_features}", [integration_test.task_id], 5, 60)
            tasks.extend([setup_test, unit_test, integration_test, e2e_test])

        # Security tasks
        if self.config["enable_security_scan"]:
            security_audit = AgentTask("security-1", "security", f"Security audit for {key_features}", [], 4, 45)
            implement_security = AgentTask("security-2", "security", f"Implement security measures for {key_features}", [security_audit.task_id], 5, 60)
            tasks.extend([security_audit, implement_security])

        self.task_queue = tasks
        return tasks

    async def _execute_tasks(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """Execute all tasks in an order that respects dependencies with enhanced error handling."""
        completed_tasks = set()
        results = {}
        semaphore = asyncio.Semaphore(self.config["max_concurrent_agents"])

        # Create a task execution tracker for better monitoring
        self.project_state['task_execution'] = {
            'total_tasks': len(tasks),
            'completed': 0,
            'failed': 0,
            'in_progress': 0,
            'pending': len(tasks)
        }

        while len(completed_tasks) < len(tasks):
            tasks_to_run = [
                task for task in tasks
                if task.status == "pending" and all(dep in completed_tasks for dep in task.dependencies)
            ]

            if not tasks_to_run:
                # Handle deadlock or cycle with more detailed error reporting
                pending_tasks = [t.task_id for t in tasks if t.status == "pending"]
                logger.error(f"Cannot execute more tasks. Check for dependency cycles. Pending tasks: {pending_tasks}")

                # Try to identify the cycle and suggest a fix
                self._detect_dependency_cycle(tasks, pending_tasks)

                # Mark remaining tasks as failed with detailed error messages
                for task in tasks:
                    if task.status == "pending":
                        task.status = "failed"
                        results[task.task_id] = {"error": f"Dependency cycle detected: {task.task_id} waiting on {[dep for dep in task.dependencies if dep not in completed_tasks]}"}
                break

            async def execute_task(task: AgentTask):
                nonlocal completed_tasks, results
                async with semaphore:
                    agent = self.specialized_agents.get(task.agent_type)
                    if not agent:
                        logger.error(f"No agent found for type: {task.agent_type}")
                        task.status = "failed"
                        results[task.task_id] = {"error": f"Agent {task.agent_type} not found."}
                        self._update_task_execution_status(task, 'failed')
                        return

                    try:
                        # Set task status and update tracker
                        task.status = "in_progress"
                        self._update_task_execution_status(task, 'in_progress')

                        logger.info(f"Executing task: {task.task_description} with {task.agent_type} agent")

                        context = {
                            "requirements": self.project_state.get("requirements"),
                            "architecture": self.project_state.get("architecture"),
                            "dependencies_results": {dep: results.get(dep) for dep in task.dependencies}
                        }

                        # Add timeout to prevent hanging tasks
                        result = await asyncio.wait_for(
                            agent.execute_task(task.task_description, context),
                            timeout=self.config["timeout_minutes"] * 60
                        )

                        task.status = "completed"
                        results[task.task_id] = result
                        completed_tasks.add(task.task_id)
                        self._update_task_execution_status(task, 'completed')
                        logger.info(f"Task '{task.task_description}' completed successfully")

                    except asyncio.TimeoutError:
                        task.status = "failed"
                        error_msg = f"Task '{task.task_description}' timed out after {self.config['timeout_minutes']} minutes"
                        logger.error(error_msg)
                        results[task.task_id] = {"error": error_msg}
                        self._update_task_execution_status(task, 'failed')

                    except Exception as e:
                        task.status = "failed"
                        error_msg = f"Task '{task.task_description}' failed: {str(e)}"
                        logger.error(error_msg)
                        results[task.task_id] = {"error": error_msg}
                        self._update_task_execution_status(task, 'failed')

            # Execute tasks with progress reporting
            if tasks_to_run:
                running_tasks = [execute_task(task) for task in tasks_to_run]
                # Add progress reporting during execution
                while running_tasks:
                    await asyncio.sleep(5)  # Check every 5 seconds
                    completed = sum(1 for t in tasks_to_run if t.status == 'completed')
                    failed = sum(1 for t in tasks_to_run if t.status == 'failed')
                    in_progress = len([t for t in running_tasks if not t.done()])
                    logger.info(f"Task execution progress: {completed} completed, {failed} failed, {in_progress} in progress")

                    # Remove completed tasks from the list
                    running_tasks = [t for t in running_tasks if not t.done()]

                # Wait for all to complete
                await asyncio.gather(*running_tasks)

        # Final error checking with detailed reporting
        failed_tasks = [t.task_id for t in tasks if t.status == 'failed']
        if failed_tasks:
            error_report = self._generate_error_report(failed_tasks, results)
            logger.error(f"Task execution completed with errors:\n{error_report}")
            raise Exception(f"One or more tasks failed. See logs for details. Failed tasks: {failed_tasks}")

        return results

    async def _integrate_components(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate all generated code components into a final project structure."""
        logger.info("Integrating all components into a cohesive codebase.")

        # Track integration progress
        self.project_state['integration_progress'] = {
            'total_files': 0,
            'processed_files': 0,
            'errors': []
        }

        final_codebase = {"files": {}}
        all_dependencies = set()

        for task_id, result in results.items():
            try:
                if "files" in result:
                    # Process each file with validation
                    for file_path, content in result["files"].items():
                        self.project_state['integration_progress']['total_files'] += 1

                        # Validate file content before adding
                        if not self._validate_file_content(file_path, content):
                            error_msg = f"Invalid content in {file_path} from task {task_id}"
                            logger.warning(error_msg)
                            self.project_state['integration_progress']['errors'].append(error_msg)
                            continue

                        # Simple merge, last write wins. A more sophisticated strategy may be needed.
                        final_codebase["files"][file_path] = content
                        self.project_state['integration_progress']['processed_files'] += 1

                if "dependencies" in result:
                    all_dependencies.update(result["dependencies"])
            except Exception as e:
                error_msg = f"Error processing files from task {task_id}: {str(e)}"
                logger.error(error_msg)
                self.project_state['integration_progress']['errors'].append(error_msg)

        final_codebase["dependencies"] = list(all_dependencies)

        # Add a README file summarizing the project
        try:
            readme_content = self._generate_readme(final_codebase)
            final_codebase["files"]["README.md"] = readme_content
            logger.info("Generated README.md successfully")
        except Exception as e:
            logger.error(f"Error generating README: {str(e)}")
            self.project_state['integration_progress']['errors'].append(f"README generation error: {str(e)}")

        # Add a code aggregator report
        try:
            aggregator_report = self._generate_code_aggregator_report(final_codebase)
            final_codebase["files"]["CODE_AGGREGATOR_REPORT.md"] = aggregator_report
            logger.info("Generated CODE_AGGREGATOR_REPORT.md successfully")
        except Exception as e:
            logger.error(f"Error generating code aggregator report: {str(e)}")
            self.project_state['integration_progress']['errors'].append(f"Code aggregator report error: {str(e)}")

        # Run integration tests
        try:
            test_context = {"codebase": final_codebase}
            test_results = await self._run_integration_tests(test_context)
            logger.info("Integration tests completed")
        except Exception as e:
            logger.error(f"Error running integration tests: {str(e)}")
            self.project_state['integration_progress']['errors'].append(f"Integration tests error: {str(e)}")

        # Log integration summary
        if self.project_state['integration_progress']['errors']:
            logger.warning(f"Integration completed with {len(self.project_state['integration_progress']['errors'])} errors.")
        else:
            logger.info(f"Integration complete. Codebase has {self.project_state['integration_progress']['processed_files']} files.")

        self.project_state['codebase'] = final_codebase
        return final_codebase

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
        """Generates a basic Dockerfile based on the project with performance optimizations."""
        # This is a very basic heuristic. A real implementation would be more robust.
        if "package.json" in solution["files"]: # NodeJS
            return """
# Use an official Node runtime as a parent image
FROM node:18-alpine

# Set the working directory
WORKDIR /usr/src/app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies with caching
RUN npm install --production

# Copy app files
COPY . .

# Expose the port the app runs on
EXPOSE 3000

# Start the app
CMD [ "node", "index.js" ]

# Healthcheck for better Docker management
HEALTHCHECK CMD curl --fail http://localhost:3000 || exit 1
"""
        elif "requirements.txt" in solution["files"]: # Python
            return """
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements file and install dependencies with caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Start the app
CMD [ "python", "main.py" ]

# Healthcheck for better Docker management
HEALTHCHECK CMD curl --fail http://localhost:8000 || exit 1
"""
        else:
            return "# Could not determine project type to generate Dockerfile."

    async def _evolve_solution(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Use an LLM to suggest and apply improvements."""
        logger.info("Generating improvements based on code analysis.")

        # Analyze the current solution for potential improvements
        improvement_report = {
            "code_quality": await self._analyze_code_quality(solution),
            "performance": await self._analyze_performance(solution),
            "security": await self._analyze_security(solution)
        }

        # Generate specific improvement suggestions
        suggestions = []
        if improvement_report["code_quality"]["score"] < 0.9:
            suggestions.append("Refactor code to improve readability and maintainability")
        if improvement_report["performance"]["bottlenecks"]:
            suggestions.extend([f"Optimize {bottleneck}" for bottleneck in improvement_report["performance"]["bottlenecks"]])
        if improvement_report["security"]["vulnerabilities"]:
            suggestions.extend([f"Fix security vulnerability: {vuln}" for vuln in improvement_report["security"]["vulnerabilities"]])

        # Add improvements to the solution
        solution["improvements"] = {
            "report": improvement_report,
            "suggestions": suggestions
        }

        logger.info(f"Generated {len(suggestions)} improvement suggestions")
        return solution

    async def _calculate_quality_score(self, solution: Dict[str, Any]) -> float:
        """Calculate a quality score for the generated solution."""
        # Implement quality metrics calculation
        # This would include code quality, test coverage, performance, security, etc.
        return 0.9  # Placeholder

    def _parse_architecture_response(self, response: str) -> Dict[str, Any]:
        """Parse architecture response when JSON parsing fails"""
        # Implement robust parsing for non-JSON responses
        return {
            "components": {"frontend": {}, "backend": {}, "database": {}},
            "raw_response": response
        }

    def _detect_dependency_cycle(self, tasks: List[AgentTask], pending_tasks: List[str]) -> None:
        """Detect dependency cycles in tasks."""
        # Simple cycle detection - could be enhanced with graph algorithms
        for task in tasks:
            if task.task_id in pending_tasks and any(dep in pending_tasks for dep in task.dependencies):
                logger.warning(f"Potential cycle detected: {task.task_id} depends on {[dep for dep in task.dependencies if dep in pending_tasks]}")

    def _update_task_execution_status(self, task: AgentTask, status: str) -> None:
        """Update the task execution tracker."""
        self.project_state['task_execution'][status] += 1
        self.project_state['task_execution']['pending'] -= 1

    def _validate_file_content(self, file_path: str, content: str) -> bool:
        """Validate file content before integration."""
        # Basic validation - could be enhanced with schema validation
        if not content or len(content) < 10:
            logger.warning(f"Empty or too short content in {file_path}")
            return False

        # Check for common issues
        if file_path.endswith('.py') and not any(line.strip().startswith('def ') or line.strip().startswith('class ')
                                             for line in content.split('\n')):
            logger.warning(f"No functions or classes found in Python file {file_path}")
            return False

        # Check for syntax errors
        if file_path.endswith('.py'):
            try:
                compile(content, file_path, 'exec')
            except SyntaxError as e:
                logger.error(f"Syntax error in {file_path}: {str(e)}")
                return False

        return True

    def _generate_code_aggregator_report(self, codebase: Dict[str, Any]) -> str:
        """Generate a report on the aggregated codebase."""
        # Analyze the codebase structure
        files_by_type = {}
        for file_path in codebase['files']:
            ext = file_path.split('.')[-1]
            files_by_type[ext] = files_by_type.get(ext, 0) + 1

        # Calculate metrics
        total_files = len(codebase['files'])
        avg_file_size = sum(len(content) for content in codebase['files'].values()) // total_files if total_files > 0 else 0

        # Generate report
        report = f"# Code Aggregator Report\n\n"
        report += f"## Overview\n"
        report += f"- Total files: {total_files}\n"
        report += f"- Average file size: {avg_file_size} bytes\n\n"
        report += f"## Files by Type\n"
        for ext, count in files_by_type.items():
            report += f"- {ext}: {count}\n"

        # Add NLP analysis of codebase
        if total_files > 0:
            sample_content = "\n".join(codebase['files'].values())[:1000]  # Take first 1000 chars for analysis
            nlp_analysis = self.nlp_processor.analyze_text(sample_content)
            report += f"\n## NLP Analysis\n"
            report += f"- Key entities: {', '.join([ent[0] for ent in nlp_analysis['entities']])}\n"
            report += f"- Main topics: {', '.join(nlp_analysis['noun_chunks'])[:100]}\n"

        return report

    async def _analyze_code_quality(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code quality using NLP and static analysis."""
        # Simple heuristic-based analysis
        python_files = [content for path, content in solution.get('files', {}).items() if path.endswith('.py')]
        js_files = [content for path, content in solution.get('files', {}).items() if path.endswith('.js')]

        # Count lines of code (LOC)
        total_loc = sum(len(content.split('\n')) for content in python_files + js_files)

        # Check for code complexity
        complex_functions = 0
        for file_content in python_files:
            function_count = sum(1 for line in file_content.split('\n') if line.strip().startswith('def '))
            if function_count > 5:  # Heuristic threshold
                complex_functions += 1

        # Use NLP to analyze code readability
        if python_files:
            sample_code = "\n".join(python_files[:2])  # Take first 2 Python files for analysis
            nlp_analysis = self.nlp_processor.analyze_text(sample_code)

            # Heuristic: More nouns/chunks might indicate better structured code
            readability_score = len(nlp_analysis['noun_chunks']) / max(1, len(nlp_analysis['tokens'])) * 100

            return {
                "score": min(0.9, max(0.5, (total_loc / 1000) * 0.8)) + (readability_score * 0.2),
                "metrics": {
                    "lines_of_code": total_loc,
                    "complex_functions": complex_functions,
                    "readability_score": readability_score
                }
            }

        return {"score": 0.5, "metrics": {"lines_of_code": 0, "complex_functions": 0}}

    async def _analyze_performance(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance characteristics of the codebase."""
        # Simple heuristic-based analysis
        python_files = [content for path, content in solution.get('files', {}).items() if path.endswith('.py')]
        js_files = [content for path, content in solution.get('files', {}).items() if path.endswith('.js')]

        # Check for performance bottlenecks
        potential_bottlenecks = []

        for file_content in python_files:
            if 'for ' in file_content and 'range' in file_content:
                potential_bottlenecks.append("Potential inefficient loop structure")

        for file_content in js_files:
            if 'for (' in file_content and 'var i = 0' in file_content:
                potential_bottlenecks.append("Potential inefficient JS loop")

        # Heuristic performance score
        return {
            "score": max(0.5, min(1.0, 1 - (len(potential_bottlenecks) * 0.1))),
            "bottlenecks": potential_bottlenecks
        }

    async def _analyze_security(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security aspects of the codebase."""
        # Simple heuristic-based analysis
        python_files = [content for path, content in solution.get('files', {}).items() if path.endswith('.py')]
        js_files = [content for path, content in solution.get('files', {}).items() if path.endswith('.js')]

        # Check for common security issues
        vulnerabilities = []

        for file_content in python_files:
            if 'os.system' in file_content and not ('subprocess' in file_content or 'shlex.quote' in file_content):
                vulnerabilities.append("Unsafe command execution")
            if 'pickle.loads' in file_content:
                vulnerabilities.append("Unsafe pickle deserialization")

        for file_content in js_files:
            if 'eval(' in file_content:
                vulnerabilities.append("Use of eval() - potential code injection")
            if 'innerHTML' in file_content and not ('textContent' in file_content):
                vulnerabilities.append("Potential XSS vulnerability with innerHTML")

        # Heuristic security score
        return {
            "score": max(0.5, min(1.0, 1 - (len(vulnerabilities) * 0.2))),
            "vulnerabilities": vulnerabilities
        }

    def _generate_error_report(self, failed_tasks: List[str], results: Dict[str, Any]) -> str:
        """Generate a detailed error report for failed tasks."""
        report = "# Error Report\n\n"
        report += f"## Failed Tasks ({len(failed_tasks)})\n"
        for task_id in failed_tasks:
            if task_id in results and 'error' in results[task_id]:
                report += f"- {task_id}: {results[task_id]['error']}\n"

        # Add suggestions for fixing errors
        report += "\n## Suggestions\n"
        report += "- Check dependencies of failed tasks\n"
        report += "- Verify agent implementations\n"
        report += "- Review error messages for specific issues\n"

        return report

    def _register_default_tests(self):
        """Register default integration tests."""
        self.integration_tests.register_test("frontend_backend", test_frontend_backend_integration)
        self.integration_tests.register_test("database_schema", test_database_schema_integration)

    async def _run_integration_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run all registered integration tests."""
        logger.info("Running integration tests...")
        return await self.integration_tests.run_all_tests(context)

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