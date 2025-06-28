"""
Main module for Backend Agent FastAPI application
"""
from fastapi import FastAPI, Depends
from .routers import items
from .dependencies import get_db_session
from .auth import authenticate_token

app = FastAPI(title="Backend Agent API")

# Include routers
app.include_router(items.router)

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    print("Backend Agent starting up...")

    # Add error handling middleware
    from .middleware import add_error_handling_middleware
    add_error_handling_middleware(app)

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    print("Backend Agent shutting down...")

@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/docs.json", tags=["documentation"])
async def get_docs():
    """Get OpenAPI documentation in JSON format"""
    from .docs import generate_api_docs
    return generate_api_docs(app)