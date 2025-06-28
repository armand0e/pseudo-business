const { execSync } = require('child_process');
const path = require('path');

// Set test environment
process.env.NODE_ENV = 'test';
process.env.PORT = 3001;
process.env.JWT_SECRET = 'test-jwt-secret-key';
process.env.RATE_LIMIT_WINDOW_MS = 60000;
process.env.RATE_LIMIT_MAX_REQUESTS = 1000;

// Create logs directory for tests
const logsDir = path.join(__dirname, '..', 'logs');
try {
  execSync(`mkdir -p ${logsDir}`, { stdio: 'ignore' });
} catch (error) {
  // Directory might already exist
}

// Global test setup
before(function() {
  this.timeout(10000);
  console.log('Setting up test environment...');
});

// Global test teardown
after(function() {
  console.log('Cleaning up test environment...');
});

// Handle uncaught exceptions in tests
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception in tests:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection in tests:', reason);
  process.exit(1);
});