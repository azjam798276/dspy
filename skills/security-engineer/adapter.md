# Security Compliance Patterns

## Zero Trust
1. **Identity First:** Verify identity on every request.
2. **Least Privilege:** Grant minimum necessary permissions.
3. **Encryption:** TLS 1.3 in transit, AES-256 at rest.

## Audit & Compliance
- Log all access control changes.
- Automated dependency scanning in CI.

## Optimization Strategy
- Refined based on feedback: Shift security left into the PR process.

# React Security Patterns

## XSS Prevention
1. **Sanitization:** Never use dangerouslySetInnerHTML without DOMPurify.
2. **Content Security Policy:** Strict CSP headers rejecting inline scripts.

## Auth
- Store tokens in HttpOnly cookies, not LocalStorage.

# Advanced Security Patterns
## AppSec
1. **Business Logic Flaws:** auditing for BOLA/IDOR beyond standard scanners.
2. **Crypto Agility:** Design for easy algorithm replacement.

## Incident Response
- Automated containment scripts for detected intrusions.