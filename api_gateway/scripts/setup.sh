#!/bin/bash

# Setup script for Agentic AI API Gateway
# This script sets up the development environment

set -e

echo "🚀 Setting up Agentic AI API Gateway..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
check_node() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+ and try again."
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version 18+ is required. Current version: $(node -v)"
        exit 1
    fi
    
    print_success "Node.js $(node -v) is installed"
}

# Check if npm is installed
check_npm() {
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm and try again."
        exit 1
    fi
    print_success "npm $(npm -v) is installed"
}

# Create logs directory
create_logs_dir() {
    print_status "Creating logs directory..."
    mkdir -p logs
    print_success "Logs directory created"
}

# Install dependencies
install_dependencies() {
    print_status "Installing npm dependencies..."
    npm install
    print_success "Dependencies installed successfully"
}

# Setup environment file
setup_environment() {
    if [ ! -f .env ]; then
        print_status "Setting up environment variables..."
        cp .env.example .env
        print_success "Environment file created from template"
        print_warning "Please edit .env file with your configuration before starting the server"
    else
        print_warning ".env file already exists, skipping environment setup"
    fi
}

# Generate JWT secret if not set
generate_jwt_secret() {
    if [ -f .env ]; then
        if grep -q "JWT_SECRET=your-super-secret-jwt-key-change-this-in-production" .env; then
            print_status "Generating secure JWT secret..."
            JWT_SECRET=$(openssl rand -hex 32)
            if command -v openssl &> /dev/null; then
                sed -i.bak "s/JWT_SECRET=your-super-secret-jwt-key-change-this-in-production/JWT_SECRET=$JWT_SECRET/" .env
                rm .env.bak 2>/dev/null || true
                print_success "JWT secret generated and updated in .env"
            else
                print_warning "OpenSSL not found. Please manually update JWT_SECRET in .env file"
            fi
        else
            print_success "JWT secret already configured"
        fi
    fi
}

# Check if Redis is available (optional)
check_redis() {
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping > /dev/null 2>&1; then
            print_success "Redis is available and running"
        else
            print_warning "Redis is installed but not running. Rate limiting will use in-memory store."
        fi
    else
        print_warning "Redis is not installed. Rate limiting will use in-memory store."
        print_status "To install Redis:"
        print_status "  macOS: brew install redis"
        print_status "  Ubuntu: sudo apt-get install redis-server"
        print_status "  CentOS: sudo yum install redis"
    fi
}

# Verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Check if all required files exist
    required_files=(
        "src/index.js"
        "src/middleware/auth.js"
        "src/middleware/errorHandler.js"
        "src/routes/auth.js"
        "src/routes/health.js"
        "src/routes/proxy.js"
        "src/utils/logger.js"
        "src/utils/swagger.js"
        "package.json"
        ".env"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file $file is missing"
            exit 1
        fi
    done
    
    print_success "All required files are present"
}

# Run tests
run_tests() {
    print_status "Running tests to verify setup..."
    if npm test; then
        print_success "All tests passed"
    else
        print_warning "Some tests failed. The setup is complete but you may need to check the configuration."
    fi
}

# Display next steps
show_next_steps() {
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Review and update the .env file with your configuration"
    echo "2. Start the development server:"
    echo "   npm run dev"
    echo ""
    echo "3. Access the API Gateway:"
    echo "   - API: http://localhost:3000"
    echo "   - Documentation: http://localhost:3000/api-docs"
    echo "   - Health Check: http://localhost:3000/health"
    echo ""
    echo "4. For production deployment:"
    echo "   - Update environment variables for production"
    echo "   - Set up backend services (orchestrator, agents)"
    echo "   - Configure load balancer and SSL/TLS"
    echo ""
    echo "📖 For more information, see README.md"
}

# Main setup process
main() {
    echo "=========================================="
    echo "  Agentic AI API Gateway Setup"
    echo "=========================================="
    echo ""
    
    check_node
    check_npm
    create_logs_dir
    install_dependencies
    setup_environment
    generate_jwt_secret
    check_redis
    verify_installation
    
    # Ask if user wants to run tests
    echo ""
    read -p "Would you like to run the test suite? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_tests
    fi
    
    show_next_steps
}

# Run main function
main "$@"