# Agent Coordinator Documentation

## Overview
The Agent Coordinator manages and coordinates different types of agents within the system, assigning tasks based on capabilities and workload.

## Features

### 1. Agent Management
- Registration and unregistration of agents
- Tracking agent status (idle/working)
- Managing agent capabilities

### 2. Task Coordination
- Task assignment to appropriate agents
- Priority-based scheduling
- Concurrency control

### 3. Monitoring
- Timeout handling for long-running tasks
- Status tracking for agents and tasks
- Workflow execution

### 4. Integration with Logging System
The AgentCoordinator class is now integrated with the logging system for:
- Detailed logging of coordination operations
- Error handling through decorator
- Configurable log levels and output channels

## Usage Examples

### Basic Setup
```python
from src.infrastructure.logging_system import LoggingSystem
from src.architecture.agent_coordinator import AgentCoordinator, AgentType, Task

# Initialize logging system
logging_system = LoggingSystem()
logging_system.setup_logging(
    log_level='INFO',
    log_file='coordination.log'
)

# Create and use AgentCoordinator
config = {
    "timeouts": {
        "backend_timeout": 300,
        "database_timeout": 600,
        "frontend_timeout": 120,
        "testing_timeout": 180
    },
    "retry_policies": {
        "max_retries": 3,
        "backoff_factor": 2
    },
    "concurrency_limits": {
        "backend": 5,
        "database": 2,
        "frontend": 10,
        "testing": 3
    }
}

coordinator = AgentCoordinator(config)

# Register agents
coordinator.register_agent("agent1", AgentType.BACKEND, ["data_processing"])
coordinator.register_agent("agent2", AgentType.DATABASE, ["query_execution"])

# Add and assign tasks
task1 = Task(
    task_id="task1",
    description="Process customer data",
    agent_type=AgentType.BACKEND,
    priority=1
)
coordinator.add_task(task1)

task2 = Task(
    task_id="task2",
    description="Generate report query",
    agent_type=AgentType.DATABASE,
    priority=2
)
coordinator.add_task(task2)

# Start coordination workflow
coordinator.execute_workflow()
```

### Error Handling
```python
@logging_system.error_handler
def get_agent_status(agent_id):
    # This function will have automatic error handling and logging
    return coordinator.get_agent_status(agent_id)
```

## Configuration Options

The AgentCoordinator can be configured through a configuration dictionary containing:

- `timeouts`: Dictionary of timeout settings for different agent types
- `retry_policies`: Dictionary of retry policies for failed tasks
- `concurrency_limits`: Dictionary of maximum concurrent tasks per agent type

## Output Formats

All coordination results are returned in consistent formats:

1. **Agent Status**: Dictionary with:
   - Agent ID
   - Type
   - Current status
   - Current task (if any)
   - Capabilities

2. **Task Status**: Dictionary with:
   - Task ID
   - Description
   - Type
   - Priority
   - Status (working/completed)
   - Dependencies

## Integration Guidelines

### For Developers
1. Initialize the LoggingSystem before creating AgentCoordinator instances
2. Use the error handler decorator for any functions that interact with agents or tasks
3. Configure appropriate log levels based on your needs
4. Define clear timeout and concurrency settings for each agent type

### For System Administrators
1. Monitor the coordination logs for errors, warnings, or timeouts
2. Adjust timeout settings based on observed task durations
3. Review agent status to identify bottlenecks or underutilized resources
4. Consider implementing custom monitoring rules for critical tasks

## Best Practices
- Set appropriate concurrency limits based on system resources
- Implement proper error handling for network operations
- Regularly review and update timeout settings as task patterns evolve
- Consider implementing a more sophisticated scheduling algorithm than simple priority-based assignment