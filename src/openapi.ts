// OpenAPI specification for CampusBook API
export const openAPISpec = {
  openapi: '3.0.0',
  info: {
    title: 'CampusBook API',
    version: '1.0.0',
    description: 'API documentation for CampusBook backend services',
  },
  servers: [
    {
      url: 'http://localhost:8787',
      description: 'Development server',
    },
    {
      url: 'https://api.campusbook.com',
      description: 'Production server',
    },
  ],
  tags: [
    {
      name: 'Authentication',
      description: 'User authentication and session management',
    },
  ],
  paths: {
    '/auth/signin': {
      post: {
        summary: 'Sign in user',
        description: 'Authenticate a user with email and password',
        tags: ['Authentication'],
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  email: {
                    type: 'string',
                    format: 'email',
                    description: 'User email address',
                  },
                  password: {
                    type: 'string',
                    minLength: 8,
                    description: 'User password',
                  },
                },
                required: ['email', 'password'],
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Successful sign in',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean' },
                    message: { type: 'string' },
                    user: {
                      type: 'object',
                      properties: {
                        id: { type: 'string' },
                        name: { type: 'string' },
                        email: { type: 'string' },
                        emailVerified: { type: 'boolean' },
                        image: { type: 'string', nullable: true },
                        createdAt: { type: 'string' },
                        updatedAt: { type: 'string' },
                      },
                    },
                  },
                },
              },
            },
          },
          '400': {
            description: 'Invalid credentials',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean', enum: [false] },
                    message: { type: 'string' },
                  },
                },
              },
            },
          },
        },
      },
    },
    '/auth/signup': {
      post: {
        summary: 'Sign up user',
        description: 'Create a new user account',
        tags: ['Authentication'],
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  name: {
                    type: 'string',
                    minLength: 2,
                    description: 'User full name',
                  },
                  email: {
                    type: 'string',
                    format: 'email',
                    description: 'User email address',
                  },
                  password: {
                    type: 'string',
                    minLength: 8,
                    description: 'User password',
                  },
                },
                required: ['name', 'email', 'password'],
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Successful registration',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean' },
                    message: { type: 'string' },
                    user: {
                      type: 'object',
                      properties: {
                        id: { type: 'string' },
                        name: { type: 'string' },
                        email: { type: 'string' },
                        emailVerified: { type: 'boolean' },
                        image: { type: 'string', nullable: true },
                        createdAt: { type: 'string' },
                        updatedAt: { type: 'string' },
                      },
                    },
                  },
                },
              },
            },
          },
          '409': {
            description: 'User already exists',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean', enum: [false] },
                    message: { type: 'string' },
                  },
                },
              },
            },
          },
        },
      },
    },
    '/auth/signout': {
      post: {
        summary: 'Sign out user',
        description: 'End the current user session',
        tags: ['Authentication'],
        responses: {
          '200': {
            description: 'Successful sign out',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean' },
                    message: { type: 'string' },
                  },
                },
              },
            },
          },
        },
      },
    },
    '/auth/session': {
      get: {
        summary: 'Get current session',
        description: 'Retrieve information about the current authenticated user',
        tags: ['Authentication'],
        responses: {
          '200': {
            description: 'Session information',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean' },
                    user: {
                      type: 'object',
                      properties: {
                        id: { type: 'string' },
                        name: { type: 'string' },
                        email: { type: 'string' },
                        emailVerified: { type: 'boolean' },
                        image: { type: 'string', nullable: true },
                        createdAt: { type: 'string' },
                        updatedAt: { type: 'string' },
                      },
                    },
                  },
                },
              },
            },
          },
          '401': {
            description: 'Not authenticated',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean', enum: [false] },
                    message: { type: 'string' },
                  },
                },
              },
            },
          },
        },
      },
    },
  },
  components: {
    securitySchemes: {
      cookieAuth: {
        type: 'apiKey',
        in: 'cookie',
        name: 'session-token',
      },
    },
  },
  security: [
    {
      cookieAuth: [],
    },
  ],
};
