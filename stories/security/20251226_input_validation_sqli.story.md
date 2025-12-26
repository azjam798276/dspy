---
id: "20251226_input_validation_sqli"
difficulty: "hard"
tags: ["security", "sql-injection", "input-validation", "express"]
tech_stack: "Node.js, Express, PostgreSQL, Joi"
---

# User Story
As a security engineer, I want to implement proper input validation to prevent SQL injection attacks on our user search endpoint.

# Context & Constraints
The current `/users/search` endpoint is vulnerable to SQL injection:
```javascript
// VULNERABLE CODE
const query = `SELECT * FROM users WHERE name LIKE '%${req.query.name}%'`;
```

**Requirements:**
- Implement parameterized queries using pg library
- Add input validation with Joi schema
- Sanitize all user inputs before database operations
- Return proper error messages without exposing internals

**Technical Constraints:**
- Must use Joi for validation (existing dependency)
- Support partial name matching (LIKE queries)
- Log attempted injection attacks for monitoring

# Acceptance Criteria
- [ ] Implement parameterized query for user search
- [ ] Create Joi schema for search input validation
- [ ] Add middleware to validate and sanitize inputs
- [ ] Return 400 for invalid inputs with safe error messages
- [ ] Log injection attempts to security audit log
