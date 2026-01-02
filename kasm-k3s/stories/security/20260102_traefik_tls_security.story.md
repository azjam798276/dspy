---
id: "20260102_traefik_tls_security"
difficulty: "easy"
tags: ["security", "tls", "traefik", "cert-manager", "ingress"]
tech_stack: "Kubernetes, K3s, Traefik, cert-manager"
---

# User Story
As a security engineer, I want to configure Traefik IngressRoute with automatic TLS certificate provisioning via cert-manager, security headers, and rate limiting.

# Context & Constraints
Implement secure ingress for Kasm Workspaces:

**Requirements:**
- Automatic Let's Encrypt TLS via cert-manager
- Security headers middleware (HSTS, X-Frame-Options, CSP)
- Rate limiting middleware to prevent DDoS
- HTTP to HTTPS redirect

**Traefik Middlewares:**
- Security headers: HSTS, X-Content-Type-Options, X-XSS-Protection
- Rate limit: 100 req/sec average, 200 burst
- HTTPS redirect: permanent (301)

**cert-manager:**
- ClusterIssuer with Let's Encrypt ACME
- HTTP-01 challenge solver
- Certificate auto-renewal 30 days before expiry

# Acceptance Criteria
- [ ] ClusterIssuer configured for letsencrypt-prod
- [ ] Certificate resource with secretName
- [ ] IngressRoute with TLS secretName reference
- [ ] Security headers middleware applied
- [ ] Rate limiting middleware applied
- [ ] HTTP redirect to HTTPS
