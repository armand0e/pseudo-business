const swaggerJsdoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Agentic AI Development Platform - API Gateway',
      version: '1.0.0',
      description: `
        The API Gateway serves as the central entry point for the Agentic AI Development Platform.
        It provides authentication, authorization, rate limiting, and intelligent routing to backend services.
        
        ## Authentication
        Most endpoints require a valid JWT token in the Authorization header:
        \`Authorization: Bearer <jwt_token>\`
        
        ## Rate Limiting
        API requests are rate-limited based on user authentication status:
        - Authenticated users: 1000 requests per 15 minutes
        - Unauthenticated users: 100 requests per 15 minutes
        
        ## Service Routing
        The gateway routes requests to the following backend services:
        - Master Orchestrator: Task orchestration and workflow management
        - Backend Agent: Core business logic and data processing
        - Database Agent: Data persistence and retrieval
        - Specialized Agents: Domain-specific processing services
      `,
      contact: {
        name: 'API Support',
        email: 'api-support@agentic-ai.com'
      },
      license: {
        name: 'MIT',
        url: 'https://opensource.org/licenses/MIT'
      }
    },
    servers: [
      {
        url: process.env.API_BASE_URL || 'http://localhost:3000',
        description: 'Development server'
      },
      {
        url: 'https://api.agentic-ai.com',
        description: 'Production server'
      }
    ],
    components: {
      securitySchemes: {
        BearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
          description: 'JWT token for authentication'
        }
      },
      schemas: {
        User: {
          type: 'object',
          properties: {
            id: {
              type: 'string',
              description: 'Unique user identifier'
            },
            email: {
              type: 'string',
              format: 'email',
              description: 'User email address'
            },
            role: {
              type: 'string',
              enum: ['admin', 'user', 'developer'],
              description: 'User role in the system'
            },
            permissions: {
              type: 'array',
              items: {
                type: 'string'
              },
              description: 'List of user permissions'
            },
            createdAt: {
              type: 'string',
              format: 'date-time',
              description: 'User creation timestamp'
            },
            lastLogin: {
              type: 'string',
              format: 'date-time',
              description: 'Last login timestamp'
            }
          },
          required: ['id', 'email', 'role']
        },
        AuthRequest: {
          type: 'object',
          properties: {
            email: {
              type: 'string',
              format: 'email',
              description: 'User email address'
            },
            password: {
              type: 'string',
              minLength: 8,
              description: 'User password (minimum 8 characters)'
            }
          },
          required: ['email', 'password']
        },
        AuthResponse: {
          type: 'object',
          properties: {
            token: {
              type: 'string',
              description: 'JWT authentication token'
            },
            user: {
              $ref: '#/components/schemas/User'
            },
            expiresIn: {
              type: 'string',
              description: 'Token expiration time'
            }
          },
          required: ['token', 'user', 'expiresIn']
        },
        Error: {
          type: 'object',
          properties: {
            error: {
              type: 'string',
              description: 'Error message'
            },
            code: {
              type: 'string',
              description: 'Error code'
            },
            details: {
              type: 'object',
              description: 'Additional error details'
            },
            timestamp: {
              type: 'string',
              format: 'date-time',
              description: 'Error timestamp'
            }
          },
          required: ['error', 'timestamp']
        },
        ValidationError: {
          type: 'object',
          properties: {
            error: {
              type: 'string',
              example: 'Validation failed'
            },
            details: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  field: {
                    type: 'string',
                    description: 'Field that failed validation'
                  },
                  message: {
                    type: 'string',
                    description: 'Validation error message'
                  }
                }
              }
            }
          }
        },
        HealthStatus: {
          type: 'object',
          properties: {
            status: {
              type: 'string',
              enum: ['healthy', 'degraded', 'unhealthy'],
              description: 'Overall health status'
            },
            timestamp: {
              type: 'string',
              format: 'date-time',
              description: 'Health check timestamp'
            },
            uptime: {
              type: 'number',
              description: 'Service uptime in seconds'
            },
            version: {
              type: 'string',
              description: 'Service version'
            },
            environment: {
              type: 'string',
              description: 'Environment name'
            }
          }
        }
      },
      responses: {
        UnauthorizedError: {
          description: 'Authentication token is missing or invalid',
          content: {
            'application/json': {
              schema: {
                $ref: '#/components/schemas/Error'
              },
              example: {
                error: 'Unauthorized access',
                code: 'UNAUTHORIZED',
                timestamp: '2024-01-01T00:00:00.000Z'
              }
            }
          }
        },
        ForbiddenError: {
          description: 'Insufficient permissions for this operation',
          content: {
            'application/json': {
              schema: {
                $ref: '#/components/schemas/Error'
              },
              example: {
                error: 'Insufficient permissions',
                code: 'FORBIDDEN',
                timestamp: '2024-01-01T00:00:00.000Z'
              }
            }
          }
        },
        ValidationError: {
          description: 'Request validation failed',
          content: {
            'application/json': {
              schema: {
                $ref: '#/components/schemas/ValidationError'
              }
            }
          }
        },
        RateLimitError: {
          description: 'Rate limit exceeded',
          content: {
            'application/json': {
              schema: {
                $ref: '#/components/schemas/Error'
              },
              example: {
                error: 'Rate limit exceeded',
                code: 'RATE_LIMIT_EXCEEDED',
                timestamp: '2024-01-01T00:00:00.000Z'
              }
            }
          }
        },
        InternalServerError: {
          description: 'Internal server error',
          content: {
            'application/json': {
              schema: {
                $ref: '#/components/schemas/Error'
              },
              example: {
                error: 'Internal server error',
                code: 'INTERNAL_ERROR',
                timestamp: '2024-01-01T00:00:00.000Z'
              }
            }
          }
        }
      }
    },
    security: [
      {
        BearerAuth: []
      }
    ],
    tags: [
      {
        name: 'Authentication',
        description: 'User authentication and authorization endpoints'
      },
      {
        name: 'Health',
        description: 'Service health monitoring and status endpoints'
      },
      {
        name: 'Proxy',
        description: 'Backend service proxy and routing endpoints'
      },
      {
        name: 'Admin',
        description: 'Administrative endpoints (admin access required)'
      }
    ]
  },
  apis: [
    './src/routes/*.js',
    './src/middleware/*.js'
  ]
};

const specs = swaggerJsdoc(options);

// Custom CSS for Swagger UI
const customCss = `
  .swagger-ui .topbar { display: none; }
  .swagger-ui .info { margin: 20px 0; }
  .swagger-ui .info .title { color: #2c3e50; }
  .swagger-ui .scheme-container { background: #f8f9fa; padding: 20px; margin: 20px 0; }
`;

const swaggerOptions = {
  customCss,
  customSiteTitle: 'Agentic AI - API Gateway Documentation',
  customfavIcon: '/favicon.ico',
  swaggerOptions: {
    persistAuthorization: true,
    displayRequestDuration: true,
    filter: true,
    showExtensions: true,
    showCommonExtensions: true,
    docExpansion: 'list',
    defaultModelsExpandDepth: 2,
    defaultModelExpandDepth: 2
  }
};

module.exports = {
  specs,
  swaggerUi,
  swaggerOptions,
  setupSwagger: (app) => {
    // Serve Swagger documentation
    app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(specs, swaggerOptions));
    
    // Serve raw OpenAPI spec
    app.get('/api-docs.json', (req, res) => {
      res.setHeader('Content-Type', 'application/json');
      res.send(specs);
    });
    
    // Health check endpoint specifically for API docs
    app.get('/api-docs/health', (req, res) => {
      res.json({
        status: 'healthy',
        documentation: 'available',
        timestamp: new Date().toISOString()
      });
    });
  }
};