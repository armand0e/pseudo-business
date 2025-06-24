"""Backend Agent Module

This module provides the BackendAgent class for generating backend code,
API endpoints, and business logic.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time
import json
import ast
from pathlib import Path

from src.infrastructure.logging_system import LoggingSystem

_logging_system = LoggingSystem()
logger = _logging_system.get_logger()

@dataclass
class CodeGenRequest:
    """Data class for code generation requests."""
    project_id: int
    requirements: str
    framework: str = "fastapi"
    database_type: str = "postgresql"
    authentication: bool = True
    api_docs: bool = True

@dataclass
class CodeGenResult:
    """Data class for code generation results."""
    success: bool
    files: Dict[str, str] = None  # filename -> content
    error: str = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

@dataclass
class APIEndpoint:
    """Data class for API endpoint specification."""
    path: str
    method: str
    function_name: str
    parameters: List[Dict[str, Any]]
    response_model: str
    description: str

@_logging_system.error_handler
class BackendAgent:
    """Backend Agent for generating backend code and API endpoints."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the BackendAgent.

        Args:
            config (Dict[str, Any]): Configuration for the backend agent.
        """
        logger.info("Initializing BackendAgent")
        self.config = config
        self.capabilities = [
            "fastapi_generation",
            "api_endpoint_creation",
            "database_integration",
            "authentication_setup",
            "documentation_generation"
        ]
        
        # Template storage
        self.templates = {
            "fastapi_main": self._get_fastapi_main_template(),
            "model": self._get_model_template(),
            "endpoint": self._get_endpoint_template(),
            "auth": self._get_auth_template(),
            "requirements": self._get_requirements_template()
        }

    def generate_backend_code(self, request: CodeGenRequest) -> CodeGenResult:
        """
        Generate backend code based on requirements.

        Args:
            request (CodeGenRequest): Code generation request.

        Returns:
            CodeGenResult: Generated code and metadata.
        """
        start_time = time.time()
        logger.info(f"Generating backend code for project {request.project_id}")
        
        try:
            # Parse requirements
            parsed_requirements = self._parse_requirements(request.requirements)
            
            # Generate code files
            generated_files = {}
            
            # Generate main application file
            generated_files["main.py"] = self._generate_main_file(request, parsed_requirements)
            
            # Generate models
            if parsed_requirements.get("models"):
                generated_files["models.py"] = self._generate_models_file(parsed_requirements["models"])
            
            # Generate API endpoints
            if parsed_requirements.get("endpoints"):
                generated_files["routes.py"] = self._generate_routes_file(parsed_requirements["endpoints"])
            
            # Generate authentication if required
            if request.authentication:
                generated_files["auth.py"] = self._generate_auth_file()
            
            # Generate requirements.txt
            generated_files["requirements.txt"] = self._generate_requirements_file(request)
            
            # Generate configuration
            generated_files["config.py"] = self._generate_config_file()
            
            execution_time = time.time() - start_time
            logger.info(f"Backend code generated successfully in {execution_time:.3f}s")
            
            return CodeGenResult(
                success=True,
                files=generated_files,
                execution_time=execution_time,
                metadata={
                    "framework": request.framework,
                    "files_generated": len(generated_files),
                    "endpoints": len(parsed_requirements.get("endpoints", [])),
                    "models": len(parsed_requirements.get("models", []))
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed to generate backend code: {e}")
            
            return CodeGenResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    def _parse_requirements(self, requirements: str) -> Dict[str, Any]:
        """
        Parse natural language requirements into structured data.

        Args:
            requirements (str): Natural language requirements.

        Returns:
            Dict[str, Any]: Parsed requirements.
        """
        logger.debug("Parsing requirements")
        
        # Simple requirement parsing (in production, use NLP)
        parsed = {
            "models": [],
            "endpoints": [],
            "features": []
        }
        
        # Look for model definitions
        if "user" in requirements.lower():
            parsed["models"].append({
                "name": "User",
                "fields": [
                    {"name": "id", "type": "int", "primary_key": True},
                    {"name": "username", "type": "str", "unique": True},
                    {"name": "email", "type": "str", "unique": True},
                    {"name": "created_at", "type": "datetime"}
                ]
            })
        
        # Look for endpoint requirements
        if "api" in requirements.lower() or "endpoint" in requirements.lower():
            if "user" in requirements.lower():
                parsed["endpoints"].extend([
                    {
                        "path": "/users",
                        "method": "GET",
                        "function_name": "list_users",
                        "description": "List all users"
                    },
                    {
                        "path": "/users",
                        "method": "POST",
                        "function_name": "create_user",
                        "description": "Create a new user"
                    },
                    {
                        "path": "/users/{user_id}",
                        "method": "GET",
                        "function_name": "get_user",
                        "description": "Get user by ID"
                    }
                ])
        
        # Look for authentication requirements
        if "auth" in requirements.lower() or "login" in requirements.lower():
            parsed["features"].append("authentication")
        
        logger.debug(f"Parsed requirements: {parsed}")
        return parsed

    def _generate_main_file(self, request: CodeGenRequest, parsed_requirements: Dict[str, Any]) -> str:
        """Generate the main FastAPI application file."""
        logger.debug("Generating main application file")
        
        imports = [
            "from fastapi import FastAPI, HTTPException, Depends",
            "from fastapi.middleware.cors import CORSMiddleware",
            "import uvicorn"
        ]
        
        if request.authentication:
            imports.append("from auth import get_current_user")
        
        if parsed_requirements.get("models"):
            imports.append("from models import *")
        
        if parsed_requirements.get("endpoints"):
            imports.append("from routes import router")
        
        app_creation = '''
app = FastAPI(
    title="Generated Backend API",
    description="Auto-generated backend API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''
        
        route_inclusion = ""
        if parsed_requirements.get("endpoints"):
            route_inclusion = "\napp.include_router(router)\n"
        
        health_endpoint = '''
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
'''
        
        main_block = '''
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        
        return "\n".join(imports) + app_creation + route_inclusion + health_endpoint + main_block

    def _generate_models_file(self, models: List[Dict[str, Any]]) -> str:
        """Generate SQLAlchemy models file."""
        logger.debug(f"Generating models file for {len(models)} models")
        
        imports = '''from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

Base = declarative_base()
'''
        
        model_classes = []
        pydantic_classes = []
        
        for model in models:
            # SQLAlchemy model
            class_name = model["name"]
            table_name = class_name.lower() + "s"
            
            model_class = f'''
class {class_name}(Base):
    __tablename__ = "{table_name}"
    
'''
            
            for field in model["fields"]:
                field_def = self._generate_field_definition(field)
                model_class += f"    {field_def}\n"
            
            model_classes.append(model_class)
            
            # Pydantic model for API
            pydantic_class = f'''
class {class_name}Create(BaseModel):
'''
            
            for field in model["fields"]:
                if not field.get("primary_key"):
                    field_type = self._convert_to_pydantic_type(field["type"])
                    optional = "Optional[" + field_type + "]" if field.get("optional") else field_type
                    pydantic_class += f'    {field["name"]}: {optional}\n'
            
            pydantic_class += f'''
class {class_name}Response(BaseModel):
'''
            
            for field in model["fields"]:
                field_type = self._convert_to_pydantic_type(field["type"])
                pydantic_class += f'    {field["name"]}: {field_type}\n'
            
            pydantic_class += '''
    class Config:
        from_attributes = True
'''
            
            pydantic_classes.append(pydantic_class)
        
        return imports + "\n".join(model_classes) + "\n" + "\n".join(pydantic_classes)

    def _generate_field_definition(self, field: Dict[str, Any]) -> str:
        """Generate SQLAlchemy field definition."""
        field_name = field["name"]
        field_type = field["type"]
        
        # Map types to SQLAlchemy types
        type_mapping = {
            "int": "Integer",
            "str": "String(255)",
            "text": "Text",
            "bool": "Boolean",
            "datetime": "DateTime"
        }
        
        sqlalchemy_type = type_mapping.get(field_type, "String(255)")
        
        definition = f'{field_name} = Column({sqlalchemy_type}'
        
        if field.get("primary_key"):
            definition += ", primary_key=True"
        if field.get("unique"):
            definition += ", unique=True"
        if field.get("nullable", True) == False:
            definition += ", nullable=False"
        if field_type == "datetime":
            definition += ", default=datetime.utcnow"
        
        definition += ")"
        return definition

    def _convert_to_pydantic_type(self, field_type: str) -> str:
        """Convert field type to Pydantic type."""
        type_mapping = {
            "int": "int",
            "str": "str",
            "text": "str",
            "bool": "bool",
            "datetime": "datetime"
        }
        return type_mapping.get(field_type, "str")

    def _generate_routes_file(self, endpoints: List[Dict[str, Any]]) -> str:
        """Generate API routes file."""
        logger.debug(f"Generating routes file for {len(endpoints)} endpoints")
        
        imports = '''from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from models import *
from database import get_db

router = APIRouter()
'''
        
        route_functions = []
        
        for endpoint in endpoints:
            route_function = self._generate_route_function(endpoint)
            route_functions.append(route_function)
        
        return imports + "\n".join(route_functions)

    def _generate_route_function(self, endpoint: Dict[str, Any]) -> str:
        """Generate individual route function."""
        method = endpoint["method"].lower()
        path = endpoint["path"]
        function_name = endpoint["function_name"]
        description = endpoint.get("description", "")
        
        decorator = f'@router.{method}("{path}")'
        
        if method == "get" and "{" in path:
            # GET with path parameter
            param_name = path.split("{")[1].split("}")[0]
            function_def = f'async def {function_name}({param_name}: int, db: Session = Depends(get_db)):'
            body = f'''    """
    {description}
    """
    # Implementation here
    return {{"message": "Endpoint not implemented"}}'''
        
        elif method == "get":
            # GET list
            function_def = f'async def {function_name}(db: Session = Depends(get_db)):'
            body = f'''    """
    {description}
    """
    # Implementation here
    return []'''
        
        elif method == "post":
            # POST create
            function_def = f'async def {function_name}(item: dict, db: Session = Depends(get_db)):'
            body = f'''    """
    {description}
    """
    # Implementation here
    return {{"message": "Item created"}}'''
        
        else:
            function_def = f'async def {function_name}(db: Session = Depends(get_db)):'
            body = f'''    """
    {description}
    """
    # Implementation here
    return {{"message": "Endpoint not implemented"}}'''
        
        return f"\n{decorator}\n{function_def}\n{body}\n"

    def _generate_auth_file(self) -> str:
        """Generate authentication module."""
        logger.debug("Generating authentication file")
        
        return '''from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
import bcrypt

security = HTTPBearer()

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def get_current_user(username: str = Depends(verify_token)):
    return {"username": username}

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
'''

    def _generate_requirements_file(self, request: CodeGenRequest) -> str:
        """Generate requirements.txt file."""
        logger.debug("Generating requirements file")
        
        requirements = [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
            "sqlalchemy>=2.0.0",
            "pydantic>=2.0.0"
        ]
        
        if request.database_type == "postgresql":
            requirements.append("psycopg2-binary>=2.9.0")
        elif request.database_type == "mysql":
            requirements.append("pymysql>=1.0.0")
        
        if request.authentication:
            requirements.extend([
                "python-jose[cryptography]>=3.3.0",
                "python-multipart>=0.0.6",
                "bcrypt>=4.0.0"
            ])
        
        return "\n".join(requirements)

    def _generate_config_file(self) -> str:
        """Generate configuration file."""
        logger.debug("Generating configuration file")
        
        return '''import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

    def _get_fastapi_main_template(self) -> str:
        """Get FastAPI main template."""
        return "# FastAPI main template placeholder"

    def _get_model_template(self) -> str:
        """Get model template."""
        return "# Model template placeholder"

    def _get_endpoint_template(self) -> str:
        """Get endpoint template."""
        return "# Endpoint template placeholder"

    def _get_auth_template(self) -> str:
        """Get auth template."""
        return "# Auth template placeholder"

    def _get_requirements_template(self) -> str:
        """Get requirements template."""
        return "# Requirements template placeholder"

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.capabilities

    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validate generated code for syntax errors.

        Args:
            code (str): Python code to validate.

        Returns:
            Dict[str, Any]: Validation result.
        """
        try:
            ast.parse(code)
            return {"valid": True, "errors": []}
        except SyntaxError as e:
            return {
                "valid": False,
                "errors": [f"Syntax error at line {e.lineno}: {e.msg}"]
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }