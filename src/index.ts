import { Hono } from 'hono';

const app = new Hono();

app.get('/healthz', c => {
  return c.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    message: 'Service is healthy',
  });
});

export default app;
