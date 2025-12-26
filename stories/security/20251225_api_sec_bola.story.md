---
id: "20251225_api_sec_bola"
source_url: "https://github.com/VArtzy/NodeJS-OWASP-API-Security"
difficulty: "medium"
tags: ["security", "authorization", "node.js", "express", "jwt"]
tech_stack: "Node.js, Express.js, JWT, Jest"
---

# User Story
As a shop owner, I should only see my own revenue data when accessing the `/shops/:shopName/revenue` endpoint, so that business-critical information remains confidential.

# Context & Constraints
The API currently allows any authenticated user to access revenue data for ANY shop by simply knowing the shop name. This is a **Broken Object Level Authorization (BOLA)** vulnerability - one of the OWASP Top 10 API Security Risks.

**Current Vulnerable Pattern:**
```javascript
app.get('/shops/:shopName/revenue', (req, res) => {
    const shopName = req.params.shopName;
    const shopRevenue = revenueData[shopName];
    if (shopRevenue) {
        res.json(shopRevenue);
    }
});
```

**Requirements:**
- Implement JWT-based authentication middleware
- Store `ownerId` with each shop's data
- Verify `userId` from token matches `ownerId` before returning data
- Return `403 Forbidden` if user attempts to access another user's shop
- Return `404 Not Found` if shop doesn't exist

# Acceptance Criteria
- [ ] **Authentication Middleware:** Create `verifyToken` middleware that extracts and validates JWT, setting `req.userId`
- [ ] **Ownership Check:** Verify `revenueData[shopName].ownerId === req.userId` before returning sensitive data
- [ ] **Security Test:** Write a test proving User A cannot access User B's shop revenue (should return 403)
- [ ] **Coverage:** Achieve >85% test coverage for the authorization logic
- [ ] **Response Codes:** Correctly return 200 (authorized), 403 (forbidden), 404 (not found)
