#!/usr/bin/env python3
"""Main entry point for CLI Tool service."""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="CLI Tool", version="1.0.0")

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "healthy", "service": "cli-tool"})

@app.get("/")
async def root():
    return JSONResponse({"message": "CLI Tool is running", "version": "1.0.0"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007) 