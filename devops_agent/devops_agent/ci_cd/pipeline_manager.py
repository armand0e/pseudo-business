"""
CI/CD pipeline manager for the Agentic AI Development Platform.

This module handles the creation and management of CI/CD pipeline templates
for GitHub Actions, facilitating automated building, testing, and deployment.
"""

import logging
import os
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

class PipelineManager:
    """Manages CI/CD pipeline configuration for the platform."""

    def __init__(self):
        """Initialize the pipeline manager."""
        self.config = None
        self.services = [
            "master_orchestrator",
            "backend_agent",
            "frontend_agent",
            "database_agent",
            "testing_agent",
            "api_gateway",
            "user_interface",
            "cli_tool",
            "evolution_engine",
        ]
        self.ci_cd_dir = "devops_agent/devops_agent/ci_cd/github_actions"

    def init_config(self, config_path):
        """Initialize configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f).get("ci_cd", {})
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            self.config = {}

        # Create CI/CD directory if it doesn't exist
        os.makedirs(self.ci_cd_dir, exist_ok=True)
        
        # Generate pipeline files
        self._generate_main_workflow()
        self._generate_service_workflows()

    def _generate_main_workflow(self):
        """Generate the main CI/CD workflow."""
        workflow_content = """name: Main CI/CD Pipeline

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  lint:
    name: Lint Code
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install black flake8 isort
          
      - name: Lint with flake8
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        
      - name: Check formatting with black
        run: black --check .
        
      - name: Check imports with isort
        run: isort --check-only --profile black .

  test:
    name: Run Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov
          pip install -r requirements.txt
          
      - name: Run tests with pytest
        run: pytest --cov=./ --cov-report=xml
        
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  build:
    name: Build and Push Docker Images
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master')
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
        
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}
          
      - name: Build and push Master Orchestrator
        uses: docker/build-push-action@v4
        with:
          context: .
          file: devops_agent/devops_agent/containerization/dockerfiles/Dockerfile.master_orchestrator
          push: true
          tags: agentic-ai/master-orchestrator:latest
          
      # Additional build steps for other services would be included here
      
  deploy-dev:
    name: Deploy to Development
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master')
    environment: development
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
          
      - name: Set up Terraform
        uses: hashicorp/setup-terraform@v2
        
      - name: Terraform Init
        run: |
          cd devops_agent/devops_agent/terraform/infrastructure/dev
          terraform init
          
      - name: Terraform Apply
        run: |
          cd devops_agent/devops_agent/terraform/infrastructure/dev
          terraform apply -auto-approve"""
        
        # Write the workflow file
        output_path = f"{self.ci_cd_dir}/main_workflow.yml"
        with open(output_path, "w") as f:
            f.write(workflow_content)
        
        logger.info(f"Generated main CI/CD workflow at {output_path}")

    def _generate_service_workflows(self):
        """Generate service-specific CI/CD workflows."""
        for service in self.services:
            # Determine language based on service
            if service in ["frontend_agent", "user_interface", "api_gateway"]:
                language = "node"
            else:
                language = "python"
                
            workflow_content = self._get_service_workflow_template(service, language)
            
            # Write the workflow file
            output_path = f"{self.ci_cd_dir}/{service}_workflow.yml"
            with open(output_path, "w") as f:
                f.write(workflow_content)
            
            logger.info(f"Generated CI/CD workflow for {service} at {output_path}")

    def _get_service_workflow_template(self, service, language):
        """Get the workflow template for a specific service and language."""
        service_name = service.replace("_", "-")
        
        if language == "python":
            return f"""name: {service_name} CI/CD

on:
  push:
    branches: [ main, master ]
    paths:
      - '{service}/**'
      - '.github/workflows/{service_name}_workflow.yml'
  pull_request:
    branches: [ main, master ]
    paths:
      - '{service}/**'

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install black flake8 isort
          if [ -f {service}/requirements.txt ]; then
            pip install -r {service}/requirements.txt
          fi
          
      - name: Lint with flake8
        run: flake8 {service} --count --select=E9,F63,F7,F82 --show-source --statistics
        
      - name: Check formatting with black
        run: black --check {service}
        
      - name: Check imports with isort
        run: isort --check-only --profile black {service}

  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov
          if [ -f {service}/requirements.txt ]; then
            pip install -r {service}/requirements.txt
          fi
          
      - name: Run tests with pytest
        run: |
          cd {service}
          pytest --cov=./ --cov-report=xml
        
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./{service}/coverage.xml

  build:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master')
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
        
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}
          
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          file: devops_agent/devops_agent/containerization/dockerfiles/Dockerfile.{service}
          push: true
          tags: agentic-ai/{service_name}:latest,${{ github.sha }}"""
        else:  # Node.js
            return f"""name: {service_name} CI/CD

on:
  push:
    branches: [ main, master ]
    paths:
      - '{service}/**'
      - '.github/workflows/{service_name}_workflow.yml'
  pull_request:
    branches: [ main, master ]
    paths:
      - '{service}/**'

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: '{service}/package-lock.json'
          
      - name: Install dependencies
        run: |
          cd {service}
          npm install
          
      - name: Lint
        run: |
          cd {service}
          npm run lint

  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: '{service}/package-lock.json'
          
      - name: Install dependencies
        run: |
          cd {service}
          npm install
          
      - name: Test
        run: |
          cd {service}
          npm test
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          directory: ./{service}/coverage

  build:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master')
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
        
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}
          
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          file: devops_agent/devops_agent/containerization/dockerfiles/Dockerfile.{service}
          push: true
          tags: agentic-ai/{service_name}:latest,${{ github.sha }}"""

    def create_workflow_files(self, output_dir=".github/workflows"):
        """Create workflow files in the GitHub Actions directory."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Copy main workflow
        main_workflow_path = f"{self.ci_cd_dir}/main_workflow.yml"
        if os.path.exists(main_workflow_path):
            with open(main_workflow_path, "r") as src:
                with open(f"{output_dir}/main.yml", "w") as dst:
                    dst.write(src.read())
            logger.info(f"Created main workflow file at {output_dir}/main.yml")
        
        # Copy service workflows
        for service in self.services:
            service_workflow_path = f"{self.ci_cd_dir}/{service}_workflow.yml"
            if os.path.exists(service_workflow_path):
                service_name = service.replace("_", "-")
                with open(service_workflow_path, "r") as src:
                    with open(f"{output_dir}/{service_name}.yml", "w") as dst:
                        dst.write(src.read())
                logger.info(f"Created workflow file for {service} at {output_dir}/{service_name}.yml")