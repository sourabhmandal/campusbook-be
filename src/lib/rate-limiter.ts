import { Context, Next } from 'hono';

/**
 * Rate limiter configuration options
 */
interface RateLimiterOptions {
  /** Maximum number of requests per window */
  maxRequests: number;
  /** Time window in seconds */
  windowSeconds: number;
  /** Custom error message */
  message: string;
  /** Skip rate limiting for certain conditions */
  skip: (c: Context) => boolean;
  /** Headers to include in response */
  headers?: boolean;
}

/**
 * Rate limit data structure
 */
interface RateLimit {
  count: number;
  resetTime: number;
  firstRequest: number;
}

/**
 * Cloudflare KV store for distributed rate limiting
 */
class CloudflareKVStore {
  constructor(private kv: KVNamespace) { }

  async get(key: string): Promise<RateLimit | undefined> {
    const data = await this.kv.get(key);
    if (!data) return undefined;

    const limit: RateLimit = JSON.parse(data);
    const now = Date.now();

    // Don't auto-delete expired entries here, let increment handle it
    if (now > limit.resetTime) {
      return undefined; // Return undefined but don't delete yet
    }
    return limit;
  }

  async set(key: string, limit: RateLimit): Promise<void> {
    console.log(`Setting rate limit for key: ${key}`, limit);
    const ttl = Math.max(1, Math.ceil((limit.resetTime - Date.now()) / 1000));
    await this.kv.put(key, JSON.stringify(limit), { expirationTtl: ttl });
  }

  async increment(key: string, windowMs: number): Promise<RateLimit> {
    const now = Date.now();
    const data = await this.kv.get(key);

    if (!data) {
      // No existing entry, create new one
      const newLimit: RateLimit = {
        count: 1,
        resetTime: now + windowMs,
        firstRequest: now,
      };
      await this.set(key, newLimit);
      return newLimit;
    }

    const existing: RateLimit = JSON.parse(data);

    // Check if we're still within the same window
    if (now < existing.resetTime) {
      // Still within the window, increment count
      existing.count++;
      await this.set(key, existing);
      return existing;
    } else {
      // Window has expired, start a new window
      const newLimit: RateLimit = {
        count: 1,
        resetTime: now + windowMs,
        firstRequest: now,
      };
      await this.set(key, newLimit);
      return newLimit;
    }
  }
}

/**
 * Auth key generator (same as used in authRateLimiter)
 */
export const pathKeyGenerator = (c: Context): string => {
  const forwarded = c.req.header('CF-Connecting-IP') ||
    c.req.header('X-Forwarded-For') ||
    c.req.header('X-Real-IP');

  if (forwarded) {
    return forwarded.split(',')[0].trim();
  }

  const ip = c.req.header('Remote-Addr') || 'unknown';
  const path = c.req.path;
  return `rate_limit:${ip}:${path}`;
};

/**
 * Enhanced rate limiter with DDoS protection
 */
export const rlConfig: RateLimiterOptions = {
  maxRequests: 100,
  windowSeconds: 60,
  message: 'API rate limit exceeded. Please slow down your requests.',
  headers: true,
  skip: (c: Context) => {
    // Skip rate limiting for health check and status endpoints
    return c.req.path === '/api/rate-status';
  }
}

export function rateLimiter() {
  const windowMs = rlConfig.windowSeconds * 1000;

  return async (c: Context, next: Next) => {
    try {
      // Skip rate limiting if condition is met
      if (rlConfig.skip && rlConfig.skip(c)) {
        await next();
        return;
      }
      

      const key = pathKeyGenerator(c);

      if (!c.env?.RATE_LIMITER_KV) {
        // return error if KV store is not available
        return c.json({
          error: 'Service Unavailable',
          message: 'Rate limiting store not configured',
          statusCode: 503,
          timestamp: new Date().toISOString()
        }, 503);
      }
      // Use KV store if available, otherwise fall back to memory store
      const store = new CloudflareKVStore(c.env.RATE_LIMITER_KV)
      const limit = await store.increment(key, windowMs)
      // Add rate limit headers if enabled
      if (rlConfig.headers) {
        const remaining = Math.max(0, rlConfig.maxRequests - limit.count);
        const resetTime = Math.ceil(limit.resetTime / 1000);

        c.header('X-RateLimit-Limit', rlConfig.maxRequests.toString());
        c.header('X-RateLimit-Remaining', remaining.toString());
        c.header('X-RateLimit-Reset', resetTime.toString());
        c.header('X-RateLimit-Policy', `${rlConfig.maxRequests};w=${rlConfig.windowSeconds}`);
      }

      // Check if rate limit exceeded
      if (limit.count > rlConfig.maxRequests) {
        const retryAfter = Math.ceil((limit.resetTime - Date.now()) / 1000);

        return c.json({
          error: 'Rate Limit Exceeded',
          message: rlConfig.message,
          statusCode: 429,
          timestamp: new Date().toISOString(),
          retryAfter,
        }, 429, {
          'Retry-After': retryAfter.toString(),
        });
      }

      await next();
    } catch {
      // Continue processing if rate limiter fails to maintain availability
      await next();
    }
  };
}

/**
 * Get rate limit status for a specific key
 */
export const getRateLimitStatus = async (
  kv: KVNamespace,
  key: string,
  config: { maxRequests: number; windowSeconds: number }
) => {
  const data = await kv.get(key);
  const now = Date.now();

  if (!data) {
    return {
      count: 0,
      remaining: config.maxRequests,
      resetIn: config.windowSeconds,
      exceeded: false
    };
  }

  const limit: RateLimit = JSON.parse(data);

  // Check if expired
  if (now > limit.resetTime) {
    return {
      count: 0,
      remaining: config.maxRequests,
      resetIn: config.windowSeconds,
      exceeded: false
    };
  }

  const remaining = Math.max(0, config.maxRequests - limit.count);
  const resetIn = Math.max(0, Math.ceil((limit.resetTime - now) / 1000));

  return {
    count: limit.count,
    remaining,
    resetIn,
    exceeded: limit.count > config.maxRequests
  };
};
