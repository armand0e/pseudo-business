require('dotenv').config();
const fastify = require('fastify')({
  logger: {
    transport: {
      prettyPrint: true
    }
  }
});
const LoadBalancer = require('./loadBalancer');
const swagger = require('fastify-swagger');

// Register plugins
async function registerPlugins() {
  const plugins = [require('@fastify/cors'), require('@fastify/helmet'), require('fastify-jwt'), require('@fastify/rate-limit')];
  for (const plugin of plugins) {
    await fastify.register(plugin);
  }

  // Register Swagger for API documentation
  fastify.register(swagger, {
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

  // Helmet configuration
  fastify.register(require('@fastify/helmet'), {
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'", "'unsafe-inline'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["'self'", 'data:'],
        objectSrc: ["'none'"]
      }
    }
  });

  // Rate limiting
  fastify.register(require('@fastify/rate-limit'), {
    max: Number.parseInt(process.env.RATE_LIMIT_MAX, 10) || 100,
    timeWindowMs: Number.parseInt(process.env.RATE_LIMIT_WINDOW_MS, 10) || 900000, // 15 minutes in milliseconds
    skipOnHealthCheck: true,
    allowList: [/localhost/, /127.0.0.1/]
  });
}

// Configure authentication
function configureAuth() {
  fastify.register(require('fastify-jwt'), {
    secret: process.env.JWT_SECRET,
    sign: {
      expiresIn: '1d'
    }
  });

  // JWT error handling
  fastify.setErrorHandler((error, request, reply) => {
    if (error instanceof fastify.auth.JWTErrors) {
      switch (error.code) {
        case 'Unauthorized':
          return reply.send(401).send({ statusCode: 401, message: 'Unauthorized' });
        case 'Forbidden':
          return reply.send(403).send({ statusCode: 403, message: 'Forbidden' });
        default:
          return reply.send(401).send({ statusCode: 401, message: error.message });
      }
    }
    // Forward to the next error handler
    throw error;
  });
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
  fastify.addHook('onRequest', (request, reply) => {
    const startHrtime = process.hrtime();
    return (error, response) => {
      if (!error && response.statusCode >= 500) {
        fastify.log.error(`Request to ${request.url} failed with status code ${response.statusCode}`);
      }

      const duration = process.hrtime(startHrtime);
      fastify.log.info(
        `Request: ${request.method} ${request.url} - Status: ${response.statusCode} - Duration: ${duration[0] * 1000 + Math.floor(duration[1] / 1000)}ms`
      );
    };
  });
}

// Configure error handling
function configureErrorHandling() {
  fastify.setErrorHandler((error, request, reply) => {
    fastify.log.error(error);

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