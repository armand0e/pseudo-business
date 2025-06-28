#!/bin/bash

# Quick start script for Agentic AI API Gateway
# This script starts the API Gateway with proper environment setup

set -e

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

# Check if .env file exists
check_environment() {
    if [ ! -f .env ]; then
        print_error ".env file not found!"
        print_status "Please run './scripts/setup.sh' first or copy .env.example to .env"
        exit 1
    fi
    print_success "Environment file found"
}

# Check if dependencies are installed
check_dependencies() {
    if [ ! -d node_modules ]; then
        print_error "Dependencies not installed!"
        print_status "Running npm install..."
        npm install
        print_success "Dependencies installed"
    else
        print_success "Dependencies are installed"
    fi
}

# Create logs directory if it doesn't exist
ensure_logs_dir() {
    if [ ! -d logs ]; then
        print_status "Creating logs directory..."
        mkdir -p logs
        print_success "Logs directory created"
    fi
}

# Check backend services (optional)
check_backend_services() {
    print_status "Checking backend services..."
    
    # Load environment variables
    source .env
    
    # Check Master Orchestrator
    if [ ! -z "$MASTER_ORCHESTRATOR_URL" ]; then
        if curl -s --connect-timeout 5 "$MASTER_ORCHESTRATOR_URL/health" > /dev/null 2>&1; then
            print_success "Master Orchestrator is available at $MASTER_ORCHESTRATOR_URL"
        else
            print_warning "Master Orchestrator is not available at $MASTER_ORCHESTRATOR_URL"
        fi
    fi
    
    # Check Backend Agent
    if [ ! -z "$BACKEND_AGENT_URL" ]; then
        if curl -s --connect-timeout 5 "$BACKEND_AGENT_URL/health" > /dev/null 2>&1; then
            print_success "Backend Agent is available at $BACKEND_AGENT_URL"
        else
            print_warning "Backend Agent is not available at $BACKEND_AGENT_URL"
        fi
    fi
    
    # Check Database Agent
    if [ ! -z "$DATABASE_AGENT_URL" ]; then
        if curl -s --connect-timeout 5 "$DATABASE_AGENT_URL/health" > /dev/null 2>&1; then
            print_success "Database Agent is available at $DATABASE_AGENT_URL"
        else
            print_warning "Database Agent is not available at $DATABASE_AGENT_URL"
        fi
    fi
}

# Check Redis connection (optional)
check_redis() {
    source .env
    if [ ! -z "$REDIS_HOST" ]; then
        if command -v redis-cli &> /dev/null; then
            if redis-cli -h "$REDIS_HOST" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; then
                print_success "Redis is available at $REDIS_HOST:${REDIS_PORT:-6379}"
            else
                print_warning "Redis is not available at $REDIS_HOST:${REDIS_PORT:-6379}"
                print_warning "Rate limiting will fall back to in-memory store"
            fi
        else
            print_warning "redis-cli not available to test Redis connection"
        fi
    fi
}

# Display startup information
show_startup_info() {
    source .env
    echo ""
    echo "🚀 Starting Agentic AI API Gateway..."
    echo ""
    echo "Configuration:"
    echo "  Environment: ${NODE_ENV:-development}"
    echo "  Port: ${PORT:-3000}"
    echo "  Host: ${HOST:-0.0.0.0}"
    echo ""
    echo "Backend Services:"
    echo "  Master Orchestrator: ${MASTER_ORCHESTRATOR_URL:-not configured}"
    echo "  Backend Agent: ${BACKEND_AGENT_URL:-not configured}"
    echo "  Database Agent: ${DATABASE_AGENT_URL:-not configured}"
    echo "  Specialized Agents: ${SPECIALIZED_AGENTS_BASE_URL:-not configured}"
    echo ""
    echo "Features:"
    echo "  Rate Limiting: ${FEATURE_RATE_LIMITING:-true}"
    echo "  Request Logging: ${FEATURE_REQUEST_LOGGING:-true}"
    echo "  API Documentation: ${API_DOCS_ENABLED:-true}"
    echo ""
}

# Start the server
start_server() {
    source .env
    NODE_ENV=${NODE_ENV:-development}
    
    if [ "$NODE_ENV" = "development" ]; then
        print_status "Starting development server with hot reload..."
        npm run dev
    else
        print_status "Starting production server..."
        npm start
    fi
}

# Show access information
show_access_info() {
    source .env
    PORT=${PORT:-3000}
    echo ""
    echo "🎉 API Gateway is running!"
    echo ""
    echo "Access URLs:"
    echo "  API Gateway: http://localhost:$PORT"
    echo "  Health Check: http://localhost:$PORT/health"
    echo "  API Documentation: http://localhost:$PORT/api-docs"
    echo ""
    echo "To stop the server, press Ctrl+C"
    echo ""
}

# Handle script interruption
cleanup() {
    echo ""
    print_status "Shutting down API Gateway..."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main function
main() {
    echo "==========================================="
    echo "  Agentic AI API Gateway Startup"
    echo "==========================================="
    echo ""
    
    check_environment
    check_dependencies
    ensure_logs_dir
    
    # Optional checks (don't fail if they don't work)
    check_redis || true
    check_backend_services || true
    
    show_startup_info
    show_access_info &
    
    # Small delay to let the access info show before server logs
    sleep 1
    
    start_server
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-checks)
            SKIP_CHECKS=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --skip-checks    Skip backend service health checks"
            echo "  --help, -h       Show this help message"
            echo ""
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main "$@"