---
id: "jwt_dual_token_golden"
tags: ["security", "jwt", "authentication"]
---

## Problem
Implement secure JWT dual-token system with access/refresh tokens.
- Access token: 15 min, RS256
- Refresh token: 7 days, stored in Redis
- Token rotation on refresh

## Solution
```javascript
// path: src/auth/tokenService.js
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');

const PRIVATE_KEY = process.env.JWT_PRIVATE_KEY;
const PUBLIC_KEY = process.env.JWT_PUBLIC_KEY;

async function generateTokenPair(userId, redisClient) {
  const jti = uuidv4();
  
  // Access token - short lived
  const accessToken = jwt.sign(
    { sub: userId, type: 'access' },
    PRIVATE_KEY,
    { algorithm: 'RS256', expiresIn: '15m', jwtid: jti }
  );

  // Refresh token - long lived, stored in Redis
  const refreshJti = uuidv4();
  const refreshToken = jwt.sign(
    { sub: userId, type: 'refresh', jti: refreshJti },
    PRIVATE_KEY,
    { algorithm: 'RS256', expiresIn: '7d' }
  );

  // Store refresh token JTI in Redis for revocation
  await redisClient.set(
    `refresh:${userId}:${refreshJti}`,
    'valid',
    'EX', 7 * 24 * 60 * 60
  );

  return { accessToken, refreshToken };
}

async function refreshTokens(refreshToken, redisClient) {
  const decoded = jwt.verify(refreshToken, PUBLIC_KEY, { algorithms: ['RS256'] });
  
  // Check if refresh token is valid in Redis
  const key = `refresh:${decoded.sub}:${decoded.jti}`;
  const isValid = await redisClient.get(key);
  
  if (!isValid) {
    throw new Error('Refresh token revoked');
  }

  // Rotate: invalidate old, issue new
  await redisClient.del(key);
  return generateTokenPair(decoded.sub, redisClient);
}

async function revokeAllTokens(userId, redisClient) {
  const keys = await redisClient.keys(`refresh:${userId}:*`);
  if (keys.length > 0) {
    await redisClient.del(keys);
  }
}

module.exports = { generateTokenPair, refreshTokens, revokeAllTokens };
```

## Key Techniques
- RS256 asymmetric algorithm (public/private keys)
- Redis-backed refresh token storage for revocation
- Token rotation on refresh (one-time use)
- UUID JTI for unique token identification
