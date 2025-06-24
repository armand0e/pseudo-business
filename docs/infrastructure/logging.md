# Logging System Documentation

## Overview
The logging system provides comprehensive logging capabilities for the agent framework. It handles:
- Log message creation and formatting
- Multiple output channels (console, file, API)
- Error handling and reporting
- Log rotation and retention

## Features

### 1. Logging Configuration
The `LoggingSystem` class allows configuration of:
- Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File-based logging with rotation
- Remote API logging
- Console output

### 2. Error Handling
- Decorator for agent methods to handle errors consistently
- Automatic logging of exceptions
- Configurable error handling policies

### 3. Custom Handlers
- `RemoteLoggingHandler`: For sending logs to a remote API
- `LogFilter`: For filtering log messages by level

## Usage Examples

### Basic Setup
```python
from src.infrastructure.logging_system import LoggingSystem

# Initialize and configure the logging system
logging_system = LoggingSystem()
logging_system.setup_logging(
    log_level='INFO',
    log_file='app.log',
    api_endpoint='https://api.example.com/logs'
)

logger = logging_system.get_logger()

# Use the logger in your code
logger.info("Processing task started")
logger.error("An error occurred", exc_info=True)
```

### Error Handling Decorator
```python
from src.infrastructure.logging_system import LoggingSystem

logging_system = LoggingSystem()

@logging_system.error_handler
def process_task(task_data):
    # Task processing logic
    pass
```

## Configuration Options

The logging system can be configured through the `setup_logging` method:

- `log_level`: Set the minimum log level to output (default: INFO)
- `log_file`: Path to the log file (default: 'app.log')
- `api_endpoint`: URL for remote logging (optional)
- `max_bytes`: Maximum bytes before rotation (default: 10MB)
- `backup_count`: Number of backup files to keep (default: 3)

## Output Formats

All log messages are formatted with:
```
<timestamp> - <logger_name> - <levelname> - <message>
```

Example output:
```
2025-06-24 13:59:00,000 - agent - INFO - Processing task started
2025-06-24 13:59:01,000 - agent - ERROR - An error occurred
```

## Integration Guidelines

### For Agent Developers
1. Initialize the `LoggingSystem` in your agent's initialization code
2. Use the `@error_handler` decorator for all public methods
3. Use the returned logger instance for logging messages

### For System Administrators
1. Configure log rotation settings appropriately based on system resources
2. Set up monitoring for critical error logs
3. Ensure API endpoints are available if remote logging is configured

## Error Handling Policies

The system implements the following policies:
- Automatic retry for failed API log attempts (3 retries with exponential backoff)
- Fallback to file logging when API is unavailable
- Full exception information included in ERROR and CRITICAL logs