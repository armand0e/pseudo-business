const request = require('supertest');
const { expect } = require('chai');
const nock = require('nock');
const app = require('../src/index');

describe('Proxy Routes', () => {
  let authToken;
  let adminToken;

  before((done) => {
    // Register and login to get auth tokens
    const testUser = {
      email: 'proxy-test@example.com',
      password: 'testpassword123',
      role: 'user'
    };

    const adminUser = {
      email: 'admin-test@example.com',
      password: 'adminpassword123',
      role: 'admin'
    };

    // Register regular user
    request(app)
      .post('/auth/register')
      .send(testUser)
      .expect(201)
      .end((err, res) => {
        if (err) return done(err);
        authToken = res.body.token;

        // Register admin user
        request(app)
          .post('/auth/register')
          .send(adminUser)
          .expect(201)
          .end((err, res) => {
            if (err) return done(err);
            adminToken = res.body.token;
            done();
          });
      });
  });

  afterEach(() => {
    // Clean up nock mocks after each test
    nock.cleanAll();
  });

  describe('GET /api/orchestrator/*', () => {
    it('should proxy authenticated requests to master orchestrator', (done) => {
      // Mock the master orchestrator service
      const mockResponse = { message: 'Hello from orchestrator', tasks: [] };
      nock('http://localhost:8000')
        .get('/api/tasks')
        .reply(200, mockResponse);

      request(app)
        .get('/api/orchestrator/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.deep.equal(mockResponse);
          done();
        });
    });

    it('should return 401 without authentication', (done) => {
      request(app)
        .get('/api/orchestrator/api/tasks')
        .expect(401)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('token');
          done();
        });
    });

    it('should handle orchestrator service errors', (done) => {
      // Mock service returning an error
      nock('http://localhost:8000')
        .get('/api/tasks')
        .reply(500, { error: 'Internal service error' });

      request(app)
        .get('/api/orchestrator/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(500)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          done();
        });
    });

    it('should handle orchestrator service timeout', (done) => {
      // Mock service with delayed response
      nock('http://localhost:8000')
        .get('/api/tasks')
        .delay(35000) // Longer than timeout
        .reply(200, { message: 'delayed response' });

      request(app)
        .get('/api/orchestrator/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(504)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('timeout');
          done();
        });
    });
  });

  describe('POST /api/orchestrator/*', () => {
    it('should proxy POST requests with body', (done) => {
      const requestBody = { task: 'Create new workflow', priority: 'high' };
      const mockResponse = { id: '123', status: 'created' };

      nock('http://localhost:8000')
        .post('/api/tasks', requestBody)
        .reply(201, mockResponse);

      request(app)
        .post('/api/orchestrator/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)
        .send(requestBody)
        .expect(201)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.deep.equal(mockResponse);
          done();
        });
    });

    it('should forward user context in headers', (done) => {
      const requestBody = { task: 'Test task' };

      nock('http://localhost:8000')
        .post('/api/tasks', requestBody)
        .matchHeader('x-user-id', /^[a-f0-9-]+$/) // UUID pattern
        .matchHeader('x-user-email', 'proxy-test@example.com')
        .matchHeader('x-user-role', 'user')
        .reply(201, { status: 'ok' });

      request(app)
        .post('/api/orchestrator/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)
        .send(requestBody)
        .expect(201)
        .end(done);
    });
  });

  describe('GET /api/backend/*', () => {
    it('should proxy to backend agent', (done) => {
      const mockResponse = { data: 'backend data' };
      nock('http://localhost:8001')
        .get('/api/data')
        .reply(200, mockResponse);

      request(app)
        .get('/api/backend/api/data')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.deep.equal(mockResponse);
          done();
        });
    });

    it('should handle backend agent unavailability', (done) => {
      // No mock set up, simulating service unavailability
      request(app)
        .get('/api/backend/api/data')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(503)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('unavailable');
          done();
        });
    });
  });

  describe('GET /api/database/*', () => {
    it('should proxy to database agent', (done) => {
      const mockResponse = { records: [], count: 0 };
      nock('http://localhost:8002')
        .get('/api/query')
        .reply(200, mockResponse);

      request(app)
        .get('/api/database/api/query')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.deep.equal(mockResponse);
          done();
        });
    });

    it('should require authentication for database operations', (done) => {
      request(app)
        .get('/api/database/api/query')
        .expect(401)
        .end(done);
    });
  });

  describe('GET /api/agents/*', () => {
    it('should proxy to specialized agents', (done) => {
      const mockResponse = { agent: 'nlp-agent', result: 'processed' };
      nock('http://localhost:8003')
        .get('/nlp/analyze')
        .reply(200, mockResponse);

      request(app)
        .get('/api/agents/nlp/analyze')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.deep.equal(mockResponse);
          done();
        });
    });

    it('should handle agent-specific errors', (done) => {
      nock('http://localhost:8003')
        .get('/nlp/analyze')
        .reply(422, { error: 'Invalid input format' });

      request(app)
        .get('/api/agents/nlp/analyze')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(422)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          done();
        });
    });
  });

  describe('Admin Routes', () => {
    describe('GET /api/admin/*', () => {
      it('should allow admin access', (done) => {
        const mockResponse = { users: [], systems: [] };
        nock('http://localhost:8000')
          .get('/admin/dashboard')
          .reply(200, mockResponse);

        request(app)
          .get('/api/admin/dashboard')
          .set('Authorization', `Bearer ${adminToken}`)
          .expect(200)
          .end((err, res) => {
            if (err) return done(err);
            
            expect(res.body).to.deep.equal(mockResponse);
            done();
          });
      });

      it('should deny non-admin access', (done) => {
        request(app)
          .get('/api/admin/dashboard')
          .set('Authorization', `Bearer ${authToken}`)
          .expect(403)
          .end((err, res) => {
            if (err) return done(err);
            
            expect(res.body).to.have.property('error');
            expect(res.body.error).to.include('Insufficient permissions');
            done();
          });
      });

      it('should deny unauthenticated access', (done) => {
        request(app)
          .get('/api/admin/dashboard')
          .expect(401)
          .end(done);
      });
    });
  });

  describe('Health Check Routes', () => {
    describe('GET /api/*/health', () => {
      it('should check orchestrator health', (done) => {
        const mockResponse = { status: 'healthy', service: 'orchestrator' };
        nock('http://localhost:8000')
          .get('/health')
          .reply(200, mockResponse);

        request(app)
          .get('/api/orchestrator/health')
          .expect(200)
          .end((err, res) => {
            if (err) return done(err);
            
            expect(res.body).to.deep.equal(mockResponse);
            done();
          });
      });

      it('should check backend agent health', (done) => {
        const mockResponse = { status: 'healthy', service: 'backend-agent' };
        nock('http://localhost:8001')
          .get('/health')
          .reply(200, mockResponse);

        request(app)
          .get('/api/backend/health')
          .expect(200)
          .end((err, res) => {
            if (err) return done(err);
            
            expect(res.body).to.deep.equal(mockResponse);
            done();
          });
      });

      it('should detect unhealthy services', (done) => {
        nock('http://localhost:8002')
          .get('/health')
          .reply(503, { status: 'unhealthy', error: 'Database connection failed' });

        request(app)
          .get('/api/database/health')
          .expect(503)
          .end((err, res) => {
            if (err) return done(err);
            
            expect(res.body).to.have.property('status');
            expect(res.body.status).to.equal('unhealthy');
            done();
          });
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', (done) => {
      // Simulate network error by not mocking the service
      request(app)
        .get('/api/orchestrator/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(503)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('Service unavailable');
          done();
        });
    });

    it('should preserve error status codes from backend', (done) => {
      nock('http://localhost:8000')
        .get('/api/tasks/nonexistent')
        .reply(404, { error: 'Task not found' });

      request(app)
        .get('/api/orchestrator/api/tasks/nonexistent')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(404)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.equal('Task not found');
          done();
        });
    });

    it('should handle invalid JSON responses', (done) => {
      nock('http://localhost:8000')
        .get('/api/tasks')
        .reply(200, 'invalid json response');

      request(app)
        .get('/api/orchestrator/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(502)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('Invalid response');
          done();
        });
    });
  });

  describe('Request Logging', () => {
    it('should log successful proxy requests', (done) => {
      const mockResponse = { data: 'test' };
      nock('http://localhost:8000')
        .get('/api/test')
        .reply(200, mockResponse);

      request(app)
        .get('/api/orchestrator/api/test')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          // Request should be logged (we can't easily test this without
          // complex logging infrastructure, but the test verifies the
          // request completes successfully)
          expect(res.body).to.deep.equal(mockResponse);
          done();
        });
    });
  });
});