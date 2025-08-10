import { z } from 'zod';
import { oc } from '@orpc/contract';
import {
  userSelectSchema,
  userInsertSchema,
  authFieldsSchema,
  commonValidation,
} from '../db/validation';

/**
 * Authentication API input schemas
 * These use z.pick() and extend from base schemas for consistency
 */

// Login input - picks email from user schema + password from auth fields
export const loginInputSchema = userSelectSchema.pick({ email: true }).extend({
  password: z.string().min(1, 'Password is required'),
  rememberMe: authFieldsSchema.shape.rememberMe,
});

// Register input - picks name, email from user schema + password validation
export const registerInputSchema = userInsertSchema
  .pick({ name: true, email: true })
  .extend({
    password: authFieldsSchema.shape.password,
  });

// Forgot password input
export const forgotPasswordInputSchema = userSelectSchema.pick({
  email: true,
});

// Reset password input
export const resetPasswordInputSchema = z.object({
  token: commonValidation.token,
  password: authFieldsSchema.shape.password,
});

/**
 * API Response schemas
 */

// User response - excludes sensitive fields, formats dates as strings
export const userResponseSchema = userSelectSchema
  .pick({
    id: true,
    name: true,
    email: true,
    emailVerified: true,
    image: true,
  })
  .extend({
    createdAt: z.string(),
    updatedAt: z.string(),
  });

// Authentication response
export const authResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  user: userResponseSchema.nullable(),
});

// Standard error response
export const errorResponseSchema = z.object({
  success: z.literal(false),
  message: z.string(),
  errors: z
    .array(
      z.object({
        field: z.string(),
        message: z.string(),
      })
    )
    .optional(),
});

// Standard success response
export const successResponseSchema = z.object({
  success: z.literal(true),
  message: z.string(),
});

// Session response
export const sessionResponseSchema = z.object({
  success: z.boolean(),
  user: userResponseSchema.nullable(),
});

/**
 * oRPC Contract Definition
 */
export const authContract = oc.router({
  signin: oc
    .input(loginInputSchema)
    .output(authResponseSchema)
    .meta({
      openapi: {
        method: 'POST',
        path: '/auth/signin',
        summary: 'User login',
        description: 'Authenticate a user with email and password',
        tags: ['Authentication'],
      },
    }),

  signup: oc
    .input(registerInputSchema)
    .output(authResponseSchema)
    .meta({
      openapi: {
        method: 'POST',
        path: '/auth/signup',
        summary: 'User registration',
        description: 'Create a new user account',
        tags: ['Authentication'],
      },
    }),

  signout: oc
    .input(z.object({}))
    .output(successResponseSchema)
    .meta({
      openapi: {
        method: 'POST',
        path: '/auth/signout',
        summary: 'User logout',
        description: 'End the current user session',
        tags: ['Authentication'],
      },
    }),

  session: oc
    .input(z.object({}))
    .output(sessionResponseSchema)
    .meta({
      openapi: {
        method: 'GET',
        path: '/auth/session',
        summary: 'Get current user',
        description: 'Retrieve information about the authenticated user',
        tags: ['Authentication'],
      },
    }),

  forgotPassword: oc
    .input(forgotPasswordInputSchema)
    .output(successResponseSchema)
    .meta({
      openapi: {
        method: 'POST',
        path: '/auth/forgot-password',
        summary: 'Forgot password',
        description: 'Send password reset email',
        tags: ['Authentication'],
      },
    }),

  resetPassword: oc
    .input(resetPasswordInputSchema)
    .output(successResponseSchema)
    .meta({
      openapi: {
        method: 'POST',
        path: '/auth/reset-password',
        summary: 'Reset password',
        description: 'Reset password using reset token',
        tags: ['Authentication'],
      },
    }),
});

export type AuthContract = typeof authContract;

// Type exports for API handlers
export type LoginInput = z.infer<typeof loginInputSchema>;
export type RegisterInput = z.infer<typeof registerInputSchema>;
export type ForgotPasswordInput = z.infer<typeof forgotPasswordInputSchema>;
export type ResetPasswordInput = z.infer<typeof resetPasswordInputSchema>;
export type UserResponse = z.infer<typeof userResponseSchema>;
export type AuthResponse = z.infer<typeof authResponseSchema>;
export type ErrorResponse = z.infer<typeof errorResponseSchema>;
