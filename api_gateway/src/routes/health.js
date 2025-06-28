const express = require('express');
const { asyncHandler } = require('../middleware/errorHandler');
const logger = require('../utils/logger');

const router = express.Router();

// Store for health metrics
const healthMetrics = {
  startTime: Date.now(),
  requestCount: 0,
  errorCount: 0,
  lastError: null
};

/**
 * @swagger
 * /health:
 *   get:
 *     summary: API Gateway health check
 *     tags: [Health]
 *     responses:
 *       200:
 *         description: Service is healthy
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: healthy
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 *                 uptime:
 *                   type: number
 *                   description: Uptime in seconds
 *                 version:
 *                   type: string
 *                 environment:
 *                   type: string
 *       503:
 *         description: Service is unhealthy
 */
router.get('/', asyncHandler(async (req, res) => {
  const uptime = Math.floor((Date.now() - healthMetrics.startTime) / 1000);
  
  // Basic health checks
  const healthStatus = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: uptime,
    version: process.env.npm_package_version || '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    nodeVersion: process.version,
    memory: process.memoryUsage(),
    requestCount: healthMetrics.requestCount,
    errorCount: healthMetrics.errorCount
  };

  // Check if there have been recent errors
  if (healthMetrics.lastError && Date.now() - healthMetrics.lastError < 60000) {
    healthStatus.status = 'degraded';
    healthStatus.warning = 'Recent errors detected';
  }

  const statusCode = healthStatus.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(healthStatus);
}));

/**
 * @swagger
 * /health/detailed:
 *   get:
 *     summary: Detailed health check with dependencies
 *     tags: [Health]
 *     responses:
 *       200:
 *         description: Detailed health information
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                 checks:
 *                   type: object
 *                 system:
 *                   type: object
 */
router.get('/detailed', asyncHandler(async (req, res) => {
  const checks = {
    memory: checkMemoryUsage(),
    uptime: checkUptime(),
    environment: checkEnvironment(),
    dependencies: await checkDependencies()
  };

  const allHealthy = Object.values(checks).every(check => check.status === 'healthy');
  
  const healthStatus = {
    status: allHealthy ? 'healthy' : 'unhealthy',
    timestamp: new Date().toISOString(),
    checks,
    system: {
      platform: process.platform,
      arch: process.arch,
      nodeVersion: process.version,
      pid: process.pid,
      cpuUsage: process.cpuUsage(),
      memoryUsage: process.memoryUsage()
    }
  };

  const statusCode = allHealthy ? 200 : 503;
  res.status(statusCode).json(healthStatus);
}));

/**
 * @swagger
 * /health/liveness:
 *   get:
 *     summary: Kubernetes liveness probe
 *     tags: [Health]
 *     responses:
 *       200:
 *         description: Service is alive
 *       503:
 *         description: Service should be restarted
 */
router.get('/liveness', (req, res) => {
  // Simple liveness check - just verify the process is running
  res.status(200).json({
    status: 'alive',
    timestamp: new Date().toISOString()
  });
});

/**
 * @swagger
 * /health/readiness:
 *   get:
 *     summary: Kubernetes readiness probe
 *     tags: [Health]
 *     responses:
 *       200:
 *         description: Service is ready to receive traffic
 *       503:
 *         description: Service is not ready
 */
router.get('/readiness', asyncHandler(async (req, res) => {
  // Check if service is ready to handle requests
  const isReady = await checkReadiness();
  
  if (isReady) {
    res.status(200).json({
      status: 'ready',
      timestamp: new Date().toISOString()
    });
  } else {
    res.status(503).json({
      status: 'not_ready',
      timestamp: new Date().toISOString(),
      message: 'Service is starting up or experiencing issues'
    });
  }
}));

/**
 * Health check functions
 */

function checkMemoryUsage() {
  const usage = process.memoryUsage();
  const maxMemory = 1024 * 1024 * 1024; // 1GB threshold
  
  return {
    status: usage.heapUsed < maxMemory ? 'healthy' : 'unhealthy',
    heapUsed: usage.heapUsed,
    heapTotal: usage.heapTotal,
    external: usage.external,
    rss: usage.rss
  };
}

function checkUptime() {
  const uptime = Math.floor((Date.now() - healthMetrics.startTime) / 1000);
  
  return {
    status: 'healthy',
    uptime: uptime,
    startTime: new Date(healthMetrics.startTime).toISOString()
  };
}

function checkEnvironment() {
  const requiredEnvVars = ['JWT_SECRET', 'NODE_ENV'];
  const missing = requiredEnvVars.filter(envVar => !process.env[envVar]);
  
  return {
    status: missing.length === 0 ? 'healthy' : 'unhealthy',
    environment: process.env.NODE_ENV,
    missingVariables: missing
  };
}

async function checkDependencies() {
  // Check Redis connection if configured
  if (process.env.REDIS_HOST) {
    try {
      const redis = require('redis');
      const client = redis.createClient({
        host: process.env.REDIS_HOST,
        port: process.env.REDIS_PORT || 6379,
        password: process.env.REDIS_PASSWORD,
        connectTimeout: 5000
      });
      
      await client.connect();
      await client.ping();
      await client.disconnect();
      
      return {
        status: 'healthy',
        redis: 'connected'
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        redis: 'disconnected',
        error: error.message
      };
    }
  }
  
  return {
    status: 'healthy',
    redis: 'not_configured'
  };
}

async function checkReadiness() {
  try {
    // Check if JWT secret is configured
    if (!process.env.JWT_SECRET) {
      return false;
    }
    
    // Check memory usage
    const memoryCheck = checkMemoryUsage();
    if (memoryCheck.status !== 'healthy') {
      return false;
    }
    
    // Service is ready
    return true;
  } catch (error) {
    logger.error('Readiness check failed:', error);
    return false;
  }
}

// Middleware to track request metrics
router.use((req, res, next) => {
  healthMetrics.requestCount++;
  
  // Track errors
  const originalSend = res.send;
  res.send = function(data) {
    if (res.statusCode >= 400) {
      healthMetrics.errorCount++;
      healthMetrics.lastError = Date.now();
    }
    originalSend.call(this, data);
  };
  
  next();
});

module.exports = router;