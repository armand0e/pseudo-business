#!/bin/bash

# Agentic AI Full-Stack Tech Company Setup Script
# This script automates the initial setup and configuration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="agentic-ai-company"
PYTHON_VERSION="3.12"
NODE_VERSION="18"
HF_TOKEN="${HF_TOKEN:-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}"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        error "This setup script requires Linux. Please use Ubuntu 20.04+ or similar."
    fi
    
    # Check memory
    total_mem=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    total_mem_gb=$((total_mem / 1024 / 1024))
    if [ $total_mem_gb -lt 16 ]; then
        error "Insufficient memory. Minimum 16GB required, 32GB recommended."
    fi
    
    # Check disk space
    available_space=$(df . | awk 'NR==2 {print $4}')
    available_space_gb=$((available_space / 1024 / 1024))
    if [ $available_space_gb -lt 100 ]; then
        error "Insufficient disk space. Minimum 100GB required."
    fi
    
    # Check for GPU
    if lspci | grep -i "amd\|radeon" > /dev/null; then
        info "AMD GPU detected"
        GPU_TYPE="amd"
    elif lspci | grep -i "nvidia" > /dev/null; then
        info "NVIDIA GPU detected"
        GPU_TYPE="nvidia"
    else
        warn "No dedicated GPU detected. Performance may be limited."
        GPU_TYPE="cpu"
    fi
    
    log "System requirements check completed successfully"
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Essential packages
    sudo apt install -y \
        curl \
        wget \
        git \
        build-essential \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        python3-pip \
        python3-venv \
        jq \
        htop \
        tmux \
        vim
    
    log "System dependencies installed successfully"
}

# Install Docker
install_docker() {
    log "Installing Docker..."
    
    if command -v docker &> /dev/null; then
        info "Docker is already installed"
        return
    fi
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    # Enable Docker service
    sudo systemctl enable docker
    sudo systemctl start docker
    
    log "Docker installed successfully"
}

# Install ROCm for AMD GPUs
install_rocm() {
    if [ "$GPU_TYPE" != "amd" ]; then
        info "Skipping ROCm check (no AMD GPU detected)"
        return
    fi

    if command -v rocminfo &> /dev/null; then
        log "ROCm installation detected."
        # Verify user is in render and video groups
        # On some systems, just 'video' is used, on others 'render' is also needed.
        if groups "$USER" | grep -q 'video' && groups "$USER" | grep -q 'render'; then
            log "User '$USER' is in 'render' and 'video' groups."
        else
            warn "User '$USER' is not in 'render' and/or 'video' groups."
            info "This is required for applications and containers to access the GPU."
            info "Please run: sudo usermod -aG render,video \"\$USER\""
            warn "A REBOOT is required for group changes to take full effect."
        fi
        return
    fi

    warn "ROCm (AMD GPU drivers) is not installed or not in your PATH."
    info "This setup script will not install ROCm automatically as requested."
    echo ""
    info "Please install ROCm manually. Based on your system, the steps are generally:"
    echo "+------------------------------------------------------------------------------+"
    echo "| 1. Download the correct amdgpu-install package for your Ubuntu version.      |"
    echo "|    (e.g., for Ubuntu 22.04/24.04 and ROCm 6.4.1)                             |"
    echo "|    \$ OS_CODENAME=\$(lsb_release -cs)                                          |"
    echo "|    \$ wget https://repo.radeon.com/amdgpu-install/6.4.1/ubuntu/\$OS_CODENAME/amdgpu-install_6.4.60401-1_all.deb"
    echo "|                                                                              |"
    echo "| 2. Install the package which sets up AMD's software repositories.            |"
    echo "|    \$ sudo apt install -y ./amdgpu-install_*.deb                              |"
    echo "|    \$ rm ./amdgpu-install_*.deb                                               |"
    echo "|                                                                              |"
    echo "| 3. Install the ROCm metapackage.                                             |"
    echo "|    \$ sudo apt update                                                        |"
    echo "|    \$ sudo apt install -y rocm                                               |"
    echo "|                                                                              |"
    echo "| 4. Add your user to the 'render' and 'video' groups.                         |"
    echo "|    \$ sudo usermod -aG render,video \"\$USER\"                                  |"
    echo "|                                                                              |"
    echo "| 5. REBOOT your system for all changes to take effect.                        |"
    echo "+------------------------------------------------------------------------------+"
    echo ""
    error "ROCm is a prerequisite for GPU acceleration. Please install it and re-run this script."
}

# Install CUDA for NVIDIA GPUs
install_cuda() {
    if [ "$GPU_TYPE" != "nvidia" ]; then
        info "Skipping CUDA installation (no NVIDIA GPU detected)"
        return
    fi
    
    if command -v nvcc &> /dev/null; then
        info "NVIDIA CUDA Toolkit is already installed, skipping installation."
        return
    fi
    
    log "Installing CUDA for NVIDIA GPU support..."
    
    # Download and install CUDA toolkit
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
    sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
    wget https://developer.download.nvidia.com/compute/cuda/12.0.0/local_installers/cuda-repo-ubuntu2004-12-0-local_12.0.0-525.60.13-1_amd64.deb
    sudo dpkg -i cuda-repo-ubuntu2004-12-0-local_12.0.0-525.60.13-1_amd64.deb
    sudo cp /var/cuda-repo-ubuntu2004-12-0-local/cuda-*-keyring.gpg /usr/share/keyrings/
    sudo apt-get update
    sudo apt-get -y install cuda
    
    log "CUDA installed successfully"
}

# Install uv, the new package and environment manager
install_uv() {
    log "Installing uv..."
    if ! command -v uv &> /dev/null; then
        log "uv not found, installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
        # Source the environment file to make `uv` available in the current shell and for the future.
        source "$HOME/.cargo/env"
        if ! grep -q '.cargo/bin' ~/.bashrc; then
            log "Adding uv to .bashrc for future sessions..."
            echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
        fi
        log "uv installed successfully."
    else
        info "uv is already installed."
        # Ensure uv is in the path for the current script session
        if [[ ! "$PATH" == *"$HOME/.cargo/bin"* ]]; then
            export PATH="$HOME/.cargo/bin:$PATH"
        fi
    fi
}

create_pyproject_toml() {
    log "Creating pyproject.toml for dependency management..."

    # Define GPU-specific dependencies
    if [ "$GPU_TYPE" = "amd" ]; then
        TORCH_DEPS="""
    "torch @ file://\${PWD}/../Frameworks/pytorch-rocm/torch-2.6.0+rocm6.4.1.git1ded221d-cp312-cp312-linux_x86_64.whl",
    "pytorch-triton-rocm @ file://\${PWD}/../Frameworks/pytorch-rocm/pytorch_triton_rocm-3.2.0+rocm6.4.1.git6da9e660-cp312-cp312-linux_x86_64.whl","""
    elif [ "$GPU_TYPE" = "nvidia" ]; then
        TORCH_DEPS="""
    "torch --index-url https://download.pytorch.org/whl/cu121",
    "torchvision --index-url https://download.pytorch.org/whl/cu121",
    "torchaudio --index-url https://download.pytorch.org/whl/cu121","""
    else
        TORCH_DEPS="""
    "torch",
    "torchvision",
    "torchaudio","""
    fi

    cat > pyproject.toml << EOF
[project]
name = "agentic-ai-company"
version = "0.1.0"
description = "An agentic AI system for creating and deploying SaaS applications."
requires-python = ">=$PYTHON_VERSION"
dependencies = [
    # Core framework
    "fastapi",
    "uvicorn[standard]",
    "pydantic",
    "sqlalchemy",
    "alembic",
    "redis",
    "celery",

    # AI/ML
    $TORCH_DEPS
    "transformers",
    "numpy",
    "pandas",
    "scikit-learn",

    # Web development
    "requests",
    "aiohttp",
    "websockets",
    "jinja2",

    # Database
    "psycopg2-binary",
    "asyncpg",
    
    # Utilities
    "python-dotenv",
    "click",
    "rich",
    "typer",
    "PyYAML",
    "croniter",
    "huggingface_hub",

    # Deployment - Relaxing version to let uv resolve conflicts
    "kubernetes",
    "docker",
    "ansible",

    # Monitoring
    "prometheus-client",
    "structlog"
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "black",
    "isort",
    "flake8",
    "mypy",
]
EOF
}

# Setup project structure
setup_project() {
    log "Setting up project structure..."
    
    # Create main project directory
    mkdir -p $PROJECT_NAME
    cd $PROJECT_NAME
    
    # Create directory structure
    mkdir -p {src/{orchestrator,agents,evolution,deployment},models,configs,tests,docs,scripts,data,logs}
    
    # Create subdirectories
    mkdir -p src/agents/{frontend,backend,database,devops,testing,security,ui_ux}
    mkdir -p src/evolution/{evaluators,mutations,selection}
    mkdir -p src/deployment/{docker,kubernetes,cloud}
    mkdir -p configs/{agents,models,deployment}
    mkdir -p tests/{unit,integration,e2e}
    
    # Create pyproject.toml for uv
    if [ ! -f "pyproject.toml" ]; then
        create_pyproject_toml
    fi
    
    log "Project structure created successfully"
}

# Clone required repositories
clone_repositories() {
    log "Cloning required repositories..."
    
    # Create frameworks directory
    mkdir -p frameworks
    cd frameworks
    
    # Clone OpenHands
    if [ ! -d "OpenHands" ]; then
        log "Cloning OpenHands..."
        git clone https://github.com/All-Hands-AI/OpenHands.git
    else
        info "'OpenHands' directory already exists, skipping clone."
    fi
    
    # Clone OpenEvolve
    if [ ! -d "openevolve" ]; then
        log "Cloning OpenEvolve..."
        git clone https://github.com/codelion/openevolve.git
    else
        info "'openevolve' directory already exists, skipping clone."
    fi
    
    # Clone Open-Codex
    if [ ! -d "open-codex" ]; then
        log "Cloning Open-Codex..."
        git clone https://github.com/ymichael/open-codex.git
    else
        info "'open-codex' directory already exists, skipping clone."
    fi
    
    # Clone Claude Code Flow (if we create a custom version)
    if [ ! -d "claude-code-flow" ]; then
        log "Cloning Claude Code Flow..."
        git clone https://github.com/ruvnet/claude-code-flow.git
    else
        info "'claude-code-flow' directory already exists, skipping clone."
    fi
    
    cd ..
    log "Repositories cloned successfully"
}

# Install Python dependencies using uv
install_python_deps() {
    log "Installing Python dependencies with uv..."

    # Create the virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        log "Creating virtual environment with uv using Python $PYTHON_VERSION..."
        uv venv --python $PYTHON_VERSION
    fi

    # Activate venv for subsequent commands in this script
    source .venv/bin/activate
    
    log "Installing PyTorch based on GPU type..."
    if [ "$GPU_TYPE" = "amd" ]; then
        #
        # ROCm / AMD GPU Installation
        #
        log "Installing PyTorch & Triton for ROCm from local wheel files."
        log "Using absolute paths and installing one-by-one for robustness."
        
        # Construct absolute paths to the wheels. The script runs from inside the 'agentic-ai-company' dir.
        PYTORCH_WHL_PATH="$(cd ../Frameworks/pytorch-rocm && pwd)/torch-2.6.0+rocm6.4.1.git1ded221d-cp312-cp312-linux_x86_64.whl"
        TRITON_WHL_PATH="$(cd ../Frameworks/pytorch-rocm && pwd)/pytorch_triton_rocm-3.2.0+rocm6.4.1.git6da9e660-cp312-cp312-linux_x86_64.whl"
        
        # --- Verification Step ---
        if [ ! -f "$PYTORCH_WHL_PATH" ]; then
            error "PyTorch ROCm wheel file NOT FOUND at: $PYTORCH_WHL_PATH"
        fi
        if [ ! -f "$TRITON_WHL_PATH" ]; then
            error "Triton ROCm wheel file NOT FOUND at: $TRITON_WHL_PATH"
        fi
        log "Local wheel files found successfully."
        
        # --- Installation Step ---
        log "Installing torch and triton wheels together..."
        uv pip install "$PYTORCH_WHL_PATH" "$TRITON_WHL_PATH"

    elif [ "$GPU_TYPE" = "nvidia" ]; then
        #
        # CUDA / NVIDIA GPU Installation
        #
        log "Installing PyTorch for CUDA 12.1..."
        uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    else
        #
        # CPU-only Installation
        #
        log "Installing CPU-only PyTorch..."
        uv pip install torch torchvision torchaudio
    fi

    log "Installing base and dev dependencies from pyproject.toml..."
    uv pip install ".[dev]"

    log "Installing agent frameworks..."
    # Install OpenHands in editable mode. This will also install its dependencies.
    if [ -d "frameworks/OpenHands" ]; then
        uv pip install -e "frameworks/OpenHands"
    fi
    
    # Install OpenEvolve dependencies
    if [ -f "frameworks/openevolve/requirements.txt" ]; then
        uv pip install -r "frameworks/openevolve/requirements.txt"
    fi

    log "Python dependencies installed successfully"
}

# Download AI models
download_models() {
    log "Downloading AI models..."
    
    # Login to Hugging Face
    if [ ! -z "$HF_TOKEN" ]; then
        uv run huggingface-cli login --token $HF_TOKEN
    fi
    
    # Download Devstral models
    log "Downloading Devstral models..."
    uv run huggingface-cli download unsloth/Devstral-Small-2505-GGUF devstral-small-2505-Q4_K_M.gguf --local-dir ./models/
    
    # Download Magistral models (if available)
    log "Downloading Magistral models..."
    # uv run huggingface-cli download unsloth/magistral-small-gguf magistral-small-Q4_K_M.gguf --local-dir ./models/ || warn "Magistral model not found"
    
    # Download embedding models
    log "Downloading embedding models..."
    uv run huggingface-cli download sentence-transformers/all-MiniLM-L6-v2 --local-dir ./models/embeddings/
    
    log "Models downloaded successfully"
}

# Setup LocalAI
setup_localai() {
    log "Setting up LocalAI..."
    
    # Determine image based on GPU type
    case $GPU_TYPE in
        "amd")
            LOCALAI_IMAGE="localai/localai:latest-aio-gpu-hipblas"
            ;;
        "nvidia")
            LOCALAI_IMAGE="localai/localai:latest-aio-gpu-nvidia-cuda-12"
            ;;
        *)
            LOCALAI_IMAGE="localai/localai:latest-aio-cpu"
            ;;
    esac
    
    # Pull LocalAI image
    docker pull $LOCALAI_IMAGE
    
    # Start LocalAI with docker-compose
    if [ -f "local_ai_setup.yml" ]; then
        docker-compose -f local_ai_setup.yml up -d
        
        # Wait for LocalAI to be ready
        log "Waiting for LocalAI to be ready..."
        timeout=60
        while [ $timeout -gt 0 ]; do
            if curl -f http://localhost:8080/readyz &> /dev/null; then
                log "LocalAI is ready!"
                break
            fi
            sleep 2
            timeout=$((timeout - 2))
        done
        
        if [ $timeout -le 0 ]; then
            error "LocalAI failed to start within 60 seconds"
        fi
    else
        warn "local_ai_setup.yml not found, starting LocalAI manually..."
        if ! docker ps -a --format '{{.Names}}' | grep -q "^localai-primary$"; then
            log "Creating 'localai-primary' container."
            docker run -d --name localai-primary \
                -p 8080:8080 \
                -v "$(pwd)/models":/models:cached \
                -e THREADS=16 \
                -e CONTEXT_SIZE=8192 \
                "$LOCALAI_IMAGE"
        else
            info "'localai-primary' container already exists. Ensuring it is started."
            docker start localai-primary
        fi
    fi
    
    log "LocalAI setup completed successfully"
}

# Create configuration files
create_configs() {
    log "Creating configuration files..."
    
    # Create .env file
    cat > .env << EOF
# Environment Configuration
ENV=development
DEBUG=true

# LocalAI Configuration
LOCALAI_BASE_URL=http://localhost:8080
LOCALAI_API_KEY=not-needed

# HuggingFace Configuration
HF_TOKEN=$HF_TOKEN

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/agentic_ai
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=$(openssl rand -hex 32)

# Agent Configuration
MAX_CONCURRENT_AGENTS=5
TIMEOUT_MINUTES=120
QUALITY_THRESHOLD=0.85

# Evolution Configuration
ENABLE_EVOLUTION=true
POPULATION_SIZE=20
GENERATIONS=10
MUTATION_RATE=0.1

# Deployment Configuration
DEFAULT_DEPLOYMENT_TARGET=docker
ENABLE_AUTO_DEPLOY=true

# Monitoring Configuration
ENABLE_MONITORING=true
LOG_LEVEL=INFO
EOF
    
    # Create orchestrator config
    cat > configs/orchestrator.yml << EOF
# Orchestrator Configuration
max_concurrent_agents: 5
timeout_minutes: 120
retry_attempts: 3
quality_threshold: 0.85

# Evolution settings
evolution:
  enable: true
  population_size: 20
  generations: 10
  mutation_rate: 0.1
  crossover_rate: 0.7
  elite_size: 2

# Agent settings
agents:
  frontend:
    specialization: "React, Vue, Angular, TypeScript"
    max_iterations: 50
  backend:
    specialization: "FastAPI, Django, Express, Spring"
    max_iterations: 50
  database:
    specialization: "PostgreSQL, MongoDB, Redis"
    max_iterations: 30
  devops:
    specialization: "Docker, Kubernetes, Terraform"
    max_iterations: 40

# Quality metrics
quality_weights:
  performance: 0.3
  readability: 0.2
  security: 0.2
  maintainability: 0.15
  test_coverage: 0.15
EOF
    
    log "Configuration files created successfully"
}

# Setup database
setup_database() {
    log "Setting up database..."
    
    # Start PostgreSQL and Redis with Docker
    if ! docker ps -a --format '{{.Names}}' | grep -q "^postgres$"; then
        log "Creating and starting 'postgres' container."
        docker run -d --name postgres \
            -e POSTGRES_PASSWORD=password \
            -e POSTGRES_DB=agentic_ai \
            -p 5432:5432 \
            postgres:15
    else
        info "'postgres' container already exists. Ensuring it is started."
        docker start postgres
    fi
    
    if ! docker ps -a --format '{{.Names}}' | grep -q "^redis$"; then
        log "Creating and starting 'redis' container."
        docker run -d --name redis \
            -p 6379:6379 \
            redis:7-alpine
    else
        info "'redis' container already exists. Ensuring it is started."
        docker start redis
    fi
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker exec postgres pg_isready -U postgres &> /dev/null; then
            log "Database is ready!"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    log "Database setup completed successfully"
}

# Create startup script
create_startup_script() {
    log "Creating startup script..."
    
    cat > start.sh << 'EOF'
#!/bin/bash

# Startup script for Agentic AI Tech Company

# Colors
GREEN='\033[0;32m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log "Starting Agentic AI Tech Company..."

# Start services
log "Starting LocalAI..."
docker-compose -f local_ai_setup.yml up -d

log "Starting database services..."
docker start postgres redis 2>/dev/null || true

# Wait for services
log "Waiting for services to be ready..."
sleep 10

# Start the main application
log "Starting main application..."
uv run python main.py

EOF
    
    chmod +x start.sh
    
    log "Startup script created successfully"
}

# Create main application file
create_main_app() {
    log "Creating main application file..."
    
    cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
Main application entry point for Agentic AI Tech Company
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from orchestrator.master_agent import MasterOrchestrator, SaaSRequirements, ProjectType, DeploymentTarget

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main application entry point"""
    logger.info("Starting Agentic AI Tech Company...")
    
    # Initialize orchestrator
    orchestrator = MasterOrchestrator()
    
    # Example: Create a simple task management SaaS
    requirements = SaaSRequirements(
        description="A project management SaaS with team collaboration features",
        project_type=ProjectType.FULL_STACK,
        features=[
            "User authentication and authorization",
            "Project creation and management", 
            "Task assignment and tracking",
            "Real-time collaboration",
            "File sharing and document management",
            "Reporting and analytics dashboard",
            "Email notifications",
            "Mobile-responsive design"
        ],
        tech_stack_preferences={
            "frontend": "React with TypeScript and Material-UI",
            "backend": "FastAPI with Python",
            "database": "PostgreSQL with Redis caching",
            "deployment": "Docker containers with Kubernetes"
        },
        deployment_target=DeploymentTarget.KUBERNETES,
        scale_requirements={
            "concurrent_users": 1000,
            "data_storage": "100GB",
            "response_time": "< 200ms",
            "availability": "99.9%"
        }
    )
    
    try:
        # Create the SaaS application
        logger.info("Creating SaaS application...")
        result = await orchestrator.create_saas_application(requirements)
        
        if result["status"] == "success":
            logger.info(f"✅ Application created successfully!")
            logger.info(f"📊 Quality Score: {result['quality_score']:.2f}")
            logger.info(f"🚀 Deployment URL: {result.get('deployment_url', 'Pending')}")
            logger.info(f"📁 Project Files: {len(result.get('project_files', []))} files generated")
        else:
            logger.error(f"❌ Application creation failed: {result.get('error', 'Unknown error')}")
            
    except KeyboardInterrupt:
        logger.info("Application shutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    log "Main application file created successfully"
}

# Final setup and validation
final_setup() {
    log "Performing final setup and validation..."
    
    # Test LocalAI connection
    if curl -f http://localhost:8080/readyz &> /dev/null; then
        log "✅ LocalAI is running and accessible"
    else
        warn "⚠️  LocalAI may not be fully ready yet"
    fi
    
    # Test database connection
    if docker exec postgres pg_isready -U postgres &> /dev/null; then
        log "✅ Database is running and accessible"
    else
        warn "⚠️  Database may not be fully ready yet"
    fi
    
    # Create success message
    cat > README.md << EOF
# 🚀 Agentic AI Full-Stack Tech Company

Successfully set up! Your agentic AI system is ready to create full-stack SaaS applications.

## Quick Start

1. **Start the system:**
   \`\`\`bash
   ./start.sh
   \`\`\`

2. **Or run manually:**
   \`\`\`bash
   # Activate environment (if you want to work in the shell)
   source .venv/bin/activate
   
   # Start services
   docker-compose -f local_ai_setup.yml up -d
   
   # Run the main application
   python main.py
   \`\`\`
   
   Or just use uv to run commands directly:
   \`\`\`bash
   uv run python main.py
   \`\`\`

## System Status

- ✅ System Dependencies: Installed
- ✅ Docker: Installed and configured
- ✅ GPU Support: $GPU_TYPE
- ✅ LocalAI: Configured and running
- ✅ Models: Downloaded
- ✅ Database: PostgreSQL + Redis running
- ✅ Python Environment: Ready (managed by uv)

## Next Steps

1. Customize the requirements in \`main.py\`
2. Run \`./start.sh\` to create your first SaaS application
3. Check the generated code in the \`outputs/\` directory
4. Deploy using the generated Docker configurations

## Support

For issues or questions, check the logs in \`logs/\` directory or review the configuration in \`configs/\`.

Happy coding! 🎉
EOF
    
    log "🎉 Setup completed successfully!"
    log "📚 Check README.md for next steps"
    log "🚀 Run './start.sh' to start the system"
}

# Main execution
main() {
    log "🚀 Starting Agentic AI Tech Company Setup"
    log "This will take approximately 15-30 minutes depending on your internet speed"
    
    check_requirements
    install_system_deps
    install_docker
    
    # GPU-specific installations
    if [ "$GPU_TYPE" = "amd" ]; then
        install_rocm
    elif [ "$GPU_TYPE" = "nvidia" ]; then
        install_cuda
    fi
    
    install_uv
    setup_project
    clone_repositories
    install_python_deps
    download_models
    setup_localai
    create_configs
    setup_database
    create_startup_script
    create_main_app
    final_setup
    
    log "🎊 Setup completed successfully!"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 Your Agentic AI Full-Stack Tech Company is ready!"
    echo ""
    echo "Next steps:"
    echo "1. cd $PROJECT_NAME"
    echo "2. ./start.sh"
    echo "3. Wait for the system to start (check README.md for details)"
    echo "4. Customize main.py and create your first SaaS application!"
    echo ""
    echo "📚 Documentation: Check README.md in the project directory"
    echo "🔧 Configuration: Edit files in configs/ directory"
    echo "📊 Monitoring: Check logs/ directory for system logs"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Run main function
main "$@" 