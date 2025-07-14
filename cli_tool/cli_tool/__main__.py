#!/usr/bin/env python3
"""
CLI Tool Main Entry Point
Provides command-line interface for the Agentic AI Development Platform
"""

import sys
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="CLI Tool Service", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "cli-tool"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "CLI Tool Service", "status": "running"}

def main():
    """Main entry point for the CLI tool service"""
    print("Starting CLI Tool Service...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8007,
        log_level="info"
    )

if __name__ == "__main__":
    main() 