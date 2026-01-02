---
id: "traefik_certmanager_tls"
source: "https://gist.github.com/jannegpriv/4ae51213d35ba8c3c5d40d188f7bbe36"
tags: ["security", "tls", "traefik", "cert-manager", "letsencrypt", "ingress"]
---

## Problem
Configure Traefik IngressRoute on K3s with automatic TLS certificate provisioning via cert-manager and Let's Encrypt. The setup must include security headers middleware, rate limiting, and HTTP to HTTPS redirection for Kasm Workspaces.

## Solution
```yaml
# 1. ClusterIssuer for Let's Encrypt
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
  namespace: cert-manager
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
    - http01:
        ingress:
          class: traefik

---
# 2. Certificate resource (auto-creates TLS Secret)
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: kasm-tls-cert
  namespace: kasm
spec:
  secretName: kasm-tls-cert
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - kasm.example.com
  usages:
    - digital signature
    - key encipherment
  renewBefore: 720h  # 30 days before expiry

---
# 3. Security Headers Middleware
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: security-headers
  namespace: kasm
spec:
  headers:
    customResponseHeaders:
      X-Frame-Options: "SAMEORIGIN"
      X-Content-Type-Options: "nosniff"
      X-XSS-Protection: "1; mode=block"
      Referrer-Policy: "strict-origin-when-cross-origin"
      Strict-Transport-Security: "max-age=31536000; includeSubDomains"
      Content-Security-Policy: "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

---
# 4. Rate Limiting Middleware
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: rate-limit
  namespace: kasm
spec:
  rateLimit:
    average: 100      # Requests per second
    period: 1s
    burst: 200        # Max burst size
    sourceCriterion:
      ipStrategy:
        depth: 1      # Use X-Forwarded-For header

---
# 5. HTTPS Redirect Middleware
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: https-redirect
  namespace: kasm
spec:
  redirectScheme:
    scheme: https
    permanent: true
    port: "443"

---
# 6. HTTPS IngressRoute (main)
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: kasm-workspace-https
  namespace: kasm
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`kasm.example.com`)
      kind: Rule
      services:
        - name: kasm-web
          port: 443
          scheme: https
      middlewares:
        - name: security-headers
        - name: rate-limit
  tls:
    secretName: kasm-tls-cert

---
# 7. HTTP to HTTPS Redirect IngressRoute
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: kasm-workspace-http
  namespace: kasm
spec:
  entryPoints:
    - web
  routes:
    - match: Host(`kasm.example.com`)
      kind: Rule
      services:
        - name: kasm-web
          port: 80
      middlewares:
        - name: https-redirect
```

## Key Techniques
- Automated Let's Encrypt certificate provisioning and renewal
- HTTP-01 challenge solver with Traefik ingress class
- Security headers: HSTS, X-Frame-Options, CSP, X-XSS-Protection
- Rate limiting middleware to prevent DDoS/brute-force attacks
- HTTP to HTTPS permanent redirect (301)
- K3s-native Traefik IngressRoute CRD (not standard Ingress)
- Certificate auto-renewal 30 days before expiry
