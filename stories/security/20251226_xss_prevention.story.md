---
id: "20251226_xss_prevention"
difficulty: "medium"
tags: ["security", "xss", "sanitization", "csp"]
tech_stack: "Node.js, Express, DOMPurify, helmet"
---

# User Story
As a security engineer, I want to implement XSS prevention across our application rendering user-generated content.

# Context & Constraints
Protect against Cross-Site Scripting attacks:

**Attack Vectors:**
- User profile bios rendered in HTML
- Comment sections with markdown support
- Search results highlighting user input

**Requirements:**
- Implement Content Security Policy headers
- Sanitize all user HTML with DOMPurify
- Context-aware output encoding
- Safe markdown rendering

**Technical Constraints:**
- Must allow safe markdown formatting
- CSP should not break legitimate functionality
- Support for reporting CSP violations
- No inline scripts or styles

# Acceptance Criteria
- [ ] Configure helmet with strict CSP headers
- [ ] Implement DOMPurify sanitization middleware
- [ ] Create safe markdown renderer with XSS filtering
- [ ] Add CSP violation reporting endpoint
- [ ] Implement context-aware output encoding helpers
