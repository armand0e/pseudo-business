#!/usr/bin/env python3
"""Main entry point for Evolution Engine service."""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Evolution Engine", version="1.0.0")

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "healthy", "service": "evolution-engine"})

@app.get("/")
async def root():
    return JSONResponse({"message": "Evolution Engine is running", "version": "1.0.0"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006) 