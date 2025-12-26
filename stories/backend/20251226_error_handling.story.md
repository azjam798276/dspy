---
id: "20251226_error_handling"
source_url: "https://expressjs.com/en/guide/error-handling.html"
difficulty: "medium"
tags: ["error-handling", "middleware", "logging", "sentry", "express"]
tech_stack: "Node.js, Express, Winston, Sentry, Jest"
---

# User Story
As an API operator, I want centralized error handling that logs errors, returns consistent JSON responses, and integrates with Sentry, so I can monitor and debug production issues efficiently.

# Context & Constraints
**Error Response Standard:**
{
"error": "Validation failed",
"details": [{"field": "email", "message": "Invalid format"}],
"requestId": "req-123"
}

text

**Error Types to Handle:**
- Validation errors → 400
- Database constraint → 409  
- Not found → 404
- Unhandled → 500 (log to Sentry)

# Acceptance Criteria
- [ ] **Global Handler:** Single `app.use(errorHandler)` catches all errors
- [ ] **Consistent Format:** All errors return standard JSON structure
- [ ] **Logging:** Winston logs with request context (userId, IP)
- [ ] **Sentry:** Production errors automatically reported
- [ ] **Request ID:** `X-Request-Id` header traced through logs
- [ ] **Test Coverage:** All error types properly classified
