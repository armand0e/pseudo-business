"""Tests for Database Agent Module"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agents.database_agent import DatabaseAgent, QueryResult, DatabaseSchema
from src.infrastructure.config_manager import ConfigManager


class TestDatabaseAgent:
    """Test cases for DatabaseAgent."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db',
                'username': 'test_user',
                'password': 'test_pass'
            }
        }

    @pytest.fixture
    def mock_database_agent(self, config):
        """Create a mock database agent for testing."""
        with patch('src.agents.database_agent.create_engine') as mock_engine:
            mock_engine.return_value = Mock()
            with patch('src.agents.database_agent.sessionmaker') as mock_session_factory:
                mock_session_factory.return_value = Mock()
                agent = DatabaseAgent(config)
                return agent

    def test_database_agent_initialization(self, config):
        """Test database agent initialization."""
        with patch('src.agents.database_agent.create_engine') as mock_engine:
            mock_engine.return_value = Mock()
            with patch('src.agents.database_agent.sessionmaker') as mock_session_factory:
                mock_session_factory.return_value = Mock()
                
                agent = DatabaseAgent(config)
                
                assert agent.config == config
                assert agent.db_config == config['database']
                mock_engine.assert_called_once()
                mock_session_factory.assert_called_once()

    def test_build_connection_string(self, config):
        """Test connection string building."""
        with patch('src.agents.database_agent.create_engine'):
            with patch('src.agents.database_agent.sessionmaker'):
                agent = DatabaseAgent(config)
                
                expected_connection_string = "postgresql://test_user:test_pass@localhost:5432/test_db"
                assert agent.connection_string == expected_connection_string

    def test_create_project_success(self, mock_database_agent):
        """Test successful project creation."""
        # Mock session
        mock_session = Mock()
        mock_database_agent.session_factory.return_value = mock_session
        
        # Mock project model
        mock_project = Mock()
        mock_project.id = 1
        mock_project.name = "Test Project"
        
        with patch('src.agents.database_agent.ProjectModel', return_value=mock_project):
            result = mock_database_agent.create_project("Test Project", "Test Description")
            
            assert result.success is True
            assert result.data == {'id': 1, 'name': 'Test Project'}
            assert result.execution_time > 0
            
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_create_project_failure(self, mock_database_agent):
        """Test project creation failure."""
        # Mock session that raises an exception
        mock_session = Mock()
        mock_session.commit.side_effect = Exception("Database error")
        mock_database_agent.session_factory.return_value = mock_session
        
        result = mock_database_agent.create_project("Test Project")
        
        assert result.success is False
        assert "Database error" in result.error
        assert result.execution_time > 0
        
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    def test_create_task_success(self, mock_database_agent):
        """Test successful task creation."""
        # Mock session
        mock_session = Mock()
        mock_database_agent.session_factory.return_value = mock_session
        
        # Mock task model
        mock_task = Mock()
        mock_task.id = 1
        mock_task.task_id = "task_001"
        
        with patch('src.agents.database_agent.TaskModel', return_value=mock_task):
            result = mock_database_agent.create_task(
                task_id="task_001",
                project_id=1,
                description="Test task",
                agent_type="backend",
                priority=1
            )
            
            assert result.success is True
            assert result.data == {'id': 1, 'task_id': 'task_001'}
            
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_register_agent_success(self, mock_database_agent):
        """Test successful agent registration."""
        # Mock session
        mock_session = Mock()
        mock_database_agent.session_factory.return_value = mock_session
        
        # Mock agent model
        mock_agent = Mock()
        mock_agent.id = 1
        mock_agent.agent_id = "agent_001"
        
        with patch('src.agents.database_agent.AgentModel', return_value=mock_agent):
            result = mock_database_agent.register_agent(
                agent_id="agent_001",
                agent_type="backend",
                capabilities=["fastapi", "sqlalchemy"]
            )
            
            assert result.success is True
            assert result.data == {'id': 1, 'agent_id': 'agent_001'}
            
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_get_pending_tasks_success(self, mock_database_agent):
        """Test successful retrieval of pending tasks."""
        # Mock session and query
        mock_session = Mock()
        mock_query = Mock()
        mock_task = Mock()
        mock_task.task_id = "task_001"
        mock_task.project_id = 1
        mock_task.description = "Test task"
        mock_task.agent_type = "backend"
        mock_task.priority = 1
        mock_task.created_at = None
        
        mock_query.order_by.return_value.all.return_value = [mock_task]
        mock_query.filter_by.return_value = mock_query
        mock_session.query.return_value.filter_by.return_value = mock_query
        mock_database_agent.session_factory.return_value = mock_session
        
        with patch('src.agents.database_agent.TaskModel') as mock_task_model:
            result = mock_database_agent.get_pending_tasks(agent_type="backend")
            
            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]['task_id'] == "task_001"
            
            mock_session.close.assert_called_once()

    def test_generate_schema(self, mock_database_agent):
        """Test schema generation."""
        columns = [
            {"name": "id", "type": "int", "primary_key": True},
            {"name": "name", "type": "str", "nullable": False}
        ]
        
        schema = mock_database_agent.generate_schema("users", columns)
        
        assert isinstance(schema, DatabaseSchema)
        assert schema.table_name == "users"
        assert len(schema.columns) == 2
        assert schema.columns[0]["name"] == "id"
        assert schema.columns[0]["primary_key"] is True

    def test_health_check_success(self, mock_database_agent):
        """Test successful health check."""
        mock_session = Mock()
        mock_database_agent.session_factory.return_value = mock_session
        
        result = mock_database_agent.health_check()
        
        assert result is True
        mock_session.execute.assert_called_once_with("SELECT 1")
        mock_session.close.assert_called_once()

    def test_health_check_failure(self, mock_database_agent):
        """Test health check failure."""
        mock_session = Mock()
        mock_session.execute.side_effect = Exception("Connection failed")
        mock_database_agent.session_factory.return_value = mock_session
        
        result = mock_database_agent.health_check()
        
        assert result is False

    def test_update_agent_status_success(self, mock_database_agent):
        """Test successful agent status update."""
        # Mock session and query
        mock_session = Mock()
        mock_agent = Mock()
        mock_agent.agent_id = "agent_001"
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_agent
        mock_database_agent.session_factory.return_value = mock_session
        
        with patch('src.agents.database_agent.AgentModel'):
            result = mock_database_agent.update_agent_status(
                agent_id="agent_001",
                status="working",
                current_task_id="task_001"
            )
            
            assert result.success is True
            assert result.data['agent_id'] == "agent_001"
            assert result.data['status'] == "working"
            
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_update_agent_status_agent_not_found(self, mock_database_agent):
        """Test agent status update when agent is not found."""
        # Mock session with no agent found
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_database_agent.session_factory.return_value = mock_session
        
        with patch('src.agents.database_agent.AgentModel'):
            result = mock_database_agent.update_agent_status(
                agent_id="nonexistent_agent",
                status="working"
            )
            
            assert result.success is False
            assert "not found" in result.error
            
            mock_session.close.assert_called_once()

    def test_execute_query_success(self, mock_database_agent):
        """Test successful query execution."""
        # Mock session
        mock_session = Mock()
        mock_result = Mock()
        mock_result.fetchall.return_value = [{"id": 1, "name": "test"}]
        mock_session.execute.return_value = mock_result
        mock_database_agent.session_factory.return_value = mock_session
        
        result = mock_database_agent.execute_query("SELECT * FROM users")
        
        assert result.success is True
        assert result.data == [{"id": 1, "name": "test"}]
        
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    def test_execute_query_failure(self, mock_database_agent):
        """Test query execution failure."""
        # Mock session that raises an exception
        mock_session = Mock()
        mock_session.execute.side_effect = Exception("Query error")
        mock_database_agent.session_factory.return_value = mock_session
        
        result = mock_database_agent.execute_query("INVALID SQL")
        
        assert result.success is False
        assert "Query error" in result.error
        
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])