---
id: "rest_api_golden"
source_story: "stories/backend/restful_users.story.md"
tags: ["api-design", "rest", "express", "validation", "error-handling"]
---

## Problem

Create RESTful `/users` endpoint following strict conventions:
- GET /users - list with pagination/filtering
- POST /users - create with validation
- Proper HTTP status codes and error responses
- Input sanitization and rate limiting

## Solution

// path: src/routes/users.js
const express = require('express');
const { body, validationResult } = require('express-validator');
const router = express.Router();

// GET /users - List with pagination
router.get('/', async (req, res) => {
try {
const { page = 1, limit = 10, status } = req.query;
const offset = (page - 1) * limit;

text
const whereClause = status ? { status } : {};
const users = await User.findAll({
  where: whereClause,
  limit: parseInt(limit),
  offset: parseInt(offset),
  attributes: { exclude: ['password'] }
});

res.json({
  data: users,
  pagination: {
    page: parseInt(page),
    limit: parseInt(limit),
    total: await User.count({ where: whereClause })
  }
});
} catch (error) {
res.status(500).json({ error: 'Internal server error' });
}
});

// POST /users - Create with validation
router.post('/',
[
body('email').isEmail().normalizeEmail().withMessage('Valid email required'),
body('name').isLength({ min: 2 }).trim().escape().withMessage('Name must be 2+ chars'),
body('password').isLength({ min: 8 }).withMessage('Password must be 8+ chars')
],
async (req, res) => {
const errors = validationResult(req);
if (!errors.isEmpty()) {
return res.status(400).json({
error: 'Validation failed',
details: errors.array()
});
}

text
try {
  const user = await User.create(req.body);
  res.status(201).json({
    id: user.id,
    email: user.email,
    message: 'User created successfully'
  });
} catch (error) {
  if (error.name === 'SequelizeUniqueConstraintError') {
    return res.status(409).json({ error: 'Email already exists' });
  }
  res.status(500).json({ error: 'Failed to create user' });
}
}
);

module.exports = router;

text

## Key Techniques
- **REST Conventions**: Plural nouns, proper HTTP verbs/status codes
- **Pagination**: `page`/`limit` with total count
- **Validation Chain**: `express-validator` middleware pipeline
- **Error Classification**: 400/409/500 distinct responses
