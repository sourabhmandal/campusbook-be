import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { secureHeaders } from 'hono/secure-headers';
import { auth } from '@/src/lib/better-auth';
import { rateLimiter } from "hono-rate-limiter";
import { pathKeyGenerator } from './lib/rate-limiter-utils';
import { openAPISpec } from './openapi';

type AppEnv = { Bindings: CloudflareBindings };
const app = new Hono<AppEnv>();

// Apply security middleware
app.use(secureHeaders());
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:5173', 'http://localhost:8080', 'http://localhost:63738'],
  credentials: true,
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization', 'Cookie', 'X-Requested-With'],
  exposeHeaders: ['Set-Cookie'],
}));
app.use(logger());

// DDoS Protection - Apply to all requests
app.use("*", (c, next) => rateLimiter<AppEnv>({
  windowMs: 1 * 60 * 1000, // 1 minute
  limit: 100, // Limit each IP to 100 requests per window
  standardHeaders: "draft-6",
  keyGenerator: pathKeyGenerator,
})(c, next));

// Handle preflight requests explicitly
app.options('*', (c) => {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': c.req.header('Origin') || '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cookie, X-Requested-With',
      'Access-Control-Allow-Credentials': 'true',
      'Access-Control-Max-Age': '86400',
    },
  });
});

// Better Auth routes - handles all built-in auth operations
// This includes: /api/auth/sign-in, /api/auth/sign-up, /api/auth/sign-out, etc.
app.on(['GET', 'POST'], '/api/auth/*', async (c) => {
  try {
    return await auth(c.env).handler(c.req.raw);
  } catch (error) {
    return c.json({
      success: false,
      message: 'Authentication error',
      error: error instanceof Error ? error.message : 'Unknown error',
    }, 500);
  }
});

// OpenAPI/Swagger documentation endpoints
app.get('/api/docs/openapi.json', (c) => {
  return c.json(openAPISpec);
});

app.get('/api/docs', (c) => {
  const swaggerHtml = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>CampusBook API Documentation</title>
      <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui.css" />
      <style>
        html {
          box-sizing: border-box;
          overflow: -moz-scrollbars-vertical;
          overflow-y: scroll;
        }
        *, *:before, *:after {
          box-sizing: inherit;
        }
        body {
          margin:0;
          background: #fafafa;
        }
      </style>
    </head>
    <body>
      <div id="swagger-ui"></div>
      <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-bundle.js"></script>
      <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-standalone-preset.js"></script>
      <script>
        window.onload = function() {
          const ui = SwaggerUIBundle({
            url: '/api/docs/openapi.json',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
              SwaggerUIBundle.presets.apis,
              SwaggerUIStandalonePreset
            ],
            plugins: [
              SwaggerUIBundle.plugins.DownloadUrl
            ],
            layout: "StandaloneLayout"
          });
        };
      </script>
    </body>
    </html>
  `;
  
  return c.html(swaggerHtml);
});

// Health check endpoint
app.get('/api/healthz', c => {
  return c.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    message: 'Service is healthy with Better Auth',
    endpoints: {
      auth: [
        'POST /api/auth/sign-in',
        'POST /api/auth/sign-up', 
        'POST /api/auth/sign-out',
        'GET /api/auth/session',
      ],
      docs: [
        'GET /api/docs - Swagger UI',
        'GET /api/docs/openapi.json - OpenAPI spec',
      ]
    },
  });
});

export default app;
