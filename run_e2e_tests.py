#!/usr/bin/env python3
"""
End-to-End Test Suite for Agentic AI Development Platform

This script runs comprehensive tests to validate all components are working correctly.
"""

import os
import sys
import time
import json
import asyncio
import traceback
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TestResult:
    """Test result container."""
    def __init__(self, test_name: str, success: bool, message: str = "", execution_time: float = 0.0):
        self.test_name = test_name
        self.success = success
        self.message = message
        self.execution_time = execution_time

class E2ETestSuite:
    """End-to-end test suite for the platform."""

    def __init__(self):
        self.results: List[TestResult] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Run a single test and record the result."""
        print(f"🧪 Running: {test_name}")
        start_time = time.time()
        
        try:
            test_func(*args, **kwargs)
            execution_time = time.time() - start_time
            result = TestResult(test_name, True, "✅ PASSED", execution_time)
            self.passed_tests += 1
            print(f"   ✅ PASSED ({execution_time:.3f}s)")
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"❌ FAILED: {str(e)}"
            result = TestResult(test_name, False, error_msg, execution_time)
            self.failed_tests += 1
            print(f"   ❌ FAILED ({execution_time:.3f}s): {str(e)}")
            
        self.results.append(result)
        self.total_tests += 1
        return result

    def test_imports(self):
        """Test that all modules can be imported."""
        print("\n📦 Testing Module Imports")
        
        # Core infrastructure imports
        self.run_test("Import LoggingSystem", self._test_import, "src.infrastructure.logging_system", "LoggingSystem")
        self.run_test("Import ConfigManager", self._test_import, "src.infrastructure.config_manager", "ConfigManager")
        self.run_test("Import APIGateway", self._test_import, "src.infrastructure.api_gateway", "APIGateway")
        
        # Agent imports
        self.run_test("Import DatabaseAgent", self._test_import, "src.agents.database_agent", "DatabaseAgent")
        self.run_test("Import BackendAgent", self._test_import, "src.agents.backend_agent", "BackendAgent")
        
        # Architecture imports
        self.run_test("Import AgentCoordinator", self._test_import, "src.architecture.agent_coordinator", "AgentCoordinator")
        self.run_test("Import NLPProcessor", self._test_import, "src.architecture.nlp_processor", "NLPProcessor")
        self.run_test("Import TaskDecomposer", self._test_import, "src.architecture.task_decomposer", "TaskDecomposer")

    def _test_import(self, module_name: str, class_name: str):
        """Test importing a specific module and class."""
        from importlib import import_module
        module = import_module(module_name)
        getattr(module, class_name)

    def test_configuration(self):
        """Test configuration system."""
        print("\n⚙️ Testing Configuration System")
        
        self.run_test("ConfigManager Initialization", self._test_config_initialization)
        self.run_test("Default Configuration", self._test_default_config)
        self.run_test("Configuration Access", self._test_config_access)
        self.run_test("Environment Override", self._test_env_override)

    def _test_config_initialization(self):
        """Test configuration manager initialization."""
        from src.infrastructure.config_manager import ConfigManager
        
        # Test with no config file
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager()
            assert config_manager.config is not None
            assert isinstance(config_manager.config, dict)

    def _test_default_config(self):
        """Test default configuration values."""
        from src.infrastructure.config_manager import ConfigManager
        
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # Verify required sections
            required_sections = ['database', 'api_gateway', 'master_orchestrator', 'agents', 'logging']
            for section in required_sections:
                assert section in config, f"Missing configuration section: {section}"

    def _test_config_access(self):
        """Test configuration access methods."""
        from src.infrastructure.config_manager import ConfigManager
        
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager()
            
            # Test getter methods
            db_config = config_manager.get_database_config()
            assert 'host' in db_config
            assert 'port' in db_config
            
            # Test dot notation
            host = config_manager.get('database.host')
            assert host is not None
            
            # Test non-existent key
            non_existent = config_manager.get('non.existent.key', 'default')
            assert non_existent == 'default'

    def _test_env_override(self):
        """Test environment variable overrides."""
        from src.infrastructure.config_manager import ConfigManager
        
        with patch('os.path.exists', return_value=False):
            with patch.dict(os.environ, {'DATABASE_HOST': 'test-host', 'DATABASE_PORT': '3306'}):
                config_manager = ConfigManager()
                
                assert config_manager.get('database.host') == 'test-host'
                assert config_manager.get('database.port') == 3306

    def test_database_agent(self):
        """Test database agent functionality."""
        print("\n🗄️ Testing Database Agent")
        
        self.run_test("DatabaseAgent Initialization", self._test_database_agent_init)
        self.run_test("Database Models", self._test_database_models)
        self.run_test("Connection String Building", self._test_connection_string)
        self.run_test("Schema Generation", self._test_schema_generation)

    def _test_database_agent_init(self):
        """Test database agent initialization."""
        from src.agents.database_agent import DatabaseAgent
        
        config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db',
                'username': 'test_user',
                'password': 'test_pass'
            }
        }
        
        # Mock database connection to avoid actual DB requirement
        with patch('src.agents.database_agent.create_engine') as mock_engine:
            mock_engine.return_value = Mock()
            with patch('src.agents.database_agent.sessionmaker') as mock_session_factory:
                mock_session_factory.return_value = Mock()
                
                agent = DatabaseAgent(config)
                assert agent.config == config
                assert agent.db_config == config['database']

    def _test_database_models(self):
        """Test database model definitions."""
        from src.agents.database_agent import ProjectModel, TaskModel, AgentModel, Base
        
        # Verify models inherit from Base
        assert issubclass(ProjectModel, Base)
        assert issubclass(TaskModel, Base)
        assert issubclass(AgentModel, Base)
        
        # Verify table names
        assert ProjectModel.__tablename__ == 'projects'
        assert TaskModel.__tablename__ == 'tasks'
        assert AgentModel.__tablename__ == 'agents'

    def _test_connection_string(self):
        """Test database connection string building."""
        from src.agents.database_agent import DatabaseAgent
        
        config = {
            'database': {
                'host': 'test-host',
                'port': 3306,
                'database': 'test_db',
                'username': 'user',
                'password': 'pass'
            }
        }
        
        with patch('src.agents.database_agent.create_engine'):
            with patch('src.agents.database_agent.sessionmaker'):
                agent = DatabaseAgent(config)
                expected = "postgresql://user:pass@test-host:3306/test_db"
                assert agent.connection_string == expected

    def _test_schema_generation(self):
        """Test database schema generation."""
        from src.agents.database_agent import DatabaseAgent, DatabaseSchema
        
        config = {'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'username': 'test', 'password': 'test'}}
        
        with patch('src.agents.database_agent.create_engine'):
            with patch('src.agents.database_agent.sessionmaker'):
                agent = DatabaseAgent(config)
                
                columns = [
                    {"name": "id", "type": "int", "primary_key": True},
                    {"name": "name", "type": "str", "nullable": False}
                ]
                
                schema = agent.generate_schema("test_table", columns)
                assert isinstance(schema, DatabaseSchema)
                assert schema.table_name == "test_table"
                assert len(schema.columns) == 2

    def test_api_gateway(self):
        """Test API Gateway functionality."""
        print("\n🌐 Testing API Gateway")
        
        self.run_test("APIGateway Initialization", self._test_api_gateway_init)
        self.run_test("FastAPI App Creation", self._test_fastapi_app)
        self.run_test("JWT Token Generation", self._test_jwt_token)
        self.run_test("Rate Limiting", self._test_rate_limiting)
        self.run_test("Authentication", self._test_authentication)

    def _test_api_gateway_init(self):
        """Test API Gateway initialization."""
        from src.infrastructure.api_gateway import APIGateway
        
        config = {
            'jwt_secret': 'test-secret',
            'jwt_algorithm': 'HS256',
            'jwt_expiry_hours': 24,
            'rate_limiting': {'max_requests_per_minute': 100},
            'cors': {'allowed_origins': ['*']},
            'default_users': {'testuser': 'testpass'}
        }
        
        gateway = APIGateway(config)
        assert gateway.config == config
        assert gateway.jwt_secret == 'test-secret'
        assert gateway.max_requests_per_minute == 100

    def _test_fastapi_app(self):
        """Test FastAPI application creation."""
        from src.infrastructure.api_gateway import APIGateway
        from fastapi import FastAPI
        
        config = {
            'jwt_secret': 'test-secret',
            'default_users': {'testuser': 'testpass'}
        }
        
        gateway = APIGateway(config)
        app = gateway.get_app()
        assert isinstance(app, FastAPI)

    def _test_jwt_token(self):
        """Test JWT token generation and validation."""
        from src.infrastructure.api_gateway import APIGateway
        import jwt
        
        config = {
            'jwt_secret': 'test-secret',
            'jwt_algorithm': 'HS256',
            'jwt_expiry_hours': 24,
            'default_users': {'testuser': 'testpass'}
        }
        
        gateway = APIGateway(config)
        token = gateway._generate_jwt_token('testuser')
        
        # Verify token can be decoded
        payload = jwt.decode(token, config['jwt_secret'], algorithms=[config['jwt_algorithm']])
        assert payload['sub'] == 'testuser'

    def _test_rate_limiting(self):
        """Test rate limiting functionality."""
        from src.infrastructure.api_gateway import APIGateway
        
        config = {
            'rate_limiting': {'max_requests_per_minute': 5},
            'default_users': {'testuser': 'testpass'}
        }
        
        gateway = APIGateway(config)
        client_ip = '127.0.0.1'
        
        # First requests should pass
        for _ in range(5):
            assert gateway._check_rate_limit(client_ip) is True
        
        # Next request should be blocked
        assert gateway._check_rate_limit(client_ip) is False

    def _test_authentication(self):
        """Test user authentication."""
        from src.infrastructure.api_gateway import APIGateway
        
        config = {
            'default_users': {'testuser': 'testpass', 'admin': 'admin123'}
        }
        
        gateway = APIGateway(config)
        
        # Test valid credentials
        assert gateway._authenticate_user('testuser', 'testpass') is True
        assert gateway._authenticate_user('admin', 'admin123') is True
        
        # Test invalid credentials
        assert gateway._authenticate_user('testuser', 'wrongpass') is False
        assert gateway._authenticate_user('nonexistent', 'password') is False

    def test_backend_agent(self):
        """Test Backend Agent functionality."""
        print("\n⚙️ Testing Backend Agent")
        
        self.run_test("BackendAgent Initialization", self._test_backend_agent_init)
        self.run_test("Requirements Parsing", self._test_requirements_parsing)
        self.run_test("Code Generation", self._test_code_generation)
        self.run_test("Code Validation", self._test_code_validation)

    def _test_backend_agent_init(self):
        """Test backend agent initialization."""
        from src.agents.backend_agent import BackendAgent
        
        config = {}
        agent = BackendAgent(config)
        
        assert agent.config == config
        assert len(agent.capabilities) > 0
        assert 'fastapi_generation' in agent.capabilities

    def _test_requirements_parsing(self):
        """Test requirements parsing."""
        from src.agents.backend_agent import BackendAgent
        
        agent = BackendAgent({})
        requirements = "Create a user management API with authentication"
        parsed = agent._parse_requirements(requirements)
        
        assert isinstance(parsed, dict)
        assert 'models' in parsed
        assert 'endpoints' in parsed
        assert 'features' in parsed

    def _test_code_generation(self):
        """Test code generation functionality."""
        from src.agents.backend_agent import BackendAgent, CodeGenRequest
        
        agent = BackendAgent({})
        request = CodeGenRequest(
            project_id=1,
            requirements="Create a simple API",
            framework="fastapi"
        )
        
        result = agent.generate_backend_code(request)
        
        assert result.success is True
        assert isinstance(result.files, dict)
        assert 'main.py' in result.files
        assert 'requirements.txt' in result.files

    def _test_code_validation(self):
        """Test code validation."""
        from src.agents.backend_agent import BackendAgent
        
        agent = BackendAgent({})
        
        # Test valid Python code
        valid_code = "def hello():\n    return 'Hello, World!'"
        result = agent.validate_code(valid_code)
        assert result['valid'] is True
        
        # Test invalid Python code
        invalid_code = "def hello(\n    return 'Hello, World!'"
        result = agent.validate_code(invalid_code)
        assert result['valid'] is False

    def test_component_integration(self):
        """Test integration between components."""
        print("\n🔗 Testing Component Integration")
        
        self.run_test("Agent Coordinator Integration", self._test_agent_coordinator)
        self.run_test("NLP Processor Integration", self._test_nlp_processor)
        self.run_test("Task Decomposer Integration", self._test_task_decomposer)

    def _test_agent_coordinator(self):
        """Test agent coordinator functionality."""
        from src.architecture.agent_coordinator import AgentCoordinator, AgentType, Agent, Task
        
        config = {
            'timeouts': {'backend_timeout': 300},
            'concurrency_limits': {'backend': 5}
        }
        
        coordinator = AgentCoordinator(config)
        
        # Test agent registration
        success = coordinator.register_agent('test_agent', AgentType.BACKEND, ['fastapi'])
        assert success is True
        
        # Test duplicate registration
        success = coordinator.register_agent('test_agent', AgentType.BACKEND, ['fastapi'])
        assert success is False
        
        # Test task creation
        task = Task(
            task_id='test_task',
            description='Test task',
            agent_type=AgentType.BACKEND,
            priority=1
        )
        
        success = coordinator.add_task(task)
        assert success is True

    def _test_nlp_processor(self):
        """Test NLP processor functionality."""
        from src.architecture.nlp_processor import NLPProcessor
        
        # Mock spacy to avoid dependency issues
        with patch('src.architecture.nlp_processor.spacy.load') as mock_spacy:
            mock_nlp = Mock()
            mock_doc = Mock()
            mock_doc.ents = []
            mock_nlp.return_value = mock_doc
            mock_spacy.return_value = mock_nlp
            
            config = {}
            processor = NLPProcessor(config)
            
            # Test text processing
            result = processor.process_text("Create a user management system")
            assert result is not None
            assert 'entities' in result

    def _test_task_decomposer(self):
        """Test task decomposer functionality."""
        from src.architecture.task_decomposer import TaskDecomposer
        
        config = {}
        decomposer = TaskDecomposer(config)
        
        # Test task decomposition
        requirements = "Build a web application with user authentication"
        tasks = decomposer.decompose_requirements(requirements)
        
        assert isinstance(tasks, list)
        assert len(tasks) > 0

    def test_main_application(self):
        """Test main application functionality."""
        print("\n🚀 Testing Main Application")
        
        self.run_test("Main Application Import", self._test_main_import)
        self.run_test("Platform Initialization", self._test_platform_init)

    def _test_main_import(self):
        """Test main application import."""
        from src.main import AgendicPlatform
        assert AgendicPlatform is not None

    def _test_platform_init(self):
        """Test platform initialization."""
        from src.main import AgendicPlatform
        
        # Mock external dependencies
        with patch('src.main.ConfigManager'):
            with patch('src.main.DatabaseAgent'):
                with patch('src.main.APIGateway'):
                    platform = AgendicPlatform()
                    assert platform is not None

    def run_all_tests(self):
        """Run all test suites."""
        print("🧪 Starting End-to-End Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run test suites
        self.test_imports()
        self.test_configuration()
        self.test_database_agent()
        self.test_api_gateway()
        self.test_backend_agent()
        self.test_component_integration()
        self.test_main_application()
        
        total_time = time.time() - start_time
        
        # Generate report
        self.generate_report(total_time)

    def generate_report(self, total_time: float):
        """Generate test report."""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ✅")
        print(f"Failed: {self.failed_tests} ❌")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print(f"Total Time: {total_time:.3f}s")
        
        if self.failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.test_name}: {result.message}")
        
        print(f"\n{'🎉 ALL TESTS PASSED!' if self.failed_tests == 0 else '⚠️ SOME TESTS FAILED'}")
        
        # Save detailed report
        self.save_detailed_report()

    def save_detailed_report(self):
        """Save detailed test report to file."""
        report_data = {
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'success_rate': (self.passed_tests/self.total_tests*100) if self.total_tests > 0 else 0,
            'tests': [
                {
                    'name': result.test_name,
                    'success': result.success,
                    'message': result.message,
                    'execution_time': result.execution_time
                }
                for result in self.results
            ]
        }
        
        report_file = project_root / 'test_report.json'
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")

def main():
    """Main function to run the test suite."""
    suite = E2ETestSuite()
    suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if suite.failed_tests == 0 else 1)

if __name__ == "__main__":
    main()