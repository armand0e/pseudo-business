require('dotenv').config();
const fastify = require('fastify')({
  logger: true
});
const LoadBalancer = require('./loadBalancer');
const swagger = require('@fastify/swagger');

// Register plugins
async function registerPlugins() {
  // Register CORS
  await fastify.register(require('@fastify/cors'));
  
  // Register Helmet
  await fastify.register(require('@fastify/helmet'));
  
  // Register JWT
  await fastify.register(require('@fastify/jwt'), {
    secret: process.env.JWT_SECRET || 'integration_test_secret'
  });
  
  // Register Rate Limiting
  await fastify.register(require('@fastify/rate-limit'), {
    max: Number.parseInt(process.env.RATE_LIMIT_MAX, 10) || 100,
    timeWindow: Number.parseInt(process.env.RATE_LIMIT_WINDOW_MS, 10) || 900000
  });

  // Register Swagger for API documentation
  await fastify.register(swagger, {
    routePrefix: '/docs',
    swagger: {
      info: {
        title: 'API Gateway Documentation',
        description: 'Documentation for the Pseudo Business API Gateway',
        version: '1.0.0'
      },
      externalDocs: {
        url: 'https://github.com/pseudo-business/api-gateway',
        description: 'Find more info here'
      },
      host: process.env.HOST || 'localhost:3000',
      schemes: ['http', 'https'],
      consumes: ['application/json'],
      produces: ['application/json']
    }
  });
}

// Configure security
function configureSecurity() {
  // CORS configuration
  fastify.addHook('onRequest', async (request, reply) => {
    if (request.method !== 'OPTIONS') {
      console.log(`Incoming request: ${request.method} ${request.url}`);
    }
  });

  // Note: Helmet and rate limiting are already registered in registerPlugins()
}

// Configure authentication
function configureAuth() {
  // JWT is already registered in registerPlugins()
  // JWT error handling will be done in the main error handler
}

// Configure routes with load balancing and API documentation
function configureRoutes() {
  const loadBalancer = new LoadBalancer();
  // Add some backend services for demonstration
  loadBalancer.addServer('http://localhost:4001');
  loadBalancer.addServer('http://localhost:4002');

  fastify.get('/health', async (request, reply) => {
    return { status: 'ok' };
  });

  // API documentation route
  fastify.get('/', async (request, reply) => {
    reply.redirect('/docs');
  });

  // Route for agents with load balancing
  fastify.route({
    method: ['GET', 'POST', 'PUT', 'DELETE'],
    url: '/agents/:agentName/*',
    schema: {
      description: 'Route requests to appropriate backend services',
      tags: ['Agents']
    },
    handler: async (request, reply) => {
      try {
        const targetService = loadBalancer.getNextServer();
        fastify.log.info(`Forwarding request to ${targetService}`);

        // Forward the request to the selected service
        const response = await fetch(`${targetService}${request.url.slice(request.routeOptions.prefix.length)}`, {
          method: request.method,
          headers: request.headers,
          body: request.body ? JSON.stringify(request.body) : undefined
        });

        reply.status(response.status).headers(response.headers);
        return response.json();
      } catch (err) {
        fastify.log.error(`Error forwarding request: ${err.message}`);
        reply.status(503).send({ error: 'Service unavailable' });
      }
    }
  });
}

// Configure monitoring and metrics
function configureMonitoring() {
  // Basic logging for monitoring
  fastify.addHook('onRequest', async (request, reply) => {
    request.startTime = process.hrtime();
  });

  fastify.addHook('onResponse', async (request, reply) => {
    const duration = process.hrtime(request.startTime);
    const durationMs = duration[0] * 1000 + Math.floor(duration[1] / 1000000);
    
    if (reply.statusCode >= 500) {
      fastify.log.error(`Request to ${request.url} failed with status code ${reply.statusCode}`);
    }

    fastify.log.info(
      `Request: ${request.method} ${request.url} - Status: ${reply.statusCode} - Duration: ${durationMs}ms`
    );
  });
}

// Configure error handling
function configureErrorHandling() {
  fastify.setErrorHandler((error, request, reply) => {
    fastify.log.error(error);

    // Handle JWT errors
    if (error.code === 'FST_JWT_AUTHORIZATION_TOKEN_EXPIRED' ||
        error.code === 'FST_JWT_AUTHORIZATION_TOKEN_INVALID' ||
        error.code === 'FST_JWT_NO_AUTHORIZATION_IN_HEADER') {
      return reply.status(401).send({ statusCode: 401, message: 'Unauthorized' });
    }

    // Return different error codes based on the type of error
    if (error.statusCode) {
      return reply.status(error.statusCode).send({ statusCode: error.statusCode, message: error.message });
    }

    reply.status(500).send({ statusCode: 500, message: 'Internal Server Error' });
  });
}

// Main function to setup the server
async function setupServer() {
  try {
    await registerPlugins();
    configureSecurity();
    configureAuth();
    configureRoutes();
    configureMonitoring();
    configureErrorHandling();

    // Start the server
    const PORT = process.env.PORT || 3000;
    await fastify.listen({ port: PORT, host: '0.0.0.0' });
    console.log(`Server listening on ${fastify.server.address().port}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
}

// Start the server
setupServer();