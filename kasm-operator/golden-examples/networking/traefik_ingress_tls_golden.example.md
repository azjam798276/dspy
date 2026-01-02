---
id: "traefik_ingress_tls_golden"
source_story: "kasm-k3s/stories/networking/20260101_traefik_ingress_tls.story.md"
source_url: "https://doc.traefik.io/traefik/routing/providers/kubernetes-ingress/"
tags: ["networking", "ingress", "traefik", "tls", "k3s", "sticky-sessions"]
---

## Problem
Configure K3s default Traefik Ingress for Kasm Workspaces.
- Enable TLS termination.
- **Critical:** Enable Sticky Sessions (Affinity) for Kasm API.
- **Critical:** Enable WebSocket upgrades via headers.
- HTTP-to-HTTPS redirection.

## Solution

### 1. Ingress with Sticky Sessions & TLS
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kasm-ingress
  namespace: kasm
  annotations:
    # Router configuration
    traefik.ingress.kubernetes.io/router.entrypoints: websecure
    traefik.ingress.kubernetes.io/router.tls: "true"
    
    # CRITICAL: Sticky sessions for Kasm API
    traefik.ingress.kubernetes.io/affinity: "true"
    traefik.ingress.kubernetes.io/service.sticky.cookie: "true"
    traefik.ingress.kubernetes.io/service.sticky.cookie.name: kasm_session
    
    # Backend configuration
    traefik.ingress.kubernetes.io/service.server.port: "443"
    kubernetes.io/ingress.class: traefik
spec:
  rules:
  - host: kasm.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: kasm-proxy
            port:
              number: 443
  tls:
  - secretName: kasm-tls
    hosts:
    - kasm.example.com
```

### 2. HTTPS Redirect Middleware
```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: https-redirect
  namespace: kasm
spec:
  redirectScheme:
    scheme: https
    permanent: true
```

### 3. WebSocket Headers (Optional/Verify)
If WebSockets fail, apply this Middleware to force protocol headers:
```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: force-https-headers
  namespace: kasm
spec:
  headers:
    customRequestHeaders:
      X-Forwarded-Proto: "https"
```

## Key Techniques
- **Sticky Sessions (`affinity: "true"`)**: Absolutely required for Kasm's multi-container session management.
- **Entrypoints**: Explicitly bind to `websecure` to avoid exposing on HTTP port 80 unintendedly.
- **Service Port**: Explicitly set `service.server.port: "443"` if the backend pod listens on TLS.
