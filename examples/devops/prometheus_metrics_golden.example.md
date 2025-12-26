---
id: "prometheus_metrics_golden"
tags: ["devops", "monitoring", "prometheus"]
---

## Problem
Implement Prometheus metrics for Node.js Express application.
- HTTP request duration histogram
- Request counter by route/status
- /metrics endpoint

## Solution
```javascript
// path: src/metrics/prometheus.js
const client = require('prom-client');

// Create registry
const register = new client.Registry();

// Add default Node.js metrics
client.collectDefaultMetrics({ register });

// HTTP request duration
const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5]
});
register.registerMetric(httpRequestDuration);

// HTTP request counter
const httpRequestTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status']
});
register.registerMetric(httpRequestTotal);

// Middleware
function metricsMiddleware(req, res, next) {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    const route = req.route?.path || req.path;
    const labels = {
      method: req.method,
      route: route,
      status: res.statusCode
    };
    
    httpRequestDuration.observe(labels, duration);
    httpRequestTotal.inc(labels);
  });
  
  next();
}

// Metrics endpoint
async function metricsHandler(req, res) {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
}

module.exports = { metricsMiddleware, metricsHandler, register };
```

## Key Techniques
- prom-client for Prometheus integration
- Histogram with SLO-appropriate buckets
- Labels for route, method, status grouping
- Default Node.js runtime metrics included
