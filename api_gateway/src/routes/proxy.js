const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const { authenticateToken, requireRoles, requirePermissions } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');
const logger = require('../utils/logger');

const router = express.Router();

// Service URLs from environment variables
const ORCHESTRATOR_SERVICE_URL = process.env.ORCHESTRATOR_SERVICE_URL || 'http://localhost:8000';
const BACKEND_SERVICE_URL = process.env.BACKEND_SERVICE_URL || 'http://localhost:8001';
const DATABASE_SERVICE_URL = process.env.DATABASE_SERVICE_URL || 'http://localhost:8002';

/**
 * Proxy configuration options
 */
const createProxyOptions = (target, pathRewrite = {}) => ({
  target,
  changeOrigin: true,
  pathRewrite,
  timeout: 30000, // 30 seconds
  proxyTimeout: 30000,
  onError: (err, req, res) => {
    logger.error('Proxy error:', {
      error: err.message,
      target,
      path: req.path,
      method: req.method
    });
    
    if (!res.headersSent) {
      res.status(503).json({
        error: 'SERVICE_UNAVAILABLE',
        message: 'The requested service is temporarily unavailable',
        service: target
      });
    }
  },
  onProxyReq: (proxyReq, req, res) => {
    // Add user information to headers for backend services
    if (req.user) {
      proxyReq.setHeader('X-User-ID', req.user.id);
      proxyReq.setHeader('X-User-Email', req.user.email);
      proxyReq.setHeader('X-User-Roles', JSON.stringify(req.user.roles));
      proxyReq.setHeader('X-User-Permissions', JSON.stringify(req.user.permissions));
    }
    
    // Add request ID for tracing
    const requestId = req.id || Date.now().toString();
    proxyReq.setHeader('X-Request-ID', requestId);
    
    logger.debug('Proxying request:', {
      method: req.method,
      path: req.path,
      target,
      requestId,
      userId: req.user?.id
    });
  },
  onProxyRes: (proxyRes, req, res) => {
    logger.debug('Proxy response:', {
      statusCode: proxyRes.statusCode,
      path: req.path,
      target
    });
  }
});

/**
 * @swagger
 * components:
 *   securitySchemes:
 *     bearerAuth:
 *       type: http
 *       scheme: bearer
 *       bearerFormat: JWT
 */

/**
 * Master Orchestrator Routes
 * Routes for managing the orchestration workflow
 */

/**
 * @swagger
 * /api/orchestrator/projects:
 *   post:
 *     summary: Submit a new project for processing
 *     tags: [Orchestrator]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               name:
 *                 type: string
 *               description:
 *                 type: string
 *               requirements:
 *                 type: object
 *     responses:
 *       201:
 *         description: Project created successfully
 *       401:
 *         description: Authentication required
 *       400:
 *         description: Invalid request data
 */
router.use('/orchestrator',
  authenticateToken,
  createProxyMiddleware(createProxyOptions(
    ORCHESTRATOR_SERVICE_URL,
    { '^/api/orchestrator': '' }
  ))
);

/**
 * Backend Service Routes
 * Routes for backend API operations
 */

/**
 * @swagger
 * /api/backend/projects:
 *   get:
 *     summary: Get all projects
 *     tags: [Backend]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: page
 *         schema:
 *           type: integer
 *           minimum: 1
 *         description: Page number
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           minimum: 1
 *           maximum: 100
 *         description: Number of items per page
 *     responses:
 *       200:
 *         description: Projects retrieved successfully
 *       401:
 *         description: Authentication required
 */
router.use('/backend',
  authenticateToken,
  createProxyMiddleware(createProxyOptions(
    BACKEND_SERVICE_URL,
    { '^/api/backend': '' }
  ))
);

/**
 * Database Service Routes
 * Routes for database operations (admin only)
 */

/**
 * @swagger
 * /api/database/schema:
 *   get:
 *     summary: Get database schema information
 *     tags: [Database]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Schema information retrieved successfully
 *       401:
 *         description: Authentication required
 *       403:
 *         description: Admin access required
 */
router.use('/database',
  authenticateToken,
  requireRoles(['admin']),
  createProxyMiddleware(createProxyOptions(
    DATABASE_SERVICE_URL,
    { '^/api/database': '' }
  ))
);

/**
 * Evolution Engine Routes
 * Routes for code optimization
 */

/**
 * @swagger
 * /api/evolution/optimize:
 *   post:
 *     summary: Start code optimization process
 *     tags: [Evolution]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               projectId:
 *                 type: string
 *               optimizationGoals:
 *                 type: array
 *                 items:
 *                   type: string
 *     responses:
 *       202:
 *         description: Optimization process started
 *       401:
 *         description: Authentication required
 */
router.use('/evolution',
  authenticateToken,
  requirePermissions(['optimize:code']),
  createProxyMiddleware(createProxyOptions(
    ORCHESTRATOR_SERVICE_URL,
    { '^/api/evolution': '/evolution' }
  ))
);

/**
 * Agent Routes
 * Routes for specialized agents
 */

/**
 * Frontend Agent Routes
 */
router.use('/agents/frontend',
  authenticateToken,
  requirePermissions(['generate:frontend']),
  createProxyMiddleware(createProxyOptions(
    ORCHESTRATOR_SERVICE_URL,
    { '^/api/agents/frontend': '/agents/frontend' }
  ))
);

/**
 * Backend Agent Routes
 */
router.use('/agents/backend',
  authenticateToken,
  requirePermissions(['generate:backend']),
  createProxyMiddleware(createProxyOptions(
    ORCHESTRATOR_SERVICE_URL,
    { '^/api/agents/backend': '/agents/backend' }
  ))
);

/**
 * Database Agent Routes
 */
router.use('/agents/database',
  authenticateToken,
  requirePermissions(['design:database']),
  createProxyMiddleware(createProxyOptions(
    ORCHESTRATOR_SERVICE_URL,
    { '^/api/agents/database': '/agents/database' }
  ))
);

/**
 * Testing Agent Routes
 */
router.use('/agents/testing',
  authenticateToken,
  requirePermissions(['generate:tests']),
  createProxyMiddleware(createProxyOptions(
    ORCHESTRATOR_SERVICE_URL,
    { '^/api/agents/testing': '/agents/testing' }
  ))
);

/**
 * DevOps Agent Routes
 */
router.use('/agents/devops',
  authenticateToken,
  requireRoles(['admin', 'devops']),
  createProxyMiddleware(createProxyOptions(
    ORCHESTRATOR_SERVICE_URL,
    { '^/api/agents/devops': '/agents/devops' }
  ))
);

/**
 * Health check endpoint for backend services
 */
router.get('/health/services',
  authenticateToken,
  requireRoles(['admin']),
  asyncHandler(async (req, res) => {
    const healthChecks = await Promise.allSettled([
      checkServiceHealth(ORCHESTRATOR_SERVICE_URL),
      checkServiceHealth(BACKEND_SERVICE_URL),
      checkServiceHealth(DATABASE_SERVICE_URL)
    ]);

    const results = {
      orchestrator: {
        url: ORCHESTRATOR_SERVICE_URL,
        status: healthChecks[0].status === 'fulfilled' ? 'healthy' : 'unhealthy',
        error: healthChecks[0].status === 'rejected' ? healthChecks[0].reason.message : null
      },
      backend: {
        url: BACKEND_SERVICE_URL,
        status: healthChecks[1].status === 'fulfilled' ? 'healthy' : 'unhealthy',
        error: healthChecks[1].status === 'rejected' ? healthChecks[1].reason.message : null
      },
      database: {
        url: DATABASE_SERVICE_URL,
        status: healthChecks[2].status === 'fulfilled' ? 'healthy' : 'unhealthy',
        error: healthChecks[2].status === 'rejected' ? healthChecks[2].reason.message : null
      }
    };

    const allHealthy = Object.values(results).every(service => service.status === 'healthy');
    
    res.status(allHealthy ? 200 : 503).json({
      status: allHealthy ? 'healthy' : 'degraded',
      services: results,
      timestamp: new Date().toISOString()
    });
  })
);

/**
 * Check service health
 */
async function checkServiceHealth(serviceUrl) {
  const fetch = require('node-fetch');
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

  try {
    const response = await fetch(`${serviceUrl}/health`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'User-Agent': 'API-Gateway-Health-Check'
      }
    });

    clearTimeout(timeoutId);
    
    if (response.ok) {
      return { status: 'healthy' };
    } else {
      throw new Error(`Service returned ${response.status}: ${response.statusText}`);
    }
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

module.exports = router;