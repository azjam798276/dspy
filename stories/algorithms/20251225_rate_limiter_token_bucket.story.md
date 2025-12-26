---
id: "20251225_rate_limiter_token_bucket"
source_url: "https://codingchallenges.fyi/challenges/challenge-rate-limiter"
difficulty: "hard"
tags: ["algorithm", "concurrency", "redis", "performance", "token-bucket"]
tech_stack: "Node.js, Redis, Express, Jest, Supertest"
---

# User Story
As an API consumer, I want my requests to be rate-limited using the **Token Bucket algorithm** so that no single user can overwhelm the system, ensuring fair resource allocation and stability.

# Context & Constraints
Implement a production-grade token bucket rate limiter with these specifications:

**Algorithm Requirements:**
- Each IP address gets a "bucket" with capacity for **10 tokens**
- **1 token** is added per second (refill rate)
- Each request consumes **1 token**
- If bucket is empty, return `429 Too Many Requests`
- If bucket is full, discard newly generated tokens

**Technical Constraints:**
- Must use **Redis** for distributed token storage (support multi-server deployments)
- Time complexity for token check: **O(1)**
- Handle concurrent requests from the same IP atomically (no race conditions)
- Token refill must be calculated lazily (no background jobs)

**Test Scenario:**
Using Postman with 10 Virtual Users hitting `/limited`:
- Initial 10 requests: All pass (bucket starts full)
- After 1 second: Only 1 request passes, 9 fail (only 1 token refilled)
- After 10 seconds: 10 requests pass (bucket refilled)

# Acceptance Criteria
- [ ] **Token Bucket Logic:** Implement `checkAndConsumeToken(ipAddress)` returning `{allowed: boolean, remainingTokens: number, retryAfter: number}`
- [ ] **Redis Atomicity:** Use Lua script or Redis transactions to prevent race conditions on token updates
- [ ] **Lazy Refill:** Calculate tokens based on `(currentTime - lastRefillTime) * refillRate`, then update `lastRefillTime`
- [ ] **Express Middleware:** Create `rateLimiter` middleware that applies token bucket to `/limited` endpoint
- [ ] **Edge Case Handling:** Handle Redis downtime gracefully (fail open or closed based on config)
- [ ] **Load Test:** Pass a test with 100 concurrent requests over 10 seconds, verifying 90%+ rejection rate after initial burst
- [ ] **Coverage:** >90% test coverage including concurrency edge cases
