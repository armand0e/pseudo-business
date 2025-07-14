#!/usr/bin/env python3
"""Main entry point for Testing Agent service."""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Testing Agent", version="1.0.0")

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "healthy", "service": "testing-agent"})

@app.get("/")
async def root():
    return JSONResponse({"message": "Testing Agent is running", "version": "1.0.0"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004) 