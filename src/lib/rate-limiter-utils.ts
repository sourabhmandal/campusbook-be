import { Context } from 'hono';

/**
 * Generate a unique key for rate limiting based on IP and path
 */
export const pathKeyGenerator = (c: Context): string => {
  const ip =
    c.req.header('Remote-Addr') ||
    c.req.header('CF-Connecting-IP') ||
    c.req.header('X-Forwarded-For') ||
    c.req.header('X-Real-IP') ||
    'unknown';
  const path = c.req.path;
  return `rate_limit:${ip}:${path}`;
};
