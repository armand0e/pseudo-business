"""
API documentation generation
"""
from fastapi.openapi.utils import get_openapi

def generate_api_docs(app):
    """Generate OpenAPI documentation for the FastAPI app"""
    return get_openapi(
        title=app.title,
        version="1.0.0",
        openapi_version="3.0.2",
        description="Backend Agent API Documentation",
        routes=app.routes
    )