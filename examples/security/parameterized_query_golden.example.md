---
id: "parameterized_query_golden"
tags: ["security", "sql-injection", "node.js"]
---

## Problem
Implement parameterized queries to prevent SQL injection on user search endpoint.
- Current code uses string interpolation (vulnerable)
- Need to use pg library's parameterized queries
- Add input validation with Joi

## Solution
```javascript
// path: src/middleware/secureQuery.js
const Joi = require('joi');

// Validation schema
const searchSchema = Joi.object({
  name: Joi.string().max(100).pattern(/^[a-zA-Z0-9\s]+$/).required(),
  limit: Joi.number().integer().min(1).max(100).default(20)
});

// Secure search function
async function searchUsers(pool, params) {
  // Validate input
  const { error, value } = searchSchema.validate(params);
  if (error) {
    throw new ValidationError(error.details[0].message);
  }

  // Parameterized query - immune to SQL injection
  const query = {
    text: 'SELECT id, name, email FROM users WHERE name ILIKE $1 LIMIT $2',
    values: [`%${value.name}%`, value.limit]
  };

  const result = await pool.query(query);
  return result.rows;
}

// Express middleware
function validateSearchInput(req, res, next) {
  const { error } = searchSchema.validate(req.query);
  if (error) {
    return res.status(400).json({
      error: 'Invalid input',
      message: error.details[0].message
    });
  }
  next();
}

module.exports = { searchUsers, validateSearchInput };
```

## Key Techniques
- Parameterized queries with $1, $2 placeholders
- Joi schema validation before database access
- Input pattern restriction (alphanumeric only)
- Generic error messages (no SQL exposure)
