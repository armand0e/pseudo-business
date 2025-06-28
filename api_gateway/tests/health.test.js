const request = require('supertest');
const { expect } = require('chai');
const app = require('../src/index');

describe('Health Check Routes', () => {
  describe('GET /health', () => {
    it('should return basic health status', (done) => {
      request(app)
        .get('/health')
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('status');
          expect(res.body).to.have.property('timestamp');
          expect(res.body).to.have.property('uptime');
          expect(res.body).to.have.property('version');
          expect(res.body).to.have.property('environment');
          expect(res.body.status).to.equal('healthy');
          
          done();
        });
    });

    it('should include memory and request metrics', (done) => {
      request(app)
        .get('/health')
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('memory');
          expect(res.body).to.have.property('requestCount');
          expect(res.body).to.have.property('errorCount');
          expect(res.body.memory).to.be.an('object');
          expect(res.body.requestCount).to.be.a('number');
          expect(res.body.errorCount).to.be.a('number');
          
          done();
        });
    });
  });

  describe('GET /health/detailed', () => {
    it('should return detailed health information', (done) => {
      request(app)
        .get('/health/detailed')
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('status');
          expect(res.body).to.have.property('timestamp');
          expect(res.body).to.have.property('checks');
          expect(res.body).to.have.property('system');
          
          // Check individual health checks
          expect(res.body.checks).to.have.property('memory');
          expect(res.body.checks).to.have.property('uptime');
          expect(res.body.checks).to.have.property('environment');
          expect(res.body.checks).to.have.property('dependencies');
          
          // Check system information
          expect(res.body.system).to.have.property('platform');
          expect(res.body.system).to.have.property('arch');
          expect(res.body.system).to.have.property('nodeVersion');
          expect(res.body.system).to.have.property('pid');
          
          done();
        });
    });

    it('should have healthy status for all checks in test environment', (done) => {
      request(app)
        .get('/health/detailed')
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body.status).to.equal('healthy');
          expect(res.body.checks.memory.status).to.equal('healthy');
          expect(res.body.checks.uptime.status).to.equal('healthy');
          expect(res.body.checks.environment.status).to.equal('healthy');
          expect(res.body.checks.dependencies.status).to.equal('healthy');
          
          done();
        });
    });
  });

  describe('GET /health/liveness', () => {
    it('should return liveness probe status', (done) => {
      request(app)
        .get('/health/liveness')
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('status');
          expect(res.body).to.have.property('timestamp');
          expect(res.body.status).to.equal('alive');
          
          done();
        });
    });

    it('should respond quickly for liveness probe', (done) => {
      const start = Date.now();
      
      request(app)
        .get('/health/liveness')
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          const duration = Date.now() - start;
          expect(duration).to.be.below(100); // Should respond within 100ms
          
          done();
        });
    });
  });

  describe('GET /health/readiness', () => {
    it('should return readiness probe status', (done) => {
      request(app)
        .get('/health/readiness')
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('status');
          expect(res.body).to.have.property('timestamp');
          expect(res.body.status).to.equal('ready');
          
          done();
        });
    });

    it('should check service readiness conditions', (done) => {
      request(app)
        .get('/health/readiness')
        .end((err, res) => {
          if (err) return done(err);
          
          // In test environment with JWT_SECRET set, should be ready
          expect(res.statusCode).to.equal(200);
          expect(res.body.status).to.equal('ready');
          
          done();
        });
    });
  });

  describe('Health Check Error Conditions', () => {
    it('should handle multiple rapid health check requests', (done) => {
      const requests = [];
      
      for (let i = 0; i < 10; i++) {
        requests.push(
          new Promise((resolve, reject) => {
            request(app)
              .get('/health')
              .expect(200)
              .end((err, res) => {
                if (err) reject(err);
                else resolve(res);
              });
          })
        );
      }
      
      Promise.all(requests)
        .then((responses) => {
          expect(responses).to.have.length(10);
          responses.forEach((res) => {
            expect(res.body.status).to.equal('healthy');
          });
          done();
        })
        .catch(done);
    });

    it('should track request metrics correctly', (done) => {
      let initialRequestCount;
      
      // Get initial request count
      request(app)
        .get('/health')
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          initialRequestCount = res.body.requestCount;
          
          // Make another request
          request(app)
            .get('/health')
            .expect(200)
            .end((err, res) => {
              if (err) return done(err);
              
              // Request count should have increased
              expect(res.body.requestCount).to.be.greaterThan(initialRequestCount);
              
              done();
            });
        });
    });
  });

  describe('Health Check Content Type', () => {
    it('should return JSON content type', (done) => {
      request(app)
        .get('/health')
        .expect('Content-Type', /json/)
        .expect(200)
        .end(done);
    });

    it('should return valid JSON for all health endpoints', (done) => {
      const endpoints = ['/health', '/health/detailed', '/health/liveness', '/health/readiness'];
      const requests = endpoints.map(endpoint => 
        new Promise((resolve, reject) => {
          request(app)
            .get(endpoint)
            .expect('Content-Type', /json/)
            .expect(200)
            .end((err, res) => {
              if (err) reject(err);
              else {
                try {
                  JSON.parse(JSON.stringify(res.body));
                  resolve(res);
                } catch (parseErr) {
                  reject(new Error(`Invalid JSON response from ${endpoint}`));
                }
              }
            });
        })
      );
      
      Promise.all(requests)
        .then(() => done())
        .catch(done);
    });
  });
});