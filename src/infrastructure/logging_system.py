import logging
import sys
from functools import wraps
from typing import Callable, Any
import requests
import os

class LoggingSystem:
    def __init__(self):
        self.logger = None
        self.file_handler = None
        self.api_handler = None
        self.console_handler = None

    def setup_logging(self,
                     log_level: str = 'INFO',
                     log_file: str = 'app.log',
                     api_endpoint: str = None,
                     max_bytes: int = 10485760,  # 10MB
                     backup_count: int = 3):
        """
        Set up comprehensive logging configuration.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to the log file
            api_endpoint: API endpoint for remote logging
            max_bytes: Maximum bytes before rotation
            backup_count: Number of backup files to keep
        """
        self.logger = logging.getLogger('agent')
        self.logger.setLevel(log_level)

        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Set up file handler with rotation
        self.file_handler = logging.FileHandler(log_file, mode='a')
        self.file_handler.setLevel(log_level)
        self.file_handler.setFormatter(formatter)

        # Set up console handler
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(log_level)
        self.console_handler.setFormatter(formatter)

        # Add handlers if they're not already present
        if not self.logger.handlers:
            self.logger.addHandler(self.file_handler)
            self.logger.addHandler(self.console_handler)

            # Set up API handler if endpoint provided
            if api_endpoint:
                self.setup_api_handler(api_endpoint, max_bytes, backup_count)

    def setup_api_handler(self, api_endpoint: str, max_bytes: int = 10485760, backup_count: int = 3):
        """
        Set up API handler for remote logging.

        Args:
            api_endpoint: API endpoint for remote logging
            max_bytes: Maximum bytes before rotation
            backup_count: Number of backup files to keep
        """
        self.api_handler = RemoteLoggingHandler(api_endpoint, max_bytes=max_bytes)
        self.api_handler.setLevel(logging.INFO)
        self.api_handler.setFormatter(self.file_handler.getFormatter())
        self.logger.addHandler(self.api_handler)

    def error_handler(self, func: Callable) -> Callable:
        """
        Decorator to handle errors in agent methods.

        Args:
            func: The function to decorate

        Returns:
            Wrapped function with error handling
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                # Implement specific error handling policies here
                raise
        return wrapper

    def get_logger(self) -> logging.Logger:
        """
        Get the configured logger instance.

        Returns:
            Configured logger instance
        """
        if self.logger is None:
            self.setup_logging()
        return self.logger

class RemoteLoggingHandler(logging.Handler):
    """
    Custom handler for sending logs to a remote API.
    """

    def __init__(self, api_endpoint: str, max_bytes: int = 10485760):
        super().__init__()
        self.api_endpoint = api_endpoint
        self.max_bytes = max_bytes

    def emit(self, record: logging.LogRecord) -> None:
        """
        Send log record to remote API.
        """
        try:
            log_entry = self.format(record)
            response = requests.post(
                self.api_endpoint,
                json={'log': log_entry},
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            # Fall back to file logging if API is unavailable
            fallback_handler = logging.FileHandler('api_logging_fallback.log')
            fallback_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            fallback_handler.handle(record)
            self.handleError(record)

class LogFilter(logging.Filter):
    """
    Custom filter for log messages.
    """

    def __init__(self, allowed_levels: list = None):
        super().__init__()
        self.allowed_levels = allowed_levels or [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records based on level.
        """
        return record.levelno in self.allowed_levels