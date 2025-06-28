# API Gateway - Agentic AI Development Platform

The API Gateway serves as the central entry point for the Agentic AI Development Platform, providing authentication, authorization, rate limiting, and intelligent routing to backend microservices.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Service Routing](#service-routing)
- [Health Monitoring](#health-monitoring)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Security](#security)
- [Contributing](#contributing)

## Overview

The API Gateway is built with Node.js and Express.js, designed to handle all incoming requests to the Agentic AI platform. It provides a unified interface for clients while routing requests to appropriate backend services including the Master Orchestrator, Backend Agent, Database Agent, and specialized processing agents.

## Features

### Core Functionality
- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **Request Routing**: Intelligent proxy routing to backend microservices
- **Rate Limiting**: Configurable rate limiting with Redis support for distributed systems
- **Request Validation**: Comprehensive input validation using express-validator
- **Error Handling**: Centralized error handling with consistent response formats
- **Logging**: Structured logging with Winston for debugging and monitoring

### Security Features
- **Helmet.js**: Security headers and protection against common vulnerabilities
- **CORS**: Configurable Cross-Origin Resource Sharing
- **Input Sanitization**: Protection against injection attacks
- **Request Size Limiting**: Protection against large payload attacks
- **JWT Token Validation**: Secure token verification and refresh

### Monitoring & Health
- **Health Checks**: Kubernetes-ready liveness and readiness probes
- **Metrics Collection**: Request/response metrics and performance monitoring
- **Service Discovery**: Health monitoring of backend services
- **Swagger Documentation**: Comprehensive API documentation with OpenAPI 3.0

## Architecture

```
┌─────────────────┐    ┌───────────────────┐    ┌─────────────────────┐
│                 │    │                   │    │                     │
│   Web Client    │    │   Mobile App      │    │   External API      │
│                 │    │                   │    │                     │
└─────────┬───────┘    └─────────┬─────────┘    └──────────┬──────────┘
          │                      │                         │
          └──────────────────────┼─────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │                         │
                    │      API Gateway        │
                    │                         │
                    │  • Authentication       │
                    │  • Rate Limiting        │
                    │  • Request Routing      │
                    │  • Input Validation     │
                    │  • Error Handling       │
                    │                         │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼──────────┐ ┌─────────▼──────────┐ ┌─────────▼──────────┐
│                    │ │                    │ │                    │
│ Master Orchestrator│ │   Backend Agent    │ │   Database Agent   │
│                    │ │                    │ │                    │
└────────────────────┘ └────────────────────┘ └────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │                         │
                    │  Specialized Agents     │
                    │                         │
                    │  • NLP Agent           │
                    │  • Code Agent          │
                    │  • Analysis Agent      │
                    │                         │
                    └─────────────────────────┘
```

## Installation

### Prerequisites
- Node.js 18+ (LTS recommended)
- npm or yarn
- Redis (optional, for distributed rate limiting)

### Quick Start

1. **Clone and navigate to the API Gateway directory:**
   ```bash
   cd api_gateway
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

The API Gateway will be available at `http://localhost:3000`

### Docker Installation

1. **Build the Docker image:**
   ```bash
   docker build -t api-gateway .
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

#### Server Configuration
```bash
NODE_ENV=development
PORT=3000
HOST=0.0.0.0
```

#### JWT Authentication
```bash
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRES_IN=24h
```

#### Rate Limiting
```bash
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=1000
RATE_LIMIT_MAX_REQUESTS_UNAUTHENTICATED=100
```

#### Backend Services
```bash
MASTER_ORCHESTRATOR_URL=http://localhost:8000
BACKEND_AGENT_URL=http://localhost:8001
DATABASE_AGENT_URL=http://localhost:8002
SPECIALIZED_AGENTS_BASE_URL=http://localhost:8003
```

#### Redis (Optional)
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

### Service URLs

Configure the URLs for backend services that the gateway will proxy to:

- **Master Orchestrator**: Handles task orchestration and workflow management
- **Backend Agent**: Core business logic and data processing
- **Database Agent**: Data persistence and retrieval operations
- **Specialized Agents**: Domain-specific processing (NLP, code analysis, etc.)

## API Documentation

### Interactive Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:3000/api-docs`
- **OpenAPI Spec**: `http://localhost:3000/api-docs.json`

### Core Endpoints

#### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Authenticate and get JWT token
- `GET /auth/profile` - Get current user profile

#### Health Monitoring
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health information
- `GET /health/liveness` - Kubernetes liveness probe
- `GET /health/readiness` - Kubernetes readiness probe

#### Service Proxy
- `/**/api/orchestrator/**` - Proxy to Master Orchestrator
- `/**/api/backend/**` - Proxy to Backend Agent
- `/**/api/database/**` - Proxy to Database Agent
- `/**/api/agents/**` - Proxy to Specialized Agents
- `/**/api/admin/**` - Admin endpoints (admin role required)

## Authentication

The API Gateway uses JWT (JSON Web Tokens) for stateless authentication.

### User Registration
```bash
curl -X POST http://localhost:3000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "role": "user"
  }'
```

### User Login
```bash
curl -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### Using JWT Token
Include the JWT token in the Authorization header:
```bash
Authorization: Bearer <jwt_token>
```

### Roles and Permissions
- **admin**: Full access to all endpoints and admin functions
- **user**: Access to standard user endpoints
- **developer**: Access to development and debugging endpoints

## Rate Limiting

Rate limiting protects against abuse and ensures fair usage:

### Default Limits
- **Authenticated users**: 1000 requests per 15 minutes
- **Unauthenticated users**: 100 requests per 15 minutes

### Redis Integration
For distributed systems, configure Redis to share rate limit state across multiple gateway instances:

```bash
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
```

### Custom Rate Limits
Rate limits can be customized per user role or endpoint by modifying the rate limiting middleware.

## Service Routing

The gateway intelligently routes requests to backend services based on URL patterns:

### Routing Rules
1. **Authentication Required**: All `/api/**` routes require valid JWT tokens
2. **Admin Routes**: `/api/admin/**` requires admin role
3. **Service Mapping**:
   - `/api/orchestrator/**` → Master Orchestrator
   - `/api/backend/**` → Backend Agent
   - `/api/database/**` → Database Agent
   - `/api/agents/**` → Specialized Agents

### Request Headers
The gateway forwards user context in headers:
- `x-user-id`: User identifier
- `x-user-email`: User email address
- `x-user-role`: User role
- `x-user-permissions`: User permissions array

### Load Balancing
For production deployments, configure multiple backend service instances and use the built-in load balancing features.

## Health Monitoring

### Health Check Endpoints

#### Basic Health Check
```bash
GET /health
```
Returns basic service status and metrics.

#### Detailed Health Check
```bash
GET /health/detailed
```
Returns comprehensive health information including:
- Memory usage
- Uptime statistics
- Environment checks
- Dependency status

#### Kubernetes Probes
- **Liveness**: `GET /health/liveness`
- **Readiness**: `GET /health/readiness`

### Monitoring Integration
The gateway exposes metrics compatible with:
- Prometheus
- Grafana
- ELK Stack
- Custom monitoring solutions

## Development

### Project Structure
```
api_gateway/
├── src/
│   ├── index.js              # Main application entry point
│   ├── middleware/           # Express middleware
│   │   ├── auth.js          # Authentication middleware
│   │   └── errorHandler.js  # Error handling middleware
│   ├── routes/              # Route handlers
│   │   ├── auth.js          # Authentication routes
│   │   ├── health.js        # Health check routes
│   │   └── proxy.js         # Service proxy routes
│   └── utils/               # Utility modules
│       ├── logger.js        # Logging configuration
│       └── swagger.js       # API documentation
├── tests/                   # Test suites
├── logs/                    # Log files
├── package.json            # Dependencies and scripts
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Multi-service setup
└── .env.example           # Environment template
```

### Available Scripts
```bash
# Development server with hot reload
npm run dev

# Production server
npm start

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Lint code
npm run lint

# Format code
npm run format

# Security audit
npm audit
```

### Code Style
The project uses:
- **ESLint**: Code linting and style enforcement
- **Prettier**: Code formatting
- **Husky**: Git hooks for pre-commit checks

## Testing

### Test Suite
```bash
# Run all tests
npm test

# Run specific test file
npm test -- --grep "Authentication"

# Run tests with coverage report
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Test Categories
- **Unit Tests**: Individual function and middleware testing
- **Integration Tests**: End-to-end API testing
- **Security Tests**: Authentication and authorization testing
- **Performance Tests**: Load and stress testing

### Test Environment
Tests use a separate test environment with:
- In-memory data stores
- Mocked external services
- Isolated test databases

## Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale the service
docker-compose up -d --scale api-gateway=3

# View logs
docker-compose logs -f api-gateway
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: api-gateway:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: api-gateway-secret
              key: jwt-secret
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Production Considerations
- **Load Balancing**: Use NGINX or cloud load balancers
- **SSL/TLS**: Configure HTTPS with valid certificates
- **Environment Variables**: Use secure secret management
- **Monitoring**: Set up comprehensive logging and alerting
- **Backup**: Regular backup of configuration and logs

## Security

### Security Features
- **Helmet.js**: Security headers and protections
- **JWT Authentication**: Stateless token-based auth
- **Rate Limiting**: Protection against abuse
- **Input Validation**: Comprehensive request validation
- **CORS Configuration**: Controlled cross-origin access
- **Error Handling**: Secure error responses

### Security Best Practices
1. **Regular Updates**: Keep dependencies updated
2. **Secret Management**: Use environment variables for secrets
3. **HTTPS Only**: Always use encrypted connections in production
4. **Monitoring**: Set up security event monitoring
5. **Access Control**: Implement principle of least privilege
6. **Audit Logging**: Log all security-relevant events

### Security Scanning
```bash
# Security audit
npm audit

# Dependency vulnerability check
npm audit fix

# Security linting
npm run lint:security
```

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install dependencies: `npm install`
4. Make your changes
5. Run tests: `npm test`
6. Submit a pull request

### Coding Standards
- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Use meaningful commit messages

### Issue Reporting
When reporting issues, include:
- Node.js version
- npm version
- Operating system
- Error messages and stack traces
- Steps to reproduce

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation and FAQ

---

**Agentic AI Development Platform - API Gateway**  
Version 1.0.0 | Built with Node.js and Express.js