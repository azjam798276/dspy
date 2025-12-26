---
id: "20251226_email_queue"
source_url: "https://optimalbits.github.io/bull/"
difficulty: "medium"
tags: ["background-jobs", "queue", "bull", "idempotency", "retries"]
tech_stack: "Node.js, Bull, Redis, Nodemailer, Jest"
---

# User Story
As a user management system, I want welcome emails sent asynchronously with retry logic and idempotency, so users receive emails reliably without blocking API responses.

# Context & Constraints
**Queue Requirements:**
- Trigger `queueWelcomeEmail(userId)` on user creation
- **3 retries** with exponential backoff (2s, 8s, 32s)
- **Idempotency key** prevents duplicate emails
- Dead letter queue for failed jobs
- Graceful shutdown drains queue

**Job Data:**
{
"userId": 123,
"template": "welcome",
"idempotencyKey": "welcome:123:1735200000"
}

text

# Acceptance Criteria
- [ ] **Queue Integration:** `POST /users` → auto-queue welcome email
- [ ] **Idempotency:** Duplicate jobs (same key) skipped
- [ ] **Retry Logic:** Failed email retries 3x automatically
- [ ] **Redis Storage:** Jobs persist across restarts
- [ ] **Monitoring:** Job completion/failure logged
- [ ] **Shutdown:** `SIGTERM` drains queue before exit
