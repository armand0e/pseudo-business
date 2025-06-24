import os  # Added missing import for cleanup operations
import logging
import unittest
from unittest.mock import patch, MagicMock
from src.infrastructure.logging_system import LoggingSystem, RemoteLoggingHandler, LogFilter

class TestLoggingSystem(unittest.TestCase):
    def setUp(self):
        self.logging_system = LoggingSystem()

    def test_setup_logging(self):
        # Test basic logging setup
        self.logging_system.setup_logging(
            log_level='DEBUG',
            log_file='test.log',
            api_endpoint=None
        )
        self.assertEqual(self.logging_system.logger.level, logging.DEBUG)
        self.assertIsNotNone(self.logging_system.file_handler)
        self.assertIsNotNone(self.logging_system.console_handler)

    def test_setup_api_handler(self):
        # Test API handler setup
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            self.logging_system.setup_logging(
                log_level='INFO',
                log_file='test.log',
                api_endpoint='http://example.com/log'
            )
            self.assertIsNotNone(self.logging_system.api_handler)
            # Force a log message to test API handler
            self.logging_system.logger.info("Test message")
            # Verify that API handler was created (not necessarily called immediately)
            self.assertEqual(type(self.logging_system.api_handler).__name__, 'RemoteLoggingHandler')

    def test_error_handler_decorator(self):
        # Test error handling decorator
        # First setup logging
        self.logging_system.setup_logging(
            log_level='INFO',
            log_file='test_errors.log'
        )
        
        @self.logging_system.error_handler
        def test_function():
            raise ValueError("Test error")

        with self.assertRaises(ValueError):
            test_function()

        # Verify that the error was logged
        with open('test_errors.log', 'r') as f:
            content = f.read()
            self.assertIn("Test error", content)

    def test_remote_logging_handler(self):
        # Test remote logging handler
        handler = RemoteLoggingHandler('http://example.com/log')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )

        with patch('requests.post') as mock_post:
            handler.emit(record)
            mock_post.assert_called()

    def test_log_filter(self):
        # Test log filter
        filter = LogFilter([logging.INFO, logging.ERROR])
        record_info = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Info message',
            args=(),
            exc_info=None
        )
        record_error = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=1,
            msg='Error message',
            args=(),
            exc_info=None
        )
        record_debug = logging.LogRecord(
            name='test',
            level=logging.DEBUG,
            pathname='test.py',
            lineno=1,
            msg='Debug message',
            args=(),
            exc_info=None
        )

        self.assertTrue(filter.filter(record_info))
        self.assertTrue(filter.filter(record_error))
        self.assertFalse(filter.filter(record_debug))

    def tearDown(self):
        # Clean up handlers to prevent logging in subsequent tests
        if self.logging_system.logger:
            for handler in self.logging_system.logger.handlers[:]:
                self.logging_system.logger.removeHandler(handler)
        try:
            os.remove('test.log')
            os.remove('test_errors.log')
            os.remove('api_logging_fallback.log')
        except:
            pass

if __name__ == '__main__':
    unittest.main()