const request = require('supertest');
const { expect } = require('chai');
const app = require('../src/index');

describe('Authentication Routes', () => {
  describe('POST /auth/register', () => {
    it('should register a new user successfully', (done) => {
      const newUser = {
        email: 'test@example.com',
        password: 'testpassword123',
        role: 'user'
      };

      request(app)
        .post('/auth/register')
        .send(newUser)
        .expect(201)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('token');
          expect(res.body).to.have.property('user');
          expect(res.body.user.email).to.equal(newUser.email);
          expect(res.body.user.role).to.equal(newUser.role);
          expect(res.body.user).to.not.have.property('password');
          
          done();
        });
    });

    it('should return validation error for invalid email', (done) => {
      const invalidUser = {
        email: 'invalid-email',
        password: 'testpassword123',
        role: 'user'
      };

      request(app)
        .post('/auth/register')
        .send(invalidUser)
        .expect(400)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('validation');
          
          done();
        });
    });

    it('should return validation error for short password', (done) => {
      const invalidUser = {
        email: 'test@example.com',
        password: '123',
        role: 'user'
      };

      request(app)
        .post('/auth/register')
        .send(invalidUser)
        .expect(400)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('validation');
          
          done();
        });
    });

    it('should return error for duplicate email', (done) => {
      const user = {
        email: 'duplicate@example.com',
        password: 'testpassword123',
        role: 'user'
      };

      // Register user first time
      request(app)
        .post('/auth/register')
        .send(user)
        .expect(201)
        .end((err, res) => {
          if (err) return done(err);
          
          // Try to register same user again
          request(app)
            .post('/auth/register')
            .send(user)
            .expect(400)
            .end((err, res) => {
              if (err) return done(err);
              
              expect(res.body).to.have.property('error');
              expect(res.body.error).to.include('already exists');
              
              done();
            });
        });
    });
  });

  describe('POST /auth/login', () => {
    beforeEach((done) => {
      // Register a test user before each login test
      const testUser = {
        email: 'login-test@example.com',
        password: 'testpassword123',
        role: 'user'
      };

      request(app)
        .post('/auth/register')
        .send(testUser)
        .expect(201)
        .end(done);
    });

    it('should login with valid credentials', (done) => {
      const credentials = {
        email: 'login-test@example.com',
        password: 'testpassword123'
      };

      request(app)
        .post('/auth/login')
        .send(credentials)
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('token');
          expect(res.body).to.have.property('user');
          expect(res.body.user.email).to.equal(credentials.email);
          expect(res.body.user).to.not.have.property('password');
          
          done();
        });
    });

    it('should return error for invalid email', (done) => {
      const credentials = {
        email: 'nonexistent@example.com',
        password: 'testpassword123'
      };

      request(app)
        .post('/auth/login')
        .send(credentials)
        .expect(401)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('Invalid credentials');
          
          done();
        });
    });

    it('should return error for invalid password', (done) => {
      const credentials = {
        email: 'login-test@example.com',
        password: 'wrongpassword'
      };

      request(app)
        .post('/auth/login')
        .send(credentials)
        .expect(401)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('Invalid credentials');
          
          done();
        });
    });

    it('should return validation error for missing fields', (done) => {
      const credentials = {
        email: 'login-test@example.com'
        // password missing
      };

      request(app)
        .post('/auth/login')
        .send(credentials)
        .expect(400)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('validation');
          
          done();
        });
    });
  });

  describe('GET /auth/profile', () => {
    let authToken;

    before((done) => {
      // Register and login to get auth token
      const testUser = {
        email: 'profile-test@example.com',
        password: 'testpassword123',
        role: 'user'
      };

      request(app)
        .post('/auth/register')
        .send(testUser)
        .expect(201)
        .end((err, res) => {
          if (err) return done(err);
          authToken = res.body.token;
          done();
        });
    });

    it('should return user profile with valid token', (done) => {
      request(app)
        .get('/auth/profile')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('user');
          expect(res.body.user.email).to.equal('profile-test@example.com');
          expect(res.body.user).to.not.have.property('password');
          
          done();
        });
    });

    it('should return error without token', (done) => {
      request(app)
        .get('/auth/profile')
        .expect(401)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('token');
          
          done();
        });
    });

    it('should return error with invalid token', (done) => {
      request(app)
        .get('/auth/profile')
        .set('Authorization', 'Bearer invalid-token')
        .expect(401)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('token');
          
          done();
        });
    });

    it('should return error with malformed authorization header', (done) => {
      request(app)
        .get('/auth/profile')
        .set('Authorization', 'InvalidFormat token')
        .expect(401)
        .end((err, res) => {
          if (err) return done(err);
          
          expect(res.body).to.have.property('error');
          expect(res.body.error).to.include('token');
          
          done();
        });
    });
  });
});