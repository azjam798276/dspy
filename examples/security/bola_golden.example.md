---
id: "bola_golden"
source_story: "stories/security/20251225_api_sec_bola.story.md"
tags: ["security", "authorization", "jwt", "express"]
---

## Problem

Fix Broken Object Level Authorization (BOLA) vulnerability in shop revenue API.
- Any authenticated user can access ANY shop's revenue by guessing shopName
- Must verify `userId` from JWT matches `shop.ownerId`
- Return 403 Forbidden for unauthorized access

## Solution

// path: src/middleware/auth.js
const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// 1. JWT Verification Middleware
const verifyToken = (req, res, next) => {
const authHeader = req.headers.authorization;
const token = authHeader && authHeader.split(' '); // Bearer TOKEN
​

if (!token) {
return res.status(401).json({ error: 'Access token required' });
}

try {
const decoded = jwt.verify(token, JWT_SECRET);
req.userId = decoded.userId;
next();
} catch (err) {
return res.status(401).json({ error: 'Invalid token' });
}
};

// 2. Shop Ownership Middleware
const checkShopOwnership = (req, res, next) => {
const { shopName } = req.params;

// Mock data - in real app, query database
const shops = {
'shopA': { ownerId: 'user123', revenue: { monthly: 5000 } },
'shopB': { ownerId: 'user456', revenue: { monthly: 7500 } }
};

const shop = shops[shopName];

if (!shop) {
return res.status(404).json({ error: 'Shop not found' });
}

if (shop.ownerId !== req.userId) {
return res.status(403).json({ error: 'Not authorized to access this shop' });
}

req.shop = shop;
next();
};

// 3. Protected Route
app.get('/shops/:shopName/revenue',
verifyToken,
checkShopOwnership,
(req, res) => {
res.json(req.shop.revenue);
}
);

module.exports = { verifyToken, checkShopOwnership };

text

## Test (Golden Assertion)
test('UserA cannot access UserB shop - 403 Forbidden', async () => {
const res = await request(app)
.get('/shops/shopB/revenue')
.set('Authorization', Bearer ${userA_token});
expect(res.status).toBe(403);
expect(res.body.error).toBe('Not authorized to access this shop');
});

text

## Key Techniques
- **Middleware Chain**: `verifyToken` → `checkOwnership` → handler
- **Fail Fast Pattern**: 401 → 404 → 403 → 200
- **No Shared State**: Each middleware validates independently
