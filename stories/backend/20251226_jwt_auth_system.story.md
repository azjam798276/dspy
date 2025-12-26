---
id: "20251226_jwt_auth_system"
source_url: "https://jwt.io/introduction/"
difficulty: "hard"
tags: ["authentication", "jwt", "security", "refresh-token", "blacklist"]
tech_stack: "Node.js, Express, jsonwebtoken, Redis, bcrypt, Jest"
---

# User Story
As a secure API consumer, I want a complete JWT authentication system with access/refresh tokens and logout capability, so I can securely access protected resources.

# Context & Constraints
**Complete Auth Flow:**
POST /auth/login → {accessToken, refreshToken}
POST /auth/refresh → new token pair
POST /auth/logout → blacklist access token
GET /profile → requires valid access token

text

**Security Requirements:**
- Access tokens: 15min expiry
- Refresh tokens: 7d expiry, stored in Redis
- Token blacklist on logout
- Secure claims: `{userId, role, iat, exp}`

# Acceptance Criteria
- [ ] **Login:** `POST /auth/login` returns valid token pair
- [ ] **Protected Route:** `GET /profile` requires `Authorization: Bearer <token>`
- [ ] **Refresh:** `POST /auth/refresh` validates refresh token → issues new pair
- [ ] **Logout:** `POST /auth/logout` blacklists access token (Redis)
- [ ] **Revoked Token:** Blacklisted token returns 401 "Token revoked"
- [ ] **Security Test:** Expired/invalid tokens properly rejected
