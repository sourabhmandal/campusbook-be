import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { secureHeaders } from 'hono/secure-headers';
import { auth } from '@/src/lib/better-auth';
import {
  rateLimiter,
  pathKeyGenerator,
  rlConfig,
  getRateLimitStatus
} from '@/src/lib/rate-limiter';

type AppEnv = { Bindings: CloudflareBindings };
const app = new Hono<AppEnv>();

// Apply security middleware
app.use(secureHeaders());
app.use(cors({
  origin: ['*'],
  credentials: true,
}));
app.use(logger());

// DDoS Protection - Apply to all requests
app.use('*', rateLimiter());

// Authentication routes
app.on(['GET', 'POST'], '/api/auth/*', (c) => {
  return auth(c.env).handler(c.req.raw);
});

// Health check endpoint
app.get('/api/healthz', c => {
  return c.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    message: 'Service is healthy',
    rl_limit: '20 req/min', 
    rl_window: '1 minute',
  });
});


app.get('/api/rate-status', async (c) => {
  try {
    // Only proceed if Cloudflare KV store is available
    if (!c.env?.RATE_LIMITER_KV) {
      return c.json({
        error: 'Service Unavailable',
        message: 'Rate limiting store not configured',
        statusCode: 503,
        timestamp: new Date().toISOString()
      }, 503);
    }

    // Generate rate limit key using the same function as the rate limiter
    const rateKey = pathKeyGenerator(c);

    // Get rate limit status using the helper function
    const status = await getRateLimitStatus(c.env.RATE_LIMITER_KV, rateKey, rlConfig);

    return c.json({
      key: rateKey,
      limit: rlConfig.maxRequests,
      window: `${rlConfig.windowSeconds} seconds`,
      windowSeconds: rlConfig.windowSeconds,
      ...status
    });

  } catch {
    return c.json({
      error: 'Internal Server Error',
      message: 'Failed to retrieve rate limit status',
      statusCode: 500,
      timestamp: new Date().toISOString()
    }, 500);
  }
})

export default app;
