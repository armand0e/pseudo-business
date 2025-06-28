const winston = require('winston');

// Define log levels
const levels = {
  error: 0,
  warn: 1,
  info: 2,
  http: 3,
  debug: 4,
};

// Define colors for each level
const colors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  http: 'magenta',
  debug: 'white',
};

// Add colors to winston
winston.addColors(colors);

// Define which log level to use based on environment
const level = () => {
  const env = process.env.NODE_ENV || 'development';
  const isDevelopment = env === 'development';
  return isDevelopment ? 'debug' : 'warn';
};

// Define format for logs
const format = winston.format.combine(
  // Add timestamp
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
  // Add colors if outputting to console
  winston.format.colorize({ all: true }),
  // Add error stack traces
  winston.format.errors({ stack: true }),
  // Define format for each log
  winston.format.printf(
    (info) => `${info.timestamp} ${info.level}: ${info.message}${info.stack ? '\n' + info.stack : ''}`
  ),
);

// Define transports
const transports = [
  // Console transport
  new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  }),
  
  // File transport for errors
  new winston.transports.File({
    filename: 'logs/error.log',
    level: 'error',
    format: winston.format.combine(
      winston.format.uncolorize(),
      winston.format.json()
    )
  }),
  
  // File transport for all logs
  new winston.transports.File({
    filename: 'logs/combined.log',
    format: winston.format.combine(
      winston.format.uncolorize(),
      winston.format.json()
    )
  }),
];

// Create logger instance
const logger = winston.createLogger({
  level: level(),
  levels,
  format,
  transports,
  // Don't exit on handled exceptions
  exitOnError: false,
});

// Create stream for morgan HTTP request logging
logger.stream = {
  write: (message) => {
    logger.http(message.trim());
  },
};

// Add request logging middleware
logger.requestLogger = (req, res, next) => {
  const start = Date.now();
  
  // Override res.end to log after response
  const originalEnd = res.end;
  res.end = function(...args) {
    const duration = Date.now() - start;
    const logData = {
      method: req.method,
      url: req.url,
      status: res.statusCode,
      duration: `${duration}ms`,
      userAgent: req.get('User-Agent'),
      ip: req.ip || req.connection.remoteAddress,
      userId: req.user ? req.user.id : 'anonymous'
    };
    
    // Log based on status code
    if (res.statusCode >= 500) {
      logger.error('HTTP Request', logData);
    } else if (res.statusCode >= 400) {
      logger.warn('HTTP Request', logData);
    } else {
      logger.http('HTTP Request', logData);
    }
    
    originalEnd.apply(this, args);
  };
  
  next();
};

// Security logging functions
logger.security = {
  invalidToken: (req, reason) => {
    logger.warn('Security: Invalid token', {
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      url: req.url,
      reason,
      timestamp: new Date().toISOString()
    });
  },
  
  authFailure: (req, email, reason) => {
    logger.warn('Security: Authentication failure', {
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      email,
      reason,
      timestamp: new Date().toISOString()
    });
  },
  
  rateLimitExceeded: (req, limit) => {
    logger.warn('Security: Rate limit exceeded', {
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      url: req.url,
      limit,
      timestamp: new Date().toISOString()
    });
  },
  
  suspiciousActivity: (req, activity) => {
    logger.error('Security: Suspicious activity detected', {
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      url: req.url,
      activity,
      headers: req.headers,
      timestamp: new Date().toISOString()
    });
  }
};

// Application-specific logging functions
logger.app = {
  serviceCall: (service, endpoint, duration, success) => {
    const logData = {
      service,
      endpoint,
      duration: `${duration}ms`,
      success,
      timestamp: new Date().toISOString()
    };
    
    if (success) {
      logger.info('Service call successful', logData);
    } else {
      logger.error('Service call failed', logData);
    }
  },
  
  configLoaded: (config) => {
    logger.info('Configuration loaded', {
      environment: config.NODE_ENV,
      port: config.PORT,
      timestamp: new Date().toISOString()
    });
  },
  
  serverStarted: (port) => {
    logger.info(`API Gateway started on port ${port}`, {
      port,
      environment: process.env.NODE_ENV,
      timestamp: new Date().toISOString()
    });
  },
  
  serverShutdown: () => {
    logger.info('API Gateway shutting down', {
      timestamp: new Date().toISOString()
    });
  }
};

// Error handling for uncaught exceptions
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

module.exports = logger;