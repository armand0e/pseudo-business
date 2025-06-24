#!/usr/bin/env python3
"""
Platform Startup Script

This script provides a convenient way to start the Agentic AI Development Platform
with proper environment setup and dependency checking.
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("Checking dependencies...")
    
    try:
        import yaml
        import fastapi
        import sqlalchemy
        import uvicorn
        print("✓ All required Python packages are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing required package: {e.name}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_docker():
    """Check if Docker is available and running."""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Docker is available")
            
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'info'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Docker daemon is running")
                return True
            else:
                print("✗ Docker daemon is not running")
                print("Please start Docker daemon")
                return False
        else:
            print("✗ Docker is not available")
            return False
    except FileNotFoundError:
        print("✗ Docker is not installed")
        return False

def start_database_services():
    """Start database and supporting services using Docker Compose."""
    print("Starting database services...")
    
    try:
        result = subprocess.run([
            'docker-compose', '-f', 'docker-compose.dev.yml', 'up', '-d'
        ], check=True, capture_output=True, text=True)
        
        print("✓ Database services started successfully")
        
        # Wait for services to be ready
        print("Waiting for services to be ready...")
        time.sleep(10)
        
        # Check service health
        result = subprocess.run([
            'docker-compose', '-f', 'docker-compose.dev.yml', 'ps'
        ], capture_output=True, text=True)
        
        print("Service status:")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to start database services: {e}")
        print("Error output:", e.stderr)
        return False

def setup_database():
    """Set up database schema."""
    print("Setting up database schema...")
    
    # Note: In a production setup, you would run Alembic migrations here
    # For now, the tables will be created automatically by SQLAlchemy
    print("✓ Database schema will be created automatically on first run")
    return True

def start_platform():
    """Start the main platform application."""
    print("Starting Agentic AI Development Platform...")
    
    try:
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path.cwd())
        
        # Start the platform
        subprocess.run([
            sys.executable, '-m', 'src.main'
        ], env=env, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to start platform: {e}")
        return False
    except KeyboardInterrupt:
        print("\n✓ Platform shutdown requested")
        return True

def stop_services():
    """Stop all services."""
    print("Stopping services...")
    
    try:
        subprocess.run([
            'docker-compose', '-f', 'docker-compose.dev.yml', 'down'
        ], check=True)
        print("✓ Services stopped successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to stop services: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Start the Agentic AI Development Platform')
    parser.add_argument('--skip-deps', action='store_true', 
                       help='Skip dependency checking')
    parser.add_argument('--skip-docker', action='store_true',
                       help='Skip Docker services (use external database)')
    parser.add_argument('--stop', action='store_true',
                       help='Stop all services and exit')
    
    args = parser.parse_args()
    
    if args.stop:
        stop_services()
        return
    
    print("=" * 60)
    print("Agentic AI Development Platform - Startup Script")
    print("=" * 60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check dependencies
    if not args.skip_deps:
        if not check_dependencies():
            sys.exit(1)
    
    # Check Docker and start services
    if not args.skip_docker:
        if not check_docker():
            print("Warning: Docker not available. You'll need to provide external database.")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
        else:
            if not start_database_services():
                sys.exit(1)
            
            if not setup_database():
                sys.exit(1)
    
    # Start the platform
    try:
        print("\n" + "=" * 60)
        print("Starting Platform...")
        print("=" * 60)
        print("Platform will be available at: http://localhost:8000")
        print("API documentation: http://localhost:8000/docs")
        print("Database admin (Adminer): http://localhost:8080")
        print("Press Ctrl+C to stop the platform")
        print("=" * 60)
        
        start_platform()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if not args.skip_docker:
            stop_services()

if __name__ == "__main__":
    main()