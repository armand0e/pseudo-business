#!/usr/bin/env python3
"""Main entry point for DevOps Agent service."""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="DevOps Agent", version="1.0.0")

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "healthy", "service": "devops-agent"})

@app.get("/")
async def root():
    return JSONResponse({"message": "DevOps Agent is running", "version": "1.0.0"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005) 