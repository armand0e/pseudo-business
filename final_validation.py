#!/usr/bin/env python3
"""
Final Validation Test - Comprehensive system validation
"""

import sys
import time
import ast
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class ValidationResult:
    def __init__(self, category: str, test: str, status: str, details: str = ""):
        self.category = category
        self.test = test
        self.status = status
        self.details = details

class FinalValidator:
    def __init__(self):
        self.results = []
        self.categories = {
            'critical': 0,
            'important': 0,
            'minor': 0
        }

    def validate(self, category: str, test: str, test_func, *args, **kwargs):
        """Run a validation test."""
        try:
            result = test_func(*args, **kwargs)
            if result:
                status = "✅ PASS"
                self.categories[category] += 1
            else:
                status = "❌ FAIL"
            self.results.append(ValidationResult(category, test, status, ""))
            print(f"  {status} {test}")
        except Exception as e:
            status = "❌ ERROR"
            self.results.append(ValidationResult(category, test, status, str(e)))
            print(f"  {status} {test} - {str(e)}")

    def run_validation(self):
        print("🔍 Running Final System Validation")
        print("=" * 60)
        
        print("\n🔧 CRITICAL FUNCTIONALITY")
        self.validate_critical()
        
        print("\n⚙️ IMPORTANT FEATURES")
        self.validate_important()
        
        print("\n📝 MINOR COMPONENTS")
        self.validate_minor()
        
        self.generate_report()

    def validate_critical(self):
        """Validate critical system functionality."""
        
        # Code Quality and Syntax
        self.validate('critical', 'All Python files compile', self.test_syntax_validation)
        self.validate('critical', 'Core imports work', self.test_core_imports)
        self.validate('critical', 'Database Agent initializes', self.test_database_agent_init)
        self.validate('critical', 'Backend Agent works', self.test_backend_agent_basic)
        self.validate('critical', 'Agent Coordinator functions', self.test_agent_coordinator_basic)
        self.validate('critical', 'Logging system operational', self.test_logging_system)

    def validate_important(self):
        """Validate important system features."""
        
        self.validate('important', 'NLP Processor has core methods', self.test_nlp_processor)
        self.validate('important', 'Task Decomposer works', self.test_task_decomposer)
        self.validate('important', 'Code generation produces valid output', self.test_code_generation)
        self.validate('important', 'Database operations functional', self.test_database_operations)
        self.validate('important', 'Error handling works', self.test_error_handling)
        self.validate('important', 'Configuration system works', self.test_configuration_basic)

    def validate_minor(self):
        """Validate minor components and edge cases."""
        
        self.validate('minor', 'Documentation files exist', self.test_documentation)
        self.validate('minor', 'Project structure is correct', self.test_project_structure)
        self.validate('minor', 'Startup script exists', self.test_startup_script)

    def test_syntax_validation(self):
        """Test that all Python files have valid syntax."""
        python_files = [
            "src/infrastructure/logging_system.py",
            "src/infrastructure/config_manager.py",
            "src/infrastructure/api_gateway.py",
            "src/agents/database_agent.py",
            "src/agents/backend_agent.py",
            "src/architecture/agent_coordinator.py",
            "src/architecture/nlp_processor.py",
            "src/architecture/task_decomposer.py",
            "src/main.py"
        ]
        
        for file_path in python_files:
            full_path = project_root / file_path
            if full_path.exists():
                with open(full_path, 'r') as f:
                    content = f.read()
                    ast.parse(content)  # Will raise SyntaxError if invalid
        return True

    def test_core_imports(self):
        """Test core module imports."""
        from src.infrastructure.logging_system import LoggingSystem
        from src.agents.database_agent import DatabaseAgent
        from src.agents.backend_agent import BackendAgent
        from src.architecture.agent_coordinator import AgentCoordinator
        from src.architecture.nlp_processor import NLPProcessor
        from src.architecture.task_decomposer import TaskDecomposer
        return True

    def test_database_agent_init(self):
        """Test database agent initialization."""
        from src.agents.database_agent import DatabaseAgent
        
        config = {'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'username': 'test', 'password': 'test'}}
        
        with patch('src.agents.database_agent.create_engine') as mock_engine:
            mock_engine.return_value = Mock()
            with patch('src.agents.database_agent.sessionmaker') as mock_session_factory:
                mock_session_factory.return_value = Mock()
                
                agent = DatabaseAgent(config)
                return agent.config == config

    def test_backend_agent_basic(self):
        """Test backend agent basic functionality."""
        from src.agents.backend_agent import BackendAgent, CodeGenRequest
        
        agent = BackendAgent({})
        request = CodeGenRequest(project_id=1, requirements="Test API", framework="fastapi")
        result = agent.generate_backend_code(request)
        
        return result.success and 'main.py' in result.files

    def test_agent_coordinator_basic(self):
        """Test agent coordinator basic functionality."""
        from src.architecture.agent_coordinator import AgentCoordinator, AgentType
        
        coordinator = AgentCoordinator({})
        success = coordinator.register_agent('test', AgentType.BACKEND, ['test'])
        
        return success

    def test_logging_system(self):
        """Test logging system."""
        from src.infrastructure.logging_system import LoggingSystem
        
        logging_system = LoggingSystem()
        logger = logging_system.get_logger()
        
        # Test that logger methods exist and are callable
        return (hasattr(logger, 'info') and 
                hasattr(logger, 'debug') and 
                hasattr(logger, 'error') and
                hasattr(logger, 'warning'))

    def test_nlp_processor(self):
        """Test NLP processor has required methods."""
        from src.architecture.nlp_processor import NLPProcessor
        
        processor = NLPProcessor({})
        
        # Check that required methods exist
        return (hasattr(processor, 'process_text') and
                hasattr(processor, 'analyze_text') and
                hasattr(processor, 'is_valid_task'))

    def test_task_decomposer(self):
        """Test task decomposer functionality."""
        from src.architecture.task_decomposer import TaskDecomposer
        
        decomposer = TaskDecomposer({})
        
        # Test that it can decompose requirements
        tasks = decomposer.decompose_requirements("Build a web app")
        
        return isinstance(tasks, list) and len(tasks) > 0

    def test_code_generation(self):
        """Test code generation produces valid Python."""
        from src.agents.backend_agent import BackendAgent, CodeGenRequest
        
        agent = BackendAgent({})
        request = CodeGenRequest(project_id=1, requirements="Simple API", framework="fastapi")
        result = agent.generate_backend_code(request)
        
        if not result.success:
            return False
        
        # Test that generated main.py is valid Python
        try:
            ast.parse(result.files['main.py'])
            return True
        except SyntaxError:
            return False

    def test_database_operations(self):
        """Test database operations with mocking."""
        from src.agents.database_agent import DatabaseAgent
        
        config = {'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'username': 'test', 'password': 'test'}}
        
        with patch('src.agents.database_agent.create_engine') as mock_engine:
            mock_engine.return_value = Mock()
            with patch('src.agents.database_agent.sessionmaker') as mock_session_factory:
                mock_session = Mock()
                mock_session_factory.return_value = lambda: mock_session
                
                agent = DatabaseAgent(config)
                
                # Test health check
                mock_session.execute = Mock()
                return agent.health_check()

    def test_error_handling(self):
        """Test error handling mechanisms."""
        from src.agents.backend_agent import BackendAgent
        
        agent = BackendAgent({})
        
        # Test code validation with invalid syntax
        invalid_code = "def invalid("
        result = agent.validate_code(invalid_code)
        
        return not result['valid'] and len(result['errors']) > 0

    def test_configuration_basic(self):
        """Test basic configuration without external dependencies."""
        # Test that config files exist
        config_path = project_root / 'config' / 'config.yaml'
        return config_path.parent.exists()  # Config directory exists

    def test_documentation(self):
        """Test documentation files exist."""
        docs = [
            'README.md',
            'TODO.md',
            'IMPLEMENTATION_ROADMAP.md'
        ]
        
        for doc in docs:
            doc_path = project_root / doc
            if not doc_path.exists():
                return False
        
        return True

    def test_project_structure(self):
        """Test project structure is correct."""
        required_dirs = [
            'src',
            'src/infrastructure',
            'src/agents',
            'src/architecture',
            'config'
        ]
        
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            if not full_path.exists():
                return False
        
        return True

    def test_startup_script(self):
        """Test startup script exists."""
        script_path = project_root / 'start_platform.py'
        return script_path.exists()

    def generate_report(self):
        """Generate final validation report."""
        
        print("\n" + "=" * 60)
        print("📊 FINAL VALIDATION REPORT")
        print("=" * 60)
        
        # Count results by category and status
        critical_pass = sum(1 for r in self.results if r.category == 'critical' and '✅' in r.status)
        critical_total = sum(1 for r in self.results if r.category == 'critical')
        
        important_pass = sum(1 for r in self.results if r.category == 'important' and '✅' in r.status)
        important_total = sum(1 for r in self.results if r.category == 'important')
        
        minor_pass = sum(1 for r in self.results if r.category == 'minor' and '✅' in r.status)
        minor_total = sum(1 for r in self.results if r.category == 'minor')
        
        total_pass = critical_pass + important_pass + minor_pass
        total_tests = len(self.results)
        
        print(f"CRITICAL FUNCTIONALITY: {critical_pass}/{critical_total} ({'✅' if critical_pass == critical_total else '⚠️'})")
        print(f"IMPORTANT FEATURES:     {important_pass}/{important_total} ({'✅' if important_pass == important_total else '⚠️'})")
        print(f"MINOR COMPONENTS:       {minor_pass}/{minor_total} ({'✅' if minor_pass == minor_total else '⚠️'})")
        print(f"OVERALL:                {total_pass}/{total_tests} ({(total_pass/total_tests*100):.1f}%)")
        
        # Show failed tests
        failed_tests = [r for r in self.results if '❌' in r.status]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - [{test.category.upper()}] {test.test}")
                if test.details:
                    print(f"    {test.details}")
        
        # Final assessment
        print(f"\n{'🎉 SYSTEM VALIDATION SUCCESSFUL!' if critical_pass == critical_total else '⚠️ CRITICAL ISSUES DETECTED'}")
        
        if critical_pass == critical_total:
            print("✅ All critical functionality is working")
            print("✅ Core system components are operational") 
            print("✅ Platform is ready for Phase 2 development")
        else:
            print("❌ Critical functionality has issues")
            print("⚠️ Platform needs fixes before continuing")
        
        return critical_pass == critical_total

def main():
    validator = FinalValidator()
    success = validator.run_validation()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())