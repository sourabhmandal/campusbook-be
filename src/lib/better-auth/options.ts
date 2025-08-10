import { BetterAuthOptions } from 'better-auth';

/**
 * Custom options for Better Auth
 *
 * Docs: https://www.better-auth.com/docs/reference/options
 */
export const betterAuthOptions: BetterAuthOptions = {
  /**
   * The name of the application.
   */
  appName: 'CampusBook',
  /**
   * Base path for Better Auth.
   * @default "/api/auth"
   */
  basePath: '/api/auth',

  /**
   * Email and password authentication configuration
   */
  emailAndPassword: {
    enabled: true,
    requireEmailVerification: false, // Set to true in production
    autoSignIn: true,
  },

  /**
   * Session configuration
   */
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // 1 day
  },

  /**
   * User configuration
   */
  user: {
    additionalFields: {
      // Add any additional fields you want to store
    },
  },
};
