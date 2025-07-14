"""
Docker containerization manager for the Agentic AI Development Platform.

This module handles the creation of Dockerfiles and building of Docker images
for all services in the platform.
"""

import logging
import os
import subprocess
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

class DockerManager:
    """Manages Docker containerization for all services."""

    def __init__(self):
        """Initialize the Docker manager."""
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
        self.dockerfile_templates = {
            "master_orchestrator": "python",
            "backend_agent": "python",
            "database_agent": "python",
            "testing_agent": "python",
            "evolution_engine": "python",
            "cli_tool": "python",
            "frontend_agent": "node",
            "user_interface": "node",
            "api_gateway": "node",
        }

    def init_config(self, config_path):
        """Initialize configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f).get("containerization", {})
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            self.config = {}

        # Create dockerfile directory if it doesn't exist
        os.makedirs("devops_agent/devops_agent/containerization/dockerfiles", exist_ok=True)
        
        # Generate Dockerfiles for all services
        for service in self.services:
            self._generate_dockerfile(service)

    def _generate_dockerfile(self, service):
        """Generate a Dockerfile for the specified service."""
        template_type = self.dockerfile_templates.get(service, "python")
        output_path = f"devops_agent/devops_agent/containerization/dockerfiles/Dockerfile.{service}"
        
        if template_type == "python":
            dockerfile_content = self._generate_python_dockerfile(service)
        elif template_type == "node":
            dockerfile_content = self._generate_node_dockerfile(service)
        else:
            logger.warning(f"Unknown template type {template_type} for service {service}")
            return
        
        with open(output_path, "w") as f:
            f.write(dockerfile_content)
        
        logger.info(f"Generated Dockerfile for {service} at {output_path}")

    def _generate_python_dockerfile(self, service):
        """Generate a Python-based Dockerfile."""
        return f"""# Dockerfile for {service}
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY {service}/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY {service}/ .

# Run the application
CMD ["python", "-m", "{service.replace('_', '.')}"]
"""

    def _generate_node_dockerfile(self, service):
        """Generate a Node.js-based Dockerfile."""
        return f"""# Dockerfile for {service}
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY {service}/package*.json ./
RUN npm install

# Copy application code
COPY {service}/ .

# Build the application (for frontend)
RUN npm run build

# Run the application
CMD ["npm", "start"]
"""

    def build_containers(self, service=None, tag="latest"):
        """Build Docker containers for all or a specific service."""
        services_to_build = [service] if service else self.services
        
        for svc in services_to_build:
            if svc not in self.services:
                logger.warning(f"Unknown service: {svc}")
                continue
                
            dockerfile_path = f"devops_agent/devops_agent/containerization/dockerfiles/Dockerfile.{svc}"
            if not os.path.exists(dockerfile_path):
                logger.warning(f"Dockerfile not found for {svc} at {dockerfile_path}")
                continue
                
            image_name = f"agentic-ai/{svc}:{tag}"
            
            try:
                logger.info(f"Building Docker image for {svc}...")
                subprocess.run(
                    ["docker", "build", "-t", image_name, "-f", dockerfile_path, "."],
                    check=True
                )
                logger.info(f"Successfully built Docker image: {image_name}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to build Docker image for {svc}: {e}")

    def generate_docker_compose(self, environment="dev"):
        """Generate a Docker Compose file for the specified environment."""
        compose_file = {
            "version": "3.8",
            "services": {}
        }
        
        # Add each service to the compose file
        for service in self.services:
            compose_file["services"][service.replace("_", "-")] = {
                "image": f"agentic-ai/{service}:latest",
                "restart": "unless-stopped",
                "environment": self._get_environment_vars(service, environment),
                "networks": ["agentic-network"],
            }
        
        # Add database
        compose_file["services"]["postgres"] = {
            "image": "postgres:13",
            "restart": "unless-stopped",
            "environment": {
                "POSTGRES_PASSWORD": "postgres",
                "POSTGRES_USER": "postgres",
                "POSTGRES_DB": "agentic_ai",
            },
            "volumes": ["postgres-data:/var/lib/postgresql/data"],
            "networks": ["agentic-network"],
        }
        
        # Add Redis for caching
        compose_file["services"]["redis"] = {
            "image": "redis:6",
            "restart": "unless-stopped",
            "networks": ["agentic-network"],
        }
        
        # Define networks and volumes
        compose_file["networks"] = {
            "agentic-network": {"driver": "bridge"}
        }
        compose_file["volumes"] = {
            "postgres-data": {"driver": "local"}
        }
        
        # Write docker-compose.yml
        output_path = f"devops_agent/devops_agent/containerization/docker-compose.{environment}.yml"
        with open(output_path, "w") as f:
            yaml.dump(compose_file, f, default_flow_style=False)
        
        logger.info(f"Generated Docker Compose file for {environment} at {output_path}")
        return output_path

    def _get_environment_vars(self, service, environment):
        """Get environment variables for a service based on environment."""
        common_vars = {
            "ENVIRONMENT": environment,
            "LOG_LEVEL": "info" if environment == "prod" else "debug",
        }
        
        # Service-specific environment variables
        service_vars = {}
        if service == "backend_agent":
            service_vars = {
                "DATABASE_URL": "postgresql://postgres:postgres@postgres:5432/agentic_ai",
                "REDIS_URL": "redis://redis:6379/0",
            }
        elif service == "api_gateway":
            service_vars = {
                "PORT": "3000",
                "BACKEND_URL": "http://backend-agent:8000",
            }
        elif service == "frontend_agent" or service == "user_interface":
            service_vars = {
                "API_URL": "http://api-gateway:3000",
            }
        
        # Merge common and service-specific vars
        return {**common_vars, **service_vars}