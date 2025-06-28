"""
Error Handler for centralized error management.

This module provides logging, retry mechanisms, and notification functionality
for handling exceptions that occur during the orchestration process.
"""

import logging
from typing import Dict, Any
from master_orchestrator.constants import DEFAULT_RETRY_CONFIG, TechStackPreferences

class ErrorHandler:
    """
    Centralized error management system for the Master Orchestrator.

    Attributes:
        logger: Python logging instance configured with handlers and formatters.
        retry_config: Configuration for retrying failed operations.
        tech_stack_preferences: Technology stack preferences for the project.
    """

    def __init__(self):
        """Initialize the error handler with logging configuration."""
        self.logger = self._setup_logging()
        self.retry_config = DEFAULT_RETRY_CONFIG
        self.tech_stack_preferences = TechStackPreferences()

    def _setup_logging(self) -> logging.Logger:
        """Set up the logging configuration."""
        logger = logging.getLogger("master_orchestrator")
        logger.setLevel(logging.DEBUG)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Create file handler
        file_handler = logging.FileHandler("orchestrator_errors.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """
        Log an error with contextual information.

        Args:
            error: The exception that occurred
            context: Additional context about the error (e.g., task ID, agent type)
        """
        try:
            error_message = str(error)

            # Add stack trace to debug logs
            self.logger.debug(f"Error details:\n{error}", exc_info=True)

            if context:
                formatted_context = ", ".join(
                    f"{key}: {value}" for key, value in context.items()
                )
                self.logger.error(f"{error_message} [Context: {formatted_context}]")
            else:
                self.logger.error(error_message)
        except Exception as logging_error:
            # Fallback error logging if something goes wrong with the logger
            print(f"Failed to log error: {logging_error}")
            print(f"Original error: {error}")

    def retry_task(self, task_func, *args, **kwargs) -> Any:
        """
        Execute a task with retry logic for transient errors.

        Args:
            task_func: The function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function

        Returns:
            The result of the successful execution or raises the last exception if retries are exhausted.
        """
        attempts = 0

        while attempts < self.retry_config["max_attempts"]:
            try:
                return task_func(*args, **kwargs)
            except Exception as e:
                attempts += 1
                if attempts < self.retry_config["max_attempts"]:
                    delay = self.retry_config["backoff_factor"] * (
                        2 ** (attempts - 1)
                    )
                    self.logger.warning(
                        f"Attempt {attempts} failed. Retrying in {delay} seconds..."
                    )
                    import time
                    time.sleep(delay)

        # All retries exhausted
        raise

    def notify_admin(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """
        Notify administrators about critical errors.

        Args:
            error: The exception that occurred
            context: Additional context about the error
        """
        try:
            # In a real implementation, this would send an email or Slack message
            self.logger.info("Would notify admin about error in production")

            # Simulate notification for demonstration purposes
            print("\n=== ADMIN NOTIFICATION ===")
            print(f"Error: {error}")
            if context:
                print("Context:", context)
            print("=========================\n")
        except Exception as e:
            self.logger.error(f"Failed to send admin notification: {e}")

    def handle_exception(self, error: Exception, context: Dict[str, Any] = None) -> bool:
        """
        Handle an exception according to its type and severity.

        Args:
            error: The exception that occurred
            context: Additional context about the error

        Returns:
            True if the error was handled (e.g., retryable), False for critical errors.
        """
        self.log_error(error, context)

        # Check if this is a retryable error
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True  # These are transient errors that can be retried

        # Check for other specific error types that might be handled differently
        if isinstance(error, ValueError):
            self.logger.warning("ValueError encountered but not automatically retrying")
            return False

        # For unknown or critical errors
        self.notify_admin(error, context)
        return False