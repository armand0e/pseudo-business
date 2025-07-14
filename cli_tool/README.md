# Agentic AI Development Platform CLI Tool

A command-line interface for interacting with the Agentic AI Development Platform.

## Installation

```bash
pip install -e .
```

## Usage

### Authentication

```bash
# Login to the platform
agentic-cli login

# Logout from the platform
agentic-cli logout
```

### Project Management

```bash
# Initialize a new project
agentic-cli init my-project --config project-config.yaml

# Submit requirements for a project
agentic-cli submit PROJECT_ID -r requirements.yaml

# Get project status
agentic-cli status PROJECT_ID

# List all projects
agentic-cli list-projects
```

### Batch Processing

```bash
# Submit a batch processing request
agentic-cli batch -b batch-config.yaml
```

### Configuration

```bash
# Configure CLI settings
agentic-cli configure --api-url http://localhost:8000 --output-format json
```

## Configuration File Format

### Project Configuration (project-config.yaml)
```yaml
name: "my-project"
description: "A sample project"
tech_stack:
  frontend: "React"
  backend: "FastAPI"
  database: "PostgreSQL"
```

### Requirements File (requirements.yaml)
```yaml
features:
  - "User authentication"
  - "Task management"
deployment:
  target: "docker"
  environment: "production"
```

### Batch Configuration (batch-config.yaml)
```yaml
projects:
  - name: "project-1"
    requirements: "requirements-1.yaml"
  - name: "project-2"
    requirements: "requirements-2.yaml"
batch_size: 2
parallel: true