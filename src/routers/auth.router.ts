import { os } from '@orpc/server';
import { z } from 'zod';
import {
  loginInputSchema,
  registerInputSchema,
  authResponseSchema,
  errorResponseSchema,
  successResponseSchema,
  sessionResponseSchema,
} from '../contracts/auth';

export const authRouter = os.router({
  signIn: os
    .input(loginInputSchema)
    .output(authResponseSchema)
    .meta({
      openapi: {
        method: 'POST',
        path: '/auth/signin',
        summary: 'Sign in user',
        description: 'Authenticate a user with email and password',
        tags: ['Authentication'],
        responses: {
          200: {
            description: 'Successful sign in',
            content: {
              'application/json': {
                schema: authResponseSchema,
              },
            },
          },
          400: {
            description: 'Invalid credentials',
            content: {
              'application/json': {
                schema: errorResponseSchema,
              },
            },
          },
          500: {
            description: 'Internal server error',
            content: {
              'application/json': {
                schema: errorResponseSchema,
              },
            },
          },
        },
      },
    })
    .handler(async ({ input, context }) => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const auth = (context as any).auth;
        const result = await auth.api.signInEmail({
          body: {
            email: input.email,
            password: input.password,
          },
        });

        if (result.user) {
          return {
            success: true,
            message: 'Signed in successfully',
            user: {
              id: result.user.id,
              name: result.user.name,
              email: result.user.email,
              emailVerified: result.user.emailVerified,
              image: result.user.image,
              createdAt: result.user.createdAt.toISOString(),
              updatedAt: result.user.updatedAt.toISOString(),
            },
          };
        }

        return {
          success: false,
          message: 'Invalid email or password',
          user: null,
        };
      } catch {
        return {
          success: false,
          message: 'Sign in failed',
          user: null,
        };
      }
    }),

  signUp: os
    .input(registerInputSchema)
    .output(authResponseSchema)
    .meta({
      openapi: {
        method: 'POST',
        path: '/auth/signup',
        summary: 'Sign up user',
        description: 'Create a new user account',
        tags: ['Authentication'],
        responses: {
          200: {
            description: 'Successful registration',
            content: {
              'application/json': {
                schema: authResponseSchema,
              },
            },
          },
          400: {
            description: 'Invalid input data',
            content: {
              'application/json': {
                schema: errorResponseSchema,
              },
            },
          },
          409: {
            description: 'User already exists',
            content: {
              'application/json': {
                schema: errorResponseSchema,
              },
            },
          },
          500: {
            description: 'Internal server error',
            content: {
              'application/json': {
                schema: errorResponseSchema,
              },
            },
          },
        },
      },
    })
    .handler(async ({ input, context }) => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const auth = (context as any).auth;
        const result = await auth.api.signUpEmail({
          body: {
            name: input.name,
            email: input.email,
            password: input.password,
          },
        });

        if (result.user) {
          return {
            success: true,
            message: 'Account created successfully',
            user: {
              id: result.user.id,
              name: result.user.name,
              email: result.user.email,
              emailVerified: result.user.emailVerified,
              image: result.user.image,
              createdAt: result.user.createdAt.toISOString(),
              updatedAt: result.user.updatedAt.toISOString(),
            },
          };
        }

        return {
          success: false,
          message: 'Registration failed',
          user: null,
        };
      } catch {
        return {
          success: false,
          message: 'Registration failed',
          user: null,
        };
      }
    }),

  signOut: os
    .input(z.object({}))
    .output(successResponseSchema)
    .meta({
      openapi: {
        method: 'POST',
        path: '/auth/signout',
        summary: 'Sign out user',
        description: 'End the current user session',
        tags: ['Authentication'],
        responses: {
          200: {
            description: 'Successful sign out',
            content: {
              'application/json': {
                schema: successResponseSchema,
              },
            },
          },
          500: {
            description: 'Internal server error',
            content: {
              'application/json': {
                schema: errorResponseSchema,
              },
            },
          },
        },
      },
    })
    .handler(async ({ context }) => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const auth = (context as { auth: any }).auth;
        await auth.api.signOut();
        return {
          success: true as const,
          message: 'Signed out successfully',
        };
      } catch {
        throw new Error('Sign out failed');
      }
    }),

  getSession: os
    .input(z.object({}))
    .output(sessionResponseSchema)
    .meta({
      openapi: {
        method: 'GET',
        path: '/auth/session',
        summary: 'Get current session',
        description:
          'Retrieve information about the current authenticated user',
        tags: ['Authentication'],
        responses: {
          200: {
            description: 'Session information',
            content: {
              'application/json': {
                schema: sessionResponseSchema,
              },
            },
          },
          401: {
            description: 'Not authenticated',
            content: {
              'application/json': {
                schema: errorResponseSchema,
              },
            },
          },
          500: {
            description: 'Internal server error',
            content: {
              'application/json': {
                schema: errorResponseSchema,
              },
            },
          },
        },
      },
    })
    .handler(async ({ context }) => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const auth = (context as { auth: any }).auth;
        const session = await auth.api.getSession();

        if (session.user) {
          return {
            success: true,
            user: {
              id: session.user.id,
              name: session.user.name,
              email: session.user.email,
              emailVerified: session.user.emailVerified,
              image: session.user.image,
              createdAt: session.user.createdAt.toISOString(),
              updatedAt: session.user.updatedAt.toISOString(),
            },
          };
        }

        return {
          success: false,
          user: null,
        };
      } catch {
        return {
          success: false,
          user: null,
        };
      }
    }),
});
