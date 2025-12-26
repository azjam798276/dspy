---
id: "20251226_rest_users_api"
source_url: "https://restfulapi.net/"
difficulty: "medium"
tags: ["api-design", "rest", "express", "validation", "pagination"]
tech_stack: "Node.js, Express, Sequelize, express-validator, Jest"
---

# User Story
As an admin, I want a complete RESTful `/api/users` endpoint with pagination, filtering, and validation so I can manage users efficiently through standardized API conventions.

# Context & Constraints
Build production-grade REST API following strict conventions:
- **GET /api/users** - List with `?page=1&limit=20&status=active`
- **POST /api/users** - Create with email/password validation
- **Standard pagination response** with `data`, `pagination` object
- **express-validator** chain for input sanitization
- **Proper HTTP status codes** (201, 400, 409, 500)

**Response Format:**
{
"data": [...],
"pagination": {
"page": 1,
"limit": 20,
"total": 150,
"pages": 8
}
}

text

# Acceptance Criteria
- [ ] **List Users:** `GET /api/users?page=1&limit=10` returns paginated users (exclude password)
- [ ] **Filter:** `GET /api/users?status=active` filters correctly
- [ ] **Validation:** `POST /api/users` rejects invalid email/password with detailed errors
- [ ] **Conflict:** Duplicate email returns 409 "Email already exists"
- [ ] **Pagination Headers:** `X-Total-Count`, `X-Page-Count` headers
- [ ] **Test Coverage:** >90% including validation edge cases
