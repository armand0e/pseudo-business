"""
Terraform infrastructure manager for the Agentic AI Development Platform.

This module handles the creation and deployment of Terraform scripts for
infrastructure provisioning across different environments.
"""

import logging
import os
import subprocess
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

class TerraformManager:
    """Manages Terraform infrastructure provisioning."""

    def __init__(self):
        """Initialize the Terraform manager."""
        self.config = None
        self.environments = ["dev", "staging", "prod"]
        self.terraform_dir = "devops_agent/devops_agent/terraform/infrastructure"

    def init_config(self, config_path):
        """Initialize configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f).get("terraform", {})
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            self.config = {}

        # Create Terraform directories for each environment
        for env in self.environments:
            env_dir = f"{self.terraform_dir}/{env}"
            os.makedirs(env_dir, exist_ok=True)
            
            # Generate Terraform files for this environment
            self._generate_terraform_files(env)

    def _generate_terraform_files(self, environment):
        """Generate Terraform files for the specified environment."""
        env_dir = f"{self.terraform_dir}/{environment}"
        
        # Generate main.tf
        main_tf = self._generate_main_tf(environment)
        with open(f"{env_dir}/main.tf", "w") as f:
            f.write(main_tf)
        
        # Generate variables.tf
        variables_tf = self._generate_variables_tf(environment)
        with open(f"{env_dir}/variables.tf", "w") as f:
            f.write(variables_tf)
        
        # Generate outputs.tf
        outputs_tf = self._generate_outputs_tf(environment)
        with open(f"{env_dir}/outputs.tf", "w") as f:
            f.write(outputs_tf)
        
        # Generate terraform.tfvars
        tfvars = self._generate_tfvars(environment)
        with open(f"{env_dir}/terraform.tfvars", "w") as f:
            f.write(tfvars)
        
        logger.info(f"Generated Terraform files for {environment} in {env_dir}")

    def _generate_main_tf(self, environment):
        """Generate main.tf file for the specified environment."""
        return f"""# Terraform configuration for {environment} environment
terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }}
  }}
  backend "s3" {{
    bucket = "agentic-ai-terraform-state"
    key    = "agentic-ai/{environment}/terraform.tfstate"
    region = "us-east-1"
  }}
}}

provider "aws" {{
  region = var.aws_region
  default_tags {{
    tags = {{
      Environment = var.environment
      Project     = "agentic-ai"
      ManagedBy   = "terraform"
    }}
  }}
}}

# VPC and Networking
module "vpc" {{
  source = "terraform-aws-modules/vpc/aws"
  
  name = "${{var.project_name}}-${{var.environment}}-vpc"
  cidr = var.vpc_cidr
  
  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  
  enable_nat_gateway = true
  single_nat_gateway = var.environment != "prod"
  
  enable_dns_hostnames = true
  enable_dns_support   = true
}}

# ECS Cluster
resource "aws_ecs_cluster" "main" {{
  name = "${{var.project_name}}-${{var.environment}}-cluster"
  
  setting {{
    name  = "containerInsights"
    value = "enabled"
  }}
}}

# Security Groups
resource "aws_security_group" "alb" {{
  name        = "${{var.project_name}}-${{var.environment}}-alb-sg"
  description = "ALB Security Group"
  vpc_id      = module.vpc.vpc_id
  
  ingress {{
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  ingress {{
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}

resource "aws_security_group" "ecs_tasks" {{
  name        = "${{var.project_name}}-${{var.environment}}-ecs-tasks-sg"
  description = "ECS Tasks Security Group"
  vpc_id      = module.vpc.vpc_id
  
  ingress {{
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.alb.id]
  }}
  
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}

# RDS Database
resource "aws_db_subnet_group" "main" {{
  name       = "${{var.project_name}}-${{var.environment}}-db-subnet-group"
  subnet_ids = module.vpc.private_subnets
}}

resource "aws_security_group" "db" {{
  name        = "${{var.project_name}}-${{var.environment}}-db-sg"
  description = "Database Security Group"
  vpc_id      = module.vpc.vpc_id
  
  ingress {{
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }}
  
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}

resource "aws_db_instance" "main" {{
  identifier             = "${{var.project_name}}-${{var.environment}}"
  engine                 = "postgres"
  engine_version         = "13.7"
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false
  skip_final_snapshot    = var.environment != "prod"
}}

# Load Balancer
resource "aws_lb" "main" {{
  name               = "${{var.project_name}}-${{var.environment}}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
}}

resource "aws_lb_target_group" "api" {{
  name        = "${{var.project_name}}-${{var.environment}}-api-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "ip"
  
  health_check {{
    path                = "/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }}
}}

resource "aws_lb_listener" "http" {{
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"
  
  default_action {{
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }}
}}
"""

    def _generate_variables_tf(self, environment):
        """Generate variables.tf file for the specified environment."""
        return f"""# Variables for {environment} environment

variable "aws_region" {{
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}}

variable "environment" {{
  description = "Environment name"
  type        = string
  default     = "{environment}"
}}

variable "project_name" {{
  description = "Project name"
  type        = string
  default     = "agentic-ai"
}}

variable "vpc_cidr" {{
  description = "CIDR block for the VPC"
  type        = string
}}

variable "availability_zones" {{
  description = "List of availability zones"
  type        = list(string)
}}

variable "private_subnet_cidrs" {{
  description = "CIDR blocks for private subnets"
  type        = list(string)
}}

variable "public_subnet_cidrs" {{
  description = "CIDR blocks for public subnets"
  type        = list(string)
}}

variable "db_instance_class" {{
  description = "RDS instance class"
  type        = string
}}

variable "db_allocated_storage" {{
  description = "Allocated storage for RDS in GB"
  type        = number
}}

variable "db_name" {{
  description = "Database name"
  type        = string
  default     = "agentic_ai"
}}

variable "db_username" {{
  description = "Database username"
  type        = string
  sensitive   = true
}}

variable "db_password" {{
  description = "Database password"
  type        = string
  sensitive   = true
}}
"""

    def _generate_outputs_tf(self, environment):
        """Generate outputs.tf file for the specified environment."""
        return f"""# Outputs for {environment} environment

output "vpc_id" {{
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}}

output "private_subnets" {{
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnets
}}

output "public_subnets" {{
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnets
}}

output "db_instance_endpoint" {{
  description = "The connection endpoint for the RDS instance"
  value       = aws_db_instance.main.endpoint
}}

output "alb_dns_name" {{
  description = "The DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}}
"""

    def _generate_tfvars(self, environment):
        """Generate terraform.tfvars file for the specified environment."""
        # Different values based on environment
        if environment == "dev":
            return """aws_region = "us-east-1"
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]
private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
public_subnet_cidrs = ["10.0.101.0/24", "10.0.102.0/24"]
db_instance_class = "db.t3.small"
db_allocated_storage = 20
db_username = "agentic"
db_password = "Password123!" # Change in a real environment!
"""
        elif environment == "staging":
            return """aws_region = "us-east-1"
vpc_cidr = "10.1.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]
private_subnet_cidrs = ["10.1.1.0/24", "10.1.2.0/24"]
public_subnet_cidrs = ["10.1.101.0/24", "10.1.102.0/24"]
db_instance_class = "db.t3.medium"
db_allocated_storage = 50
db_username = "agentic"
db_password = "Password123!" # Change in a real environment!
"""
        else:  # prod
            return """aws_region = "us-east-1"
vpc_cidr = "10.2.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
private_subnet_cidrs = ["10.2.1.0/24", "10.2.2.0/24", "10.2.3.0/24"]
public_subnet_cidrs = ["10.2.101.0/24", "10.2.102.0/24", "10.2.103.0/24"]
db_instance_class = "db.m5.large"
db_allocated_storage = 100
db_username = "agentic"
db_password = "Password123!" # Change in a real environment!
"""

    def deploy(self, environment="dev", apply=False):
        """Deploy infrastructure using Terraform."""
        if environment not in self.environments:
            logger.error(f"Unknown environment: {environment}")
            return False
            
        env_dir = f"{self.terraform_dir}/{environment}"
        if not os.path.exists(env_dir):
            logger.error(f"Terraform directory not found for {environment}: {env_dir}")
            return False
            
        try:
            # Initialize Terraform
            logger.info(f"Initializing Terraform for {environment}...")
            subprocess.run(
                ["terraform", "init"],
                cwd=env_dir,
                check=True
            )
            
            # Run terraform plan
            logger.info(f"Planning Terraform changes for {environment}...")
            plan_output = subprocess.run(
                ["terraform", "plan", "-out=tfplan"],
                cwd=env_dir,
                check=True,
                capture_output=True,
                text=True
            ).stdout
            
            logger.info(f"Terraform plan for {environment}:\n{plan_output}")
            
            # Apply changes if requested
            if apply:
                logger.info(f"Applying Terraform changes for {environment}...")
                apply_output = subprocess.run(
                    ["terraform", "apply", "tfplan"],
                    cwd=env_dir,
                    check=True,
                    capture_output=True,
                    text=True
                ).stdout
                
                logger.info(f"Terraform apply for {environment} completed:\n{apply_output}")
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Terraform error: {e}")
            return False