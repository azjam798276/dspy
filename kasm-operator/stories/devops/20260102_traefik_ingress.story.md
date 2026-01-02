---
id: "20260102_traefik_ingress"
difficulty: "medium"
tags: ["devops", "traefik", "ingress", "tls", "websocket"]
tech_stack: "Traefik, Kubernetes, Let's Encrypt"
---

# User Story
As a DevOps engineer, I want Traefik IngressRoutes for VDI sessions with wildcard TLS, so each user gets a unique HTTPS subdomain.

# Context & Constraints
**IngressRoute Template:**
```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: {{ .session.name }}
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`{{ .username }}.vdi.example.com`)
      kind: Rule
      services:
        - name: {{ .session.name }}
          port: 8080
  tls:
    certResolver: letsencrypt
    domains:
      - main: "*.vdi.example.com"
```

**Traefik Configuration:**
```yaml
# Traefik static config
certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /data/acme.json
      dnsChallenge:
        provider: cloudflare
```

**WebSocket Support:**
- Traefik automatically handles WebSocket upgrades
- No additional configuration needed for WebRTC signaling

# Acceptance Criteria
- [ ] **IngressRoute:** Generate per-session with unique host
- [ ] **TLS:** Wildcard certificate via Let's Encrypt DNS challenge
- [ ] **WebSocket:** Verify WebSocket upgrade works
- [ ] **Host Sanitization:** Sanitize username for valid subdomain
- [ ] **Owner Reference:** Set session as owner of IngressRoute
- [ ] **Cleanup:** IngressRoute deleted when session deleted
