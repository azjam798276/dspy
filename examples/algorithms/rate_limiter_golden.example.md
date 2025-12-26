---
id: "rate_limiter_golden"
source_story: "stories/algorithms/20251225_rate_limiter_token_bucket.story.md"
tags: ["algorithm", "redis", "rate-limiting", "token-bucket"]
---

## Problem

Implement a Token Bucket rate limiter with Redis for distributed state.
- Each IP gets a bucket with 10 tokens capacity
- 1 token refills per second (lazy calculation)
- Return 429 if bucket is empty
- Must be atomic (no race conditions)

## Solution

```javascript
// path: src/middleware/rateLimiter.js
const redis = require('redis');

const BUCKET_CAPACITY = 10;
const REFILL_RATE = 1; // tokens per second

/**
 * Check and consume a token from the bucket.
 * Uses Redis Lua script for atomicity.
 * @param {string} ipAddress - Client IP
 * @returns {Promise<{allowed: boolean, remainingTokens: number, retryAfter: number}>}
 */
async function checkAndConsumeToken(redisClient, ipAddress) {
  const key = `ratelimit:${ipAddress}`;
  const now = Date.now() / 1000; // Current time in seconds

  // Lua script for atomic token bucket operation
  const luaScript = `
    local key = KEYS[1]
    local capacity = tonumber(ARGV[1])
    local refillRate = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])

    local bucket = redis.call('HMGET', key, 'tokens', 'lastRefill')
    local tokens = tonumber(bucket[1]) or capacity
    local lastRefill = tonumber(bucket[2]) or now

    -- Calculate tokens to add based on time elapsed
    local elapsed = now - lastRefill
    local tokensToAdd = math.floor(elapsed * refillRate)
    tokens = math.min(capacity, tokens + tokensToAdd)

    if tokensToAdd > 0 then
      lastRefill = now
    end

    if tokens >= 1 then
      tokens = tokens - 1
      redis.call('HMSET', key, 'tokens', tokens, 'lastRefill', lastRefill)
      redis.call('EXPIRE', key, capacity / refillRate * 2) -- TTL for cleanup
      return {1, tokens, 0} -- allowed, remaining, retryAfter
    else
      local retryAfter = (1 - tokens) / refillRate
      return {0, 0, retryAfter} -- denied
    end
  `;

  const result = await redisClient.eval(luaScript, {
    keys: [key],
    arguments: [BUCKET_CAPACITY.toString(), REFILL_RATE.toString(), now.toString()]
  });

  return {
    allowed: result[0] === 1,
    remainingTokens: result[1],
    retryAfter: result[2]
  };
}

/**
 * Express middleware for rate limiting.
 */
function rateLimiterMiddleware(redisClient) {
  return async (req, res, next) => {
    const ip = req.ip || req.connection.remoteAddress;

    try {
      const { allowed, remainingTokens, retryAfter } = await checkAndConsumeToken(redisClient, ip);

      res.setHeader('X-RateLimit-Remaining', remainingTokens);

      if (!allowed) {
        res.setHeader('Retry-After', Math.ceil(retryAfter));
        return res.status(429).json({
          error: 'Too Many Requests',
          retryAfter: Math.ceil(retryAfter)
        });
      }

      next();
    } catch (error) {
      // Fail open: allow request if Redis is down (configurable)
      console.error('Rate limiter error:', error);
      next();
    }
  };
}

module.exports = { checkAndConsumeToken, rateLimiterMiddleware };
```

## Key Techniques
- **Lua Script Atomicity**: All token operations in a single Redis script
- **Lazy Refill**: Tokens calculated on-demand, no background jobs
- **Fail Open**: Graceful degradation if Redis is unavailable
