---
id: "20251226_secrets_management"
difficulty: "medium"
tags: ["security", "secrets", "vault", "environment"]
tech_stack: "Node.js, dotenv, HashiCorp Vault, AWS Secrets Manager"
---

# User Story
As a security engineer, I want to implement proper secrets management to eliminate hardcoded credentials and API keys.

# Context & Constraints
Replace hardcoded secrets with centralized management:

**Current Issues:**
- Database credentials in config files
- API keys committed to repository
- No rotation policy for secrets

**Requirements:**
- Load secrets from environment variables (12-factor)
- Support HashiCorp Vault for production
- Fallback to .env for local development
- Implement automatic rotation hooks

**Technical Constraints:**
- Zero secrets in codebase or logs
- Support for secret versioning
- Health check for secret availability
- Graceful handling of secret rotation

# Acceptance Criteria
- [ ] Create secrets loader with Vault integration
- [ ] Implement environment variable fallback for dev
- [ ] Add secret rotation callback handlers
- [ ] Create health endpoint to verify secret access
- [ ] Ensure no secrets leak to logs or error messages
