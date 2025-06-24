# Agentic AI Development Platform

A next-generation platform for automated, intelligent software development.

## Overview

The Agentic AI Development Platform is an innovative system designed to automate and optimize the software development process. It leverages advanced NLP techniques and evolutionary algorithms to generate high-quality code based on user requirements.

Key features:
- Intelligent code generation using evolutionary algorithms
- Specialized agents for frontend, backend, database, and testing
- Master orchestrator for coordinating complex development tasks
- Evolution engine for continuous code optimization

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker (for local development)
- Node.js 18+ (for frontend components)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/agentic-platform.git
   cd agentic-platform
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Quick Start

The easiest way to start the platform is using the startup script:

```bash
python start_platform.py
```

This script will:
- Check all dependencies
- Start database services using Docker
- Initialize the database schema
- Start the main platform application

### Manual Setup

If you prefer manual setup or need to customize the configuration:

1. Start the database services:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. Start the platform:
   ```bash
   PYTHONPATH=. python -m src.main
   ```

### Running the Application

Once started, the platform provides several interfaces:

- **Main API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API Explorer**: http://localhost:8000/redoc
- **Database Admin (Adminer)**: http://localhost:8080
- **Health Check**: http://localhost:8000/health

### Authentication

Default users for testing:
- Username: `admin`, Password: `admin123`
- Username: `developer`, Password: `dev123`

### Stopping the Platform

To stop all services:
```bash
python start_platform.py --stop
```

Or manually:
```bash
docker-compose -f docker-compose.dev.yml down
```

## Project Structure

```
agentic-platform/
├── config/                # Configuration files
│   └── config.yaml        # Main configuration file
├── docs/                  # Documentation
├── src/                   # Source code
│   ├── agents/            # Specialized development agents
│   ├── architecture/      # Core orchestration components
│   ├── infrastructure/     # Infrastructure services
│   ├── ui-interfaces/    # User interface components
│   └── __init__.py        # Python package initialization
├── docker-compose.dev.yml  # Docker Compose configuration for development
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```

## Usage

1. **Project Initialization**:
   - Use the CLI tool to create a new project:
     ```bash
     python src/development/cli_tool.py init --name "My Project" --description "A brief description"
     ```

2. **Code Generation**:
   - Through the web interface, provide requirements and let the system generate code
   - The platform will automatically handle frontend, backend, database, and testing code

3. **Evolution Engine**:
   - Generated code is continuously optimized through evolutionary algorithms
   - View optimization history in the "Evolution" tab of the dashboard

4. **Testing**:
   - Automated tests are generated alongside implementation code
   - Run tests using:
     ```bash
     pytest src/ --cov=src --cov-report=html
     ```

## Configuration

The platform uses a centralized configuration system based on `config/config.yaml`. You can override default settings by:

1. Creating a local config file: `cp config/config.example.yaml config/config.local.yaml`
2. Modifying the values in `config/local.yaml`

Environment variables can also be used for sensitive data:
```bash
export DATABASE_URI="postgresql://user:password@localhost/agentic_platform"
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Create a feature branch (`git checkout -b feature/your-feature`)
2. Commit your changes (`git commit -am 'Add some feature'`)
3. Push to the branch (`git push origin feature/your-feature`)
4. Open a Pull Request

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
