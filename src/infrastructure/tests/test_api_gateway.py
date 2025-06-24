"""Tests for API Gateway Module"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta

from src.infrastructure.api_gateway import APIGateway, APIResponse


class TestAPIGateway:
    """Test cases for APIGateway."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            'jwt_secret': 'test-secret-key',
            'jwt_algorithm': 'HS256',
            'jwt_expiry_hours': 24,
            'rate_limiting': {
                'max_requests_per_minute': 100
            },
            'cors': {
                'allowed_origins': ['*']
            },
            'allowed_hosts': ['*'],
            'default_users': {
                'testuser': 'testpass'
            }
        }

    @pytest.fixture
    def api_gateway(self, config):
        """Create API Gateway instance for testing."""
        gateway = APIGateway(config)
        
        # Mock dependencies
        mock_database_agent = Mock()
        mock_database_agent.health_check.return_value = True
        mock_orchestrator = Mock()
        
        gateway.set_dependencies(
            database_agent=mock_database_agent,
            master_orchestrator=mock_orchestrator
        )
        
        return gateway

    @pytest.fixture
    def client(self, api_gateway):
        """Create test client."""
        return TestClient(api_gateway.get_app())

    def test_api_gateway_initialization(self, config):
        """Test API Gateway initialization."""
        gateway = APIGateway(config)
        
        assert gateway.config == config
        assert gateway.jwt_secret == 'test-secret-key'
        assert gateway.jwt_algorithm == 'HS256'
        assert gateway.jwt_expiry_hours == 24
        assert gateway.max_requests_per_minute == 100

    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'data' in data
        assert data['data']['api_gateway'] == 'healthy'

    def test_login_success(self, client):
        """Test successful login."""
        login_data = {
            'username': 'testuser',
            'password': 'testpass'
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'token' in data['data']
        assert 'expires_in' in data['data']

    def test_login_failure(self, client):
        """Test login failure with invalid credentials."""
        login_data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert response.json()['detail'] == 'Invalid credentials'

    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        login_data = {
            'username': 'testuser'
            # Missing password
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 422  # Validation error

    def test_generate_jwt_token(self, api_gateway):
        """Test JWT token generation."""
        username = 'testuser'
        token = api_gateway._generate_jwt_token(username)
        
        # Decode token to verify
        payload = jwt.decode(
            token,
            api_gateway.jwt_secret,
            algorithms=[api_gateway.jwt_algorithm]
        )
        
        assert payload['sub'] == username
        assert 'exp' in payload
        assert 'iat' in payload

    def test_authenticate_user_success(self, api_gateway):
        """Test successful user authentication."""
        result = api_gateway._authenticate_user('testuser', 'testpass')
        assert result is True

    def test_authenticate_user_failure(self, api_gateway):
        """Test failed user authentication."""
        result = api_gateway._authenticate_user('testuser', 'wrongpass')
        assert result is False

    def test_rate_limiting(self, api_gateway):
        """Test rate limiting functionality."""
        client_ip = '127.0.0.1'
        
        # First request should pass
        assert api_gateway._check_rate_limit(client_ip) is True
        
        # Simulate many requests
        for _ in range(api_gateway.max_requests_per_minute):
            api_gateway._check_rate_limit(client_ip)
        
        # Next request should be blocked
        assert api_gateway._check_rate_limit(client_ip) is False

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.post("/projects", json={
            'name': 'Test Project',
            'description': 'Test Description'
        })
        
        assert response.status_code == 403  # Forbidden due to missing token

    def test_protected_endpoint_with_valid_token(self, client, api_gateway):
        """Test accessing protected endpoint with valid token."""
        # Generate valid token
        token = api_gateway._generate_jwt_token('testuser')
        
        # Mock database agent response
        api_gateway.database_agent.create_project.return_value = Mock(
            success=True,
            data={'id': 1, 'name': 'Test Project'}
        )
        
        response = client.post(
            "/projects",
            json={
                'name': 'Test Project',
                'description': 'Test Description'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.post(
            "/projects",
            json={
                'name': 'Test Project',
                'description': 'Test Description'
            },
            headers={'Authorization': 'Bearer invalid-token'}
        )
        
        assert response.status_code == 401

    def test_protected_endpoint_with_expired_token(self, client, api_gateway):
        """Test accessing protected endpoint with expired token."""
        # Generate expired token
        payload = {
            'sub': 'testuser',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() - timedelta(hours=1)  # Expired
        }
        expired_token = jwt.encode(
            payload,
            api_gateway.jwt_secret,
            algorithm=api_gateway.jwt_algorithm
        )
        
        response = client.post(
            "/projects",
            json={
                'name': 'Test Project',
                'description': 'Test Description'
            },
            headers={'Authorization': f'Bearer {expired_token}'}
        )
        
        assert response.status_code == 401

    def test_create_project_endpoint(self, client, api_gateway):
        """Test project creation endpoint."""
        # Generate valid token
        token = api_gateway._generate_jwt_token('testuser')
        
        # Mock database agent response
        api_gateway.database_agent.create_project.return_value = Mock(
            success=True,
            data={'id': 1, 'name': 'Test Project'}
        )
        
        response = client.post(
            "/projects",
            json={
                'name': 'Test Project',
                'description': 'Test Description'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['id'] == 1
        assert data['data']['name'] == 'Test Project'

    def test_create_project_database_error(self, client, api_gateway):
        """Test project creation with database error."""
        # Generate valid token
        token = api_gateway._generate_jwt_token('testuser')
        
        # Mock database agent error response
        api_gateway.database_agent.create_project.return_value = Mock(
            success=False,
            error='Database connection failed'
        )
        
        response = client.post(
            "/projects",
            json={
                'name': 'Test Project',
                'description': 'Test Description'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 500

    def test_create_task_endpoint(self, client, api_gateway):
        """Test task creation endpoint."""
        # Generate valid token
        token = api_gateway._generate_jwt_token('testuser')
        
        # Mock database agent response
        api_gateway.database_agent.create_task.return_value = Mock(
            success=True,
            data={'id': 1, 'task_id': 'task_001'}
        )
        
        response = client.post(
            "/tasks",
            json={
                'task_id': 'task_001',
                'project_id': 1,
                'description': 'Test task',
                'agent_type': 'backend',
                'priority': 1
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['task_id'] == 'task_001'

    def test_list_tasks_endpoint(self, client, api_gateway):
        """Test task listing endpoint."""
        # Generate valid token
        token = api_gateway._generate_jwt_token('testuser')
        
        # Mock database agent response
        api_gateway.database_agent.get_pending_tasks.return_value = Mock(
            success=True,
            data=[
                {
                    'task_id': 'task_001',
                    'description': 'Test task',
                    'agent_type': 'backend',
                    'priority': 1
                }
            ]
        )
        
        response = client.get(
            "/tasks",
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['task_id'] == 'task_001'

    def test_register_agent_endpoint(self, client, api_gateway):
        """Test agent registration endpoint."""
        # Generate valid token
        token = api_gateway._generate_jwt_token('testuser')
        
        # Mock database agent response
        api_gateway.database_agent.register_agent.return_value = Mock(
            success=True,
            data={'id': 1, 'agent_id': 'agent_001'}
        )
        
        response = client.post(
            "/agents",
            json={
                'agent_id': 'agent_001',
                'agent_type': 'backend',
                'capabilities': ['fastapi', 'sqlalchemy']
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['agent_id'] == 'agent_001'

    def test_get_agent_status_endpoint(self, client, api_gateway):
        """Test agent status endpoint."""
        # Generate valid token
        token = api_gateway._generate_jwt_token('testuser')
        
        # Mock master orchestrator response
        api_gateway.master_orchestrator.get_agent_status.return_value = {
            'agent_id': 'agent_001',
            'status': 'idle',
            'type': 'backend'
        }
        
        response = client.get(
            "/agents/agent_001/status",
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['agent_id'] == 'agent_001'

    def test_refresh_token_endpoint(self, client, api_gateway):
        """Test token refresh endpoint."""
        # Generate valid token
        token = api_gateway._generate_jwt_token('testuser')
        
        response = client.post(
            "/auth/refresh",
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'token' in data['data']

    def test_validation_errors(self, client, api_gateway):
        """Test request validation errors."""
        # Generate valid token
        token = api_gateway._generate_jwt_token('testuser')
        
        # Test with invalid project data (missing name)
        response = client.post(
            "/projects",
            json={
                'description': 'Test Description'
                # Missing required 'name' field
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 422  # Validation error

    def test_service_unavailable(self, client, api_gateway):
        """Test service unavailable when dependencies are missing."""
        # Generate valid token
        token = api_gateway._generate_jwt_token('testuser')
        
        # Set database agent to None
        api_gateway.database_agent = None
        
        response = client.post(
            "/projects",
            json={
                'name': 'Test Project',
                'description': 'Test Description'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 503  # Service unavailable


if __name__ == "__main__":
    pytest.main([__file__])