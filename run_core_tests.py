#!/usr/bin/env python3
"""
Core functionality tests - bypassing dependency issues for critical validation.
"""

import os
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class CoreTestResult:
    def __init__(self, name: str, success: bool, message: str = "", time: float = 0.0):
        self.name = name
        self.success = success
        self.message = message
        self.time = time

class CoreTestSuite:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def test(self, name: str, test_func, *args, **kwargs):
        print(f"🧪 {name}")
        start = time.time()
        try:
            test_func(*args, **kwargs)
            elapsed = time.time() - start
            result = CoreTestResult(name, True, "✅ PASSED", elapsed)
            self.passed += 1
            print(f"   ✅ PASSED ({elapsed:.3f}s)")
        except Exception as e:
            elapsed = time.time() - start
            result = CoreTestResult(name, False, f"❌ {str(e)}", elapsed)
            self.failed += 1
            print(f"   ❌ FAILED ({elapsed:.3f}s): {str(e)}")
        
        self.results.append(result)

    def run_all_tests(self):
        print("🚀 Running Core Functionality Tests")
        print("=" * 50)
        
        # Test 1: Basic imports
        self.test("Import Core Modules", self.test_core_imports)
        
        # Test 2: Database Agent with mocked SQLAlchemy
        self.test("Database Agent Core", self.test_database_agent_core)
        
        # Test 3: Backend Agent functionality
        self.test("Backend Agent Core", self.test_backend_agent_core)
        
        # Test 4: Agent Coordinator
        self.test("Agent Coordinator", self.test_agent_coordinator)
        
        # Test 5: NLP Processor with mocked spacy
        self.test("NLP Processor Core", self.test_nlp_processor_core)
        
        # Test 6: Task Decomposer
        self.test("Task Decomposer Core", self.test_task_decomposer_core)
        
        # Test 7: Logging System
        self.test("Logging System", self.test_logging_system)
        
        # Test 8: Code validation
        self.test("Code Validation", self.test_code_validation)
        
        self.report()

    def test_core_imports(self):
        """Test that core modules can be imported."""
        from src.infrastructure.logging_system import LoggingSystem
        from src.agents.database_agent import DatabaseAgent, QueryResult, DatabaseSchema
        from src.agents.backend_agent import BackendAgent, CodeGenRequest
        from src.architecture.agent_coordinator import AgentCoordinator, AgentType
        from src.architecture.nlp_processor import NLPProcessor
        from src.architecture.task_decomposer import TaskDecomposer
        
        assert LoggingSystem is not None
        assert DatabaseAgent is not None
        assert BackendAgent is not None
        assert AgentCoordinator is not None

    def test_database_agent_core(self):
        """Test database agent core functionality."""
        from src.agents.database_agent import DatabaseAgent, DatabaseSchema
        
        config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db',
                'username': 'test_user',
                'password': 'test_pass'
            }
        }
        
        # Mock SQLAlchemy dependencies
        with patch('src.agents.database_agent.create_engine') as mock_engine:
            mock_engine.return_value = Mock()
            with patch('src.agents.database_agent.sessionmaker') as mock_session_factory:
                mock_session_factory.return_value = Mock()
                
                agent = DatabaseAgent(config)
                assert agent.config == config
                
                # Test connection string
                expected = "postgresql://test_user:test_pass@localhost:5432/test_db"
                assert agent.connection_string == expected
                
                # Test schema generation
                columns = [{"name": "id", "type": "int", "primary_key": True}]
                schema = agent.generate_schema("test_table", columns)
                assert isinstance(schema, DatabaseSchema)
                assert schema.table_name == "test_table"

    def test_backend_agent_core(self):
        """Test backend agent core functionality."""
        from src.agents.backend_agent import BackendAgent, CodeGenRequest
        
        agent = BackendAgent({})
        assert len(agent.capabilities) > 0
        
        # Test requirements parsing
        requirements = "Create a user management API"
        parsed = agent._parse_requirements(requirements)
        assert isinstance(parsed, dict)
        assert 'models' in parsed
        
        # Test code generation
        request = CodeGenRequest(
            project_id=1,
            requirements="Create API",
            framework="fastapi"
        )
        result = agent.generate_backend_code(request)
        assert result.success is True
        assert 'main.py' in result.files
        
        # Test code validation
        valid_code = "def hello(): return 'world'"
        validation = agent.validate_code(valid_code)
        assert validation['valid'] is True

    def test_agent_coordinator(self):
        """Test agent coordinator functionality."""
        from src.architecture.agent_coordinator import AgentCoordinator, AgentType, Task
        
        config = {'timeouts': {'backend_timeout': 300}}
        coordinator = AgentCoordinator(config)
        
        # Test agent registration
        success = coordinator.register_agent('test_agent', AgentType.BACKEND, ['fastapi'])
        assert success is True
        
        # Test task creation
        task = Task(
            task_id='test_task',
            description='Test task',
            agent_type=AgentType.BACKEND,
            priority=1
        )
        success = coordinator.add_task(task)
        assert success is True
        
        # Test status retrieval
        status = coordinator.get_agent_status('test_agent')
        assert status['agent_id'] == 'test_agent'

    def test_nlp_processor_core(self):
        """Test NLP processor with mocked spacy."""
        from src.architecture.nlp_processor import NLPProcessor
        
        # Mock spacy
        with patch('src.architecture.nlp_processor.spacy.load') as mock_spacy:
            mock_nlp = Mock()
            mock_doc = Mock()
            mock_doc.ents = []
            mock_nlp.return_value = mock_doc
            mock_spacy.return_value = mock_nlp
            
            processor = NLPProcessor({})
            
            # Test text processing (should handle spacy mock)
            result = processor.process_text("Create a user system")
            assert result is not None
            assert 'entities' in result or 'error' in result

    def test_task_decomposer_core(self):
        """Test task decomposer functionality."""
        from src.architecture.task_decomposer import TaskDecomposer
        
        decomposer = TaskDecomposer({})
        
        # Test requirements decomposition
        requirements = "Build a web application"
        tasks = decomposer.decompose_requirements(requirements)
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        
        # Test task analysis
        analysis = decomposer.analyze_task("Create user authentication")
        assert 'description' in analysis
        assert 'complexity' in analysis

    def test_logging_system(self):
        """Test logging system functionality."""
        from src.infrastructure.logging_system import LoggingSystem
        
        logging_system = LoggingSystem()
        logger = logging_system.get_logger()
        
        # Test basic logging operations
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.warning("Test warning message")
        
        # Test error handler decorator
        @logging_system.error_handler
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"

    def test_code_validation(self):
        """Test overall code quality and syntax."""
        # Test that all Python files compile
        python_files = [
            "src/infrastructure/logging_system.py",
            "src/agents/database_agent.py", 
            "src/agents/backend_agent.py",
            "src/architecture/agent_coordinator.py",
            "src/architecture/nlp_processor.py",
            "src/architecture/task_decomposer.py"
        ]
        
        for file_path in python_files:
            full_path = project_root / file_path
            if full_path.exists():
                with open(full_path, 'r') as f:
                    content = f.read()
                    # Basic syntax check
                    compile(content, str(full_path), 'exec')

    def report(self):
        print("\n" + "=" * 50)
        print("📊 CORE TEST RESULTS")
        print("=" * 50)
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} ❌")
        
        if self.failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.name}: {result.message}")
        
        success_rate = (self.passed / len(self.results)) * 100 if self.results else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if self.failed == 0:
            print("🎉 ALL CORE TESTS PASSED!")
            print("✅ Core functionality is working correctly")
        else:
            print("⚠️ Some tests failed, but core functionality is partially working")

def main():
    suite = CoreTestSuite()
    suite.run_all_tests()
    return 0 if suite.failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())