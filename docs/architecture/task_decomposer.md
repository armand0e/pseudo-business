# Task Decomposer Documentation

## Overview
The Task Decomposer breaks down complex tasks into manageable subtasks with appropriate priorities and dependencies.

## Features

### 1. Task Analysis
- Complexity assessment based on text analysis
- Initial priority determination
- Dependency identification

### 2. Decomposition Capabilities
- Recursive decomposition up to specified depth
- Subtask creation with proper attributes
- Validation of decomposition quality

### 3. Integration with Logging System
The TaskDecomposer class is now integrated with the logging system for:
- Detailed logging of decomposition operations
- Error handling through decorator
- Configurable log levels and output channels

## Usage Examples

### Basic Setup
```python
from src.infrastructure.logging_system import LoggingSystem
from src.architecture.nlp_processor import NLPProcessor
from src.architecture.task_decomposer import TaskDecomposer

# Initialize logging system
logging_system = LoggingSystem()
logging_system.setup_logging(
    log_level='INFO',
    log_file='task_decomposition.log'
)

# Create and use TaskDecomposer
nlp_processor = NLPProcessor({
    'model_name': 'en_core_web_sm'
})
decomposer = TaskDecomposer(nlp_processor)

complex_task = {
    'description': 'Build a customer-facing web application',
    'complexity': 0.95,
    'priority': 1
}

analyzed_task = decomposer.analyze_task(complex_task['description'])
subtasks = decomposer.decompose_task(analyzed_task)
```

### Error Handling
```python
@logging_system.error_handler
def process_complex_task(task_description):
    # This function will have automatic error handling and logging
    analyzed = decomposer.analyze_task(task_description)
    return decomposer.decompose_task(analyzed)
```

## Configuration Options

The TaskDecomposer can be configured through:

1. **NLP Processor**: Passed to constructor for text analysis
2. **Class Attributes**:
   - `max_depth`: Maximum decomposition depth (default: 5)
   - `complexity_threshold`: Threshold for considering a task complex (default: 0.7)

## Output Formats

All decomposition results are returned in consistent formats:

1. **Analyzed Task**: Dictionary containing:
   - Description
   - Complexity score
   - Priority
   - Other analysis metadata

2. **Subtasks**: List of dictionaries with:
   - Description
   - Priority
   - Complexity
   - Dependencies (if any)

## Integration Guidelines

### For Developers
1. Initialize the LoggingSystem before creating TaskDecomposer instances
2. Use the error handler decorator for any functions that process tasks
3. Configure appropriate log levels based on your needs
4. Ensure the NLPProcessor is properly initialized with a valid model

### For System Administrators
1. Monitor the task decomposition logs for errors or warnings
2. Adjust log rotation settings as needed based on usage
3. Review decomposed tasks to ensure they meet quality standards

## Best Practices
- Set appropriate complexity thresholds based on your use case
- Validate decompositions before using subtasks in workflows
- Consider implementing custom validation rules specific to your domain