#!/usr/bin/env python
"""
Command-line interface for the DevOps Agent.

This CLI provides commands for containerization, infrastructure provisioning,
CI/CD pipeline setup, monitoring configuration, logging setup, and security checks.
"""

import argparse
import logging
import sys
import os

logger = logging.getLogger(__name__)

def setup_logging():
    """Configure logging for the DevOps Agent."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="DevOps Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize DevOps Agent")
    init_parser.add_argument(
        "--config", 
        default="config/devops_config.yaml", 
        help="Path to configuration file"
    )

    # Build command
    build_parser = subparsers.add_parser("build", help="Build containers")
    build_parser.add_argument(
        "--service", 
        help="Specific service to build (default: all)"
    )
    build_parser.add_argument(
        "--tag", 
        default="latest", 
        help="Docker image tag"
    )

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy infrastructure")
    deploy_parser.add_argument(
        "--environment", 
        choices=["dev", "staging", "prod"], 
        default="dev", 
        help="Target environment"
    )
    deploy_parser.add_argument(
        "--apply", 
        action="store_true", 
        help="Apply Terraform changes"
    )

    # Setup monitoring command
    monitor_parser = subparsers.add_parser("setup-monitoring", help="Setup monitoring")
    monitor_parser.add_argument(
        "--environment", 
        choices=["dev", "staging", "prod"], 
        default="dev", 
        help="Target environment"
    )

    # Setup logging command
    logging_parser = subparsers.add_parser("setup-logging", help="Setup logging")
    logging_parser.add_argument(
        "--environment", 
        choices=["dev", "staging", "prod"], 
        default="dev", 
        help="Target environment"
    )

    # Security check command
    security_parser = subparsers.add_parser("security-check", help="Run security checks")
    security_parser.add_argument(
        "--service", 
        help="Specific service to check (default: all)"
    )

    return parser.parse_args()

def main():
    """Main entry point for the CLI."""
    setup_logging()
    logger.info("DevOps Agent starting...")
    args = parse_args()

    if not args.command:
        logger.error("No command specified")
        sys.exit(1)

    try:
        if args.command == "init":
            logger.info("Initializing DevOps Agent...")
            # Import managers here to avoid circular imports
            from devops_agent.containerization.docker_manager import DockerManager
            from devops_agent.terraform.terraform_manager import TerraformManager
            from devops_agent.ci_cd.pipeline_manager import PipelineManager
            from devops_agent.monitoring.prometheus_manager import PrometheusManager
            from devops_agent.logging.elk_manager import ELKManager
            from devops_agent.security.security_manager import SecurityManager
            
            # Initialize configurations
            if not os.path.exists(args.config):
                logger.warning(f"Config file {args.config} not found, using default config")
                args.config = os.path.join(os.path.dirname(__file__), "default_config.yaml")
            
            docker_manager = DockerManager()
            docker_manager.init_config(args.config)
            
            terraform_manager = TerraformManager()
            terraform_manager.init_config(args.config)
            
            pipeline_manager = PipelineManager()
            pipeline_manager.init_config(args.config)
            
            prometheus_manager = PrometheusManager()
            prometheus_manager.init_config(args.config)
            
            elk_manager = ELKManager()
            elk_manager.init_config(args.config)
            
            security_manager = SecurityManager()
            security_manager.init_config(args.config)
            
            logger.info("DevOps Agent initialized successfully")
            
        elif args.command == "build":
            from devops_agent.containerization.docker_manager import DockerManager
            logger.info(f"Building containers{f' for {args.service}' if args.service else ''}...")
            docker_manager = DockerManager()
            docker_manager.build_containers(service=args.service, tag=args.tag)
            
        elif args.command == "deploy":
            from devops_agent.terraform.terraform_manager import TerraformManager
            logger.info(f"Deploying infrastructure to {args.environment}...")
            terraform_manager = TerraformManager()
            terraform_manager.deploy(environment=args.environment, apply=args.apply)
            
        elif args.command == "setup-monitoring":
            from devops_agent.monitoring.prometheus_manager import PrometheusManager
            logger.info(f"Setting up monitoring for {args.environment}...")
            prometheus_manager = PrometheusManager()
            prometheus_manager.setup(environment=args.environment)
            
        elif args.command == "setup-logging":
            from devops_agent.logging.logging_manager import LoggingManager
            logger.info(f"Setting up logging for {args.environment}...")
            logging_manager = LoggingManager()
            logging_manager.init_config()
            
        elif args.command == "security-check":
            from devops_agent.security.security_manager import SecurityManager
            logger.info(f"Running security checks{f' for {args.service}' if args.service else ''}...")
            security_manager = SecurityManager()
            security_manager.run_checks(service=args.service)
            
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()