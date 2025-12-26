---
id: "20251226_jwt_token_security"
difficulty: "hard"
tags: ["security", "jwt", "authentication", "token-management"]
tech_stack: "Node.js, Express, jsonwebtoken, Redis"
---

# User Story
As a security engineer, I want to implement secure JWT token management with proper expiration and revocation capabilities.

# Context & Constraints
Implement a dual-token authentication system:

**Token Structure:**
- Access Token: Short-lived (15 min), used for API calls
- Refresh Token: Long-lived (7 days), used to get new access tokens
- Store refresh tokens in Redis for revocation capability

**Security Requirements:**
- Use RS256 algorithm (asymmetric keys)
- Include minimal claims (sub, iat, exp, jti)
- Implement token blacklist in Redis for revoked tokens
- Rotate refresh tokens on each use (one-time use)

**Technical Constraints:**
- Private key stored in environment variable
- All tokens must have unique JTI (JWT ID)
- Revocation check must be O(1) using Redis

# Acceptance Criteria
- [ ] Implement access token generation with RS256
- [ ] Implement refresh token with JTI stored in Redis
- [ ] Create token refresh endpoint with rotation
- [ ] Add middleware to validate tokens and check blacklist
- [ ] Implement logout that revokes all user tokens
