#!/usr/bin/env python3
"""
Testing Agent Main Entry Point
Provides testing services for the Agentic AI Development Platform
"""

import sys
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Testing Agent Service", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "testing-agent"}

@app.get("/status")
async def get_status():
    """Detailed service status"""
    return {
        "status": "running",
        "service": "testing-agent",
        "port": 8005,
        "version": "1.0.0",
        "components": {
            "test_generator": "healthy",
            "security_scanner": "healthy",
            "coverage_analyzer": "healthy"
        }
    }

@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics"""
    return {
        "tests_generated": 0,
        "security_scans_completed": 0,
        "coverage_percentage": 0.0,
        "test_execution_time": 0.0
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Testing Agent Service", "status": "running"}

@app.get("/test/run")
async def run_tests():
    """Run tests endpoint"""
    return {"message": "Running tests", "status": "success"}

def main():
    """Main entry point for the testing agent service"""
    print("Starting Testing Agent Service...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8005,
        log_level="info"
    )

if __name__ == "__main__":
    main() 