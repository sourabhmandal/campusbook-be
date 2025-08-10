import { z } from 'zod';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import { user, session, account, verification } from '@/src/db/schema';

/**
 * Base validation schemas generated from Drizzle tables
 * These serve as the single source of truth for database operations
 */

// Generate base schemas from Drizzle tables
export const userInsertSchema = createInsertSchema(user, {
  email: z.email('Invalid email format'),
  name: z
    .string()
    .min(2, 'Name must be at least 2 characters')
    .max(50, 'Name cannot exceed 50 characters'),
  emailVerified: z.boolean().default(false),
  createdAt: z.coerce.date(),
  updatedAt: z.coerce.date(),
});

export const userSelectSchema = createSelectSchema(user, {
  email: z.email('Invalid email format'),
  name: z
    .string()
    .min(2, 'Name must be at least 2 characters')
    .max(50, 'Name cannot exceed 50 characters'),
  createdAt: z.coerce.date(),
  updatedAt: z.coerce.date(),
});

export const sessionInsertSchema = createInsertSchema(session, {
  token: z.string().min(1, 'Session token is required'),
  expiresAt: z.coerce.date(),
  createdAt: z.coerce.date().default(() => new Date()),
  updatedAt: z.coerce.date().default(() => new Date()),
  ipAddress: z.string().optional(),
  userAgent: z.string().optional(),
});

export const sessionSelectSchema = createSelectSchema(session, {
  expiresAt: z.coerce.date(),
  createdAt: z.coerce.date(),
  updatedAt: z.coerce.date(),
  ipAddress: z.string().nullable(),
  userAgent: z.string().nullable(),
});

export const accountInsertSchema = createInsertSchema(account, {
  accountId: z.string().min(1, 'Account ID is required'),
  providerId: z.string().min(1, 'Provider ID is required'),
  accessTokenExpiresAt: z.coerce.date().optional(),
  refreshTokenExpiresAt: z.coerce.date().optional(),
  createdAt: z.coerce.date().default(() => new Date()),
  updatedAt: z.coerce.date().default(() => new Date()),
});

export const accountSelectSchema = createSelectSchema(account, {
  accessTokenExpiresAt: z.coerce.date().nullable(),
  refreshTokenExpiresAt: z.coerce.date().nullable(),
  createdAt: z.coerce.date(),
  updatedAt: z.coerce.date(),
});

export const verificationInsertSchema = createInsertSchema(verification, {
  identifier: z.string().min(1, 'Identifier is required'),
  value: z.string().min(1, 'Verification value is required'),
  expiresAt: z.coerce.date(),
  createdAt: z.coerce.date().default(() => new Date()),
  updatedAt: z.coerce.date().default(() => new Date()),
});

export const verificationSelectSchema = createSelectSchema(verification, {
  expiresAt: z.coerce.date(),
  createdAt: z.coerce.date(),
  updatedAt: z.coerce.date(),
});

/**
 * Extended validation schemas for specific use cases
 * These extend the base schemas with additional fields or validation rules
 */

// Authentication-specific fields not in database
export const authFieldsSchema = z.object({
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      'Password must contain uppercase, lowercase, and number'
    ),
  rememberMe: z.boolean().optional().default(false),
  confirmPassword: z.string().optional(),
});

// Common validation patterns
export const commonValidation = {
  email: z.email('Invalid email format'),
  password: authFieldsSchema.shape.password,
  token: z.string().min(1, 'Token is required'),
  id: z.string().min(1, 'ID is required'),
} as const;

/**
 * Type exports for use across the application
 */
export type UserInsert = z.infer<typeof userInsertSchema>;
export type UserSelect = z.infer<typeof userSelectSchema>;
export type SessionInsert = z.infer<typeof sessionInsertSchema>;
export type SessionSelect = z.infer<typeof sessionSelectSchema>;
export type AccountInsert = z.infer<typeof accountInsertSchema>;
export type AccountSelect = z.infer<typeof accountSelectSchema>;
export type VerificationInsert = z.infer<typeof verificationInsertSchema>;
export type VerificationSelect = z.infer<typeof verificationSelectSchema>;
