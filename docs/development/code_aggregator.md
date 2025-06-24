# Code Aggregator

The Code Aggregator is a system component responsible for collecting, merging, and validating code changes from multiple agents in our development environment.

## Purpose

The primary purpose of the Code Aggregator is to:

1. Collect code changes from different agents working on the same project
2. Resolve conflicts between concurrent changes
3. Ensure code quality standards are maintained
4. Apply validated changes to the codebase

## Usage Examples

### Basic Usage

```python
# Create an instance of CodeAggregator with configuration
config = {
    'file_monitoring_patterns': [r'^\w[\w/-]*\.(py|js)$'],
    'conflict_resolution': 'latest',
    'quality_thresholds': {
        'complexity': 10,
        'line_length': 120
    }
}
aggregator = CodeAggregator(config)

# Collect a code change from an agent
aggregator.collect_code_change('agent1', 'src/app.py', 'print("Hello")')

# Resolve conflicts and apply changes
if aggregator.apply_changes():
    print("Changes applied successfully")
```

### Advanced Usage with Conflict Resolution

```python
# Configure for merge strategy
config['conflict_resolution'] = 'merge'
aggregator.config = config

# Collect multiple changes that might conflict
aggregator.collect_code_change('agent1', 'src/app.py', 'print("Hello")')
aggregator.collect_code_change('agent2', 'src/app.py', 'print("World")')

# Resolve conflicts and apply
if aggregator.apply_changes():
    print("Changes applied successfully")
```

## Configuration Options

The Code Aggregator can be configured through the following parameters:

### File Monitoring Patterns

- `file_monitoring_patterns`: List of regex patterns for files to monitor (default: `['^\w[\w/-]*\.(py|js)$']`)
  - Example: `['^src/.*\.py$', '^utils/.*\.js$']`

### Conflict Resolution

- `conflict_resolution`: Strategy for resolving conflicts between changes
  - Options:
    - `latest`: Use the most recent change (default)
    - `merge`: Attempt to merge conflicting changes

### Quality Thresholds

- `complexity`: Maximum allowed complexity score (default: 10)
- `line_length`: Maximum allowed line length (default: 120)
- `function_lines`: Maximum lines per function (default: 50)
- `doc_coverage`: Minimum documentation coverage percentage (default: 80)

### Logging

- `logging.level`: Log level (DEBUG, INFO, WARNING, ERROR) (default: INFO)
- `logging.file`: Path to log file (default: logs/code_aggregator.log)

## Output Formats

The Code Aggregator produces the following outputs:

1. Resolved code changes ready for application
2. Quality check results indicating compliance with standards
3. Log messages documenting the aggregation process

## Integration Guidelines

### With AgentCoordinator

The AgentCoordinator should integrate with the Code Aggregator by:

1. Creating an instance of `CodeAggregator` with appropriate configuration
2. Collecting code changes from agents using `collect_code_change()`
3. Triggering conflict resolution and application via `apply_changes()`

### With Logging System

The Code Aggregator is integrated with our logging system to provide visibility into the aggregation process. Log messages include:

- Collection of changes from agents
- Conflict detection and resolution
- Quality check results
- Application success/failure

## Best Practices

1. Configure appropriate quality thresholds based on project standards
2. Choose a conflict resolution strategy that matches your team's workflow
3. Monitor log output for potential issues in the aggregation process
4. Regularly review quality check failures to maintain code standards