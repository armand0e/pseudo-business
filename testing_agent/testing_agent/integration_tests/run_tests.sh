#!/bin/bash

# Integration Test Runner Script
# This script automates the execution of the comprehensive integration testing framework
# for the Agentic AI Development Platform

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
REPORTS_DIR="$SCRIPT_DIR/reports"
DOCKER_COMPOSE_FILE="$SCRIPT_DIR/config/docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Integration Test Runner for Agentic AI Development Platform

Usage: $0 [OPTIONS]

OPTIONS:
    -s, --suite SUITE       Test suite to run (all|workflow|component|performance) [default: all]
    -e, --environment ENV   Test environment (docker|local) [default: docker]
    -v, --verbose          Enable verbose output
    -c, --cleanup          Clean up Docker environment after tests
    --skip-setup          Skip Docker environment setup
    --reports-only        Generate reports only (skip test execution)
    -h, --help            Show this help message

EXAMPLES:
    $0                                    # Run all tests with Docker environment
    $0 -s workflow -v                   # Run workflow tests with verbose output
    $0 -e local --skip-setup            # Run tests in local environment
    $0 --cleanup                        # Run tests and cleanup Docker environment
    $0 --reports-only                   # Generate reports from existing test data

EOF
}

# Parse command line arguments
SUITE="all"
ENVIRONMENT="docker"
VERBOSE=""
CLEANUP=false
SKIP_SETUP=false
REPORTS_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--suite)
            SUITE="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        -c|--cleanup)
            CLEANUP=true
            shift
            ;;
        --skip-setup)
            SKIP_SETUP=true
            shift
            ;;
        --reports-only)
            REPORTS_ONLY=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate suite option
if [[ ! "$SUITE" =~ ^(all|workflow|component|performance)$ ]]; then
    log_error "Invalid suite: $SUITE. Must be one of: all, workflow, component, performance"
    exit 1
fi

# Validate environment option
if [[ ! "$ENVIRONMENT" =~ ^(docker|local)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT. Must be one of: docker, local"
    exit 1
fi

# Function to check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is required but not installed"
        exit 1
    fi
    
    # Check Docker if using Docker environment
    if [[ "$ENVIRONMENT" == "docker" ]]; then
        if ! command -v docker &> /dev/null; then
            log_error "Docker is required but not installed"
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            log_error "Docker Compose is required but not installed"
            exit 1
        fi
        
        # Check if Docker daemon is running
        if ! docker info &> /dev/null; then
            log_error "Docker daemon is not running"
            exit 1
        fi
    fi
    
    log_success "Dependencies check passed"
}

# Function to setup Python environment
setup_python_environment() {
    log "Setting up Python environment..."
    
    cd "$PROJECT_ROOT"
    
    # Install requirements if they exist
    if [[ -f "requirements.txt" ]]; then
        python3 -m pip install -r requirements.txt
    fi
    
    # Install testing requirements
    if [[ -f "testing_agent/requirements.txt" ]]; then
        python3 -m pip install -r testing_agent/requirements.txt
    fi
    
    # Install additional test dependencies
    python3 -m pip install pytest pytest-html pytest-json-report psutil httpx
    
    log_success "Python environment ready"
}

# Function to setup Docker environment
setup_docker_environment() {
    if [[ "$SKIP_SETUP" == true ]]; then
        log "Skipping Docker environment setup"
        return
    fi
    
    log "Setting up Docker environment..."
    
    # Stop any existing containers
    docker-compose -f "$DOCKER_COMPOSE_FILE" down -v 2>/dev/null || true
    
    # Start the environment
    log "Starting Docker containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Check if services are healthy
    log "Checking service health..."
    for i in {1..12}; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up (healthy)"; then
            log_success "Services are healthy"
            return
        fi
        log "Waiting for services to become healthy... ($i/12)"
        sleep 10
    done
    
    log_warning "Some services may not be fully healthy, but proceeding with tests"
}

# Function to cleanup Docker environment
cleanup_docker_environment() {
    if [[ "$ENVIRONMENT" == "docker" ]]; then
        log "Cleaning up Docker environment..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" down -v
        
        # Remove unused volumes and networks
        docker volume prune -f 2>/dev/null || true
        docker network prune -f 2>/dev/null || true
        
        log_success "Docker environment cleaned up"
    fi
}

# Function to run tests
run_tests() {
    if [[ "$REPORTS_ONLY" == true ]]; then
        log "Skipping test execution (reports only mode)"
        return
    fi
    
    log "Running integration tests..."
    
    cd "$SCRIPT_DIR"
    
    # Create reports directory
    mkdir -p "$REPORTS_DIR"
    
    # Run the test runner
    python3 test_runner.py \
        --suite "$SUITE" \
        --environment "$ENVIRONMENT" \
        $VERBOSE
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "All tests passed"
    elif [[ $exit_code -eq 1 ]]; then
        log_warning "Some tests failed"
    else
        log_error "Test execution encountered errors"
    fi
    
    return $exit_code
}

# Function to generate summary report
generate_summary_report() {
    log "Generating summary report..."
    
    local summary_file="$REPORTS_DIR/test_summary.md"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    cat > "$summary_file" << EOF
# Integration Test Summary

**Execution Date:** $timestamp
**Test Suite:** $SUITE
**Environment:** $ENVIRONMENT

## Test Results

EOF
    
    # Add test results if JSON report exists
    if [[ -f "$REPORTS_DIR/integration_test_report.json" ]]; then
        python3 -c "
import json
import sys

try:
    with open('$REPORTS_DIR/integration_test_report.json', 'r') as f:
        data = json.load(f)
    
    summary = data.get('summary', {})
    print(f\"- **Total Tests:** {summary.get('total_tests', 0)}\")
    print(f\"- **Passed:** {summary.get('passed', 0)}\")
    print(f\"- **Failed:** {summary.get('failed', 0)}\")
    print(f\"- **Skipped:** {summary.get('skipped', 0)}\")
    print(f\"- **Success Rate:** {summary.get('success_rate', 0):.1f}%\")
    print(f\"- **Coverage:** {summary.get('coverage_percentage', 0):.1f}%\")
    print()
    print('## Performance Metrics')
    print()
    perf = data.get('performance_summary', {})
    if perf:
        print(f\"- **Average Response Time:** {perf.get('average_response_time_ms', 0):.2f} ms\")
        print(f\"- **Average Throughput:** {perf.get('average_throughput_rps', 0):.2f} RPS\")
        print(f\"- **Error Rate:** {perf.get('error_rate_percent', 0):.2f}%\")
except Exception as e:
    print(f'Error generating summary: {e}')
    sys.exit(1)
" >> "$summary_file"
    else
        echo "- Test results not available" >> "$summary_file"
    fi
    
    echo "" >> "$summary_file"
    echo "## Available Reports" >> "$summary_file"
    echo "" >> "$summary_file"
    
    for report in "$REPORTS_DIR"/*; do
        if [[ -f "$report" ]]; then
            local filename=$(basename "$report")
            echo "- [$filename](./$filename)" >> "$summary_file"
        fi
    done
    
    log_success "Summary report generated: $summary_file"
}

# Function to show test results
show_test_results() {
    log "Test execution completed"
    
    if [[ -f "$REPORTS_DIR/integration_test_report.json" ]]; then
        echo ""
        echo "=== TEST RESULTS SUMMARY ==="
        python3 -c "
import json
try:
    with open('$REPORTS_DIR/integration_test_report.json', 'r') as f:
        data = json.load(f)
    summary = data.get('summary', {})
    print(f\"Total Tests: {summary.get('total_tests', 0)}\")
    print(f\"Passed: {summary.get('passed', 0)}\")
    print(f\"Failed: {summary.get('failed', 0)}\")
    print(f\"Skipped: {summary.get('skipped', 0)}\")
    print(f\"Success Rate: {summary.get('success_rate', 0):.1f}%\")
    print(f\"Coverage: {summary.get('coverage_percentage', 0):.1f}%\")
except Exception as e:
    print(f'Error reading test results: {e}')
"
    fi
    
    echo ""
    echo "Reports available in: $REPORTS_DIR"
    echo ""
    
    # List available reports
    if [[ -d "$REPORTS_DIR" ]] && [[ "$(ls -A "$REPORTS_DIR")" ]]; then
        echo "Generated reports:"
        for report in "$REPORTS_DIR"/*; do
            if [[ -f "$report" ]]; then
                echo "  - $(basename "$report")"
            fi
        done
    fi
}

# Trap function for cleanup on exit
cleanup_on_exit() {
    local exit_code=$?
    
    if [[ "$CLEANUP" == true ]]; then
        cleanup_docker_environment
    fi
    
    if [[ $exit_code -ne 0 ]]; then
        log_error "Script exited with error code $exit_code"
    fi
    
    exit $exit_code
}

# Set trap for cleanup
trap cleanup_on_exit EXIT INT TERM

# Main execution
main() {
    log "Starting Integration Test Runner for Agentic AI Development Platform"
    log "Suite: $SUITE, Environment: $ENVIRONMENT"
    
    # Check dependencies
    check_dependencies
    
    # Setup Python environment
    setup_python_environment
    
    # Setup Docker environment if needed
    if [[ "$ENVIRONMENT" == "docker" ]]; then
        setup_docker_environment
    fi
    
    # Run tests
    local test_exit_code=0
    run_tests || test_exit_code=$?
    
    # Generate reports
    generate_summary_report
    
    # Show results
    show_test_results
    
    # Return with appropriate exit code
    return $test_exit_code
}

# Execute main function
main "$@"