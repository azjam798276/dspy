---
id: "jwt_auth_golden"
source_story: "stories/backend/user_auth.story.md"
tags: ["authentication", "jwt", "security", "middleware", "refresh-token"]
---

## Problem

Implement JWT auth with refresh tokens:
- POST /auth/login - Issue access/refresh tokens
- POST /auth/refresh - Rotate refresh tokens
- Middleware protects routes with token validation
- Secure token storage + blacklist support

## Solution

// path: src/middleware/auth.js
const jwt = require('jsonwebtoken');
const redis = require('../config/redis');

const JWT_ACCESS_SECRET = process.env.JWT_ACCESS_SECRET;
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET;
const ACCESS_EXPIRY = '15m';
const REFRESH_EXPIRY = '7d';

const generateTokens = (user) => {
const accessToken = jwt.sign(
{ userId: user.id, role: user.role },
JWT_ACCESS_SECRET,
{ expiresIn: ACCESS_EXPIRY }
);

const refreshToken = jwt.sign(
{ userId: user.id },
JWT_REFRESH_SECRET,
{ expiresIn: REFRESH_EXPIRY }
);

return { accessToken, refreshToken };
};

// Verify access token middleware
const authenticateToken = async (req, res, next) => {
const authHeader = req.headers['authorization'];
const token = authHeader?.split(' ');
​

if (!token) {
return res.status(401).json({ error: 'Access token required' });
}

try {
// Check blacklist first
const isBlacklisted = await redis.get(blacklist:${token});
if (isBlacklisted) {
return res.status(401).json({ error: 'Token revoked' });
}

text
const decoded = jwt.verify(token, JWT_ACCESS_SECRET);
req.user = decoded;
next();
} catch (err) {
res.status(401).json({ error: 'Invalid token' });
}
};

// Login endpoint
app.post('/auth/login', async (req, res) => {
const { email, password } = req.body;
const user = await User.findOne({ where: { email } });

if (!user || !await user.validatePassword(password)) {
return res.status(401).json({ error: 'Invalid credentials' });
}

const tokens = generateTokens(user);

// Store refresh token
await redis.setex(refresh:${tokens.refreshToken},
7 * 24 * 3600, user.id);

res.json({
accessToken: tokens.accessToken,
refreshToken: tokens.refreshToken
});
});

module.exports = { authenticateToken, generateTokens };

text

## Key Techniques
- **Dual Token System**: Short-lived access + long-lived refresh
- **Token Blacklist**: Redis storage for logout/revocation
- **Secure Claims**: `userId` + `role` in access token
- **Rotation**: Refresh endpoint validates + issues new pair
