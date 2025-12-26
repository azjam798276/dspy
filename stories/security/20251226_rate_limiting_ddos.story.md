---
id: "20251226_rate_limiting_ddos"
difficulty: "medium"
tags: ["security", "rate-limiting", "ddos", "express"]
tech_stack: "Node.js, Express, Redis, express-rate-limit"
---

# User Story
As a security engineer, I want to implement multi-tier rate limiting to protect against DDoS and brute force attacks.

# Context & Constraints
Implement defense-in-depth rate limiting:

**Tiers:**
1. **Global**: 1000 req/min per IP
2. **Auth endpoints**: 5 req/min per IP (login, register)
3. **User-specific**: 100 req/min per authenticated user

**Requirements:**
- Use Redis backend for distributed rate limiting
- Return proper 429 responses with Retry-After header
- Different limits for authenticated vs anonymous users
- Exponential backoff for repeated violations

**Technical Constraints:**
- Must work across multiple server instances
- Include client fingerprinting for bypass detection
- Log rate limit violations for security monitoring

# Acceptance Criteria
- [ ] Implement global rate limiter with Redis backend
- [ ] Create stricter limiter for authentication endpoints
- [ ] Add user-tier rate limiting for authenticated requests
- [ ] Return 429 with Retry-After and X-RateLimit headers
- [ ] Implement exponential backoff for repeat offenders
