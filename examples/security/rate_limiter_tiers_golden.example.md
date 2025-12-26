---
id: "rate_limiter_tiers_golden"
tags: ["security", "rate-limiting", "express"]
---

## Problem
Implement multi-tier rate limiting to protect against DDoS.
- Global: 1000 req/min per IP
- Auth endpoints: 5 req/min
- Return 429 with Retry-After

## Solution
```javascript
// path: src/middleware/rateLimiter.js
const rateLimit = require('express-rate-limit');
const RedisStore = require('rate-limit-redis');

function createRateLimiter(redisClient, options) {
  return rateLimit({
    store: new RedisStore({
      sendCommand: (...args) => redisClient.call(...args)
    }),
    windowMs: options.windowMs || 60 * 1000,
    max: options.max,
    standardHeaders: true,
    legacyHeaders: false,
    keyGenerator: (req) => req.ip,
    handler: (req, res) => {
      res.status(429).json({
        error: 'Too Many Requests',
        retryAfter: Math.ceil(options.windowMs / 1000)
      });
    }
  });
}

// Global limiter - 1000/min
const globalLimiter = (redisClient) => createRateLimiter(redisClient, {
  max: 1000,
  windowMs: 60 * 1000
});

// Auth limiter - 5/min (stricter)
const authLimiter = (redisClient) => createRateLimiter(redisClient, {
  max: 5,
  windowMs: 60 * 1000,
  keyGenerator: (req) => `auth:${req.ip}`
});

// Usage in Express
// app.use(globalLimiter(redisClient));
// app.use('/auth', authLimiter(redisClient));

module.exports = { globalLimiter, authLimiter, createRateLimiter };
```

## Key Techniques
- Redis-backed distributed rate limiting
- Tiered limits (global vs auth-specific)
- Standard rate limit headers (X-RateLimit-*)
- Custom key generators for different contexts
