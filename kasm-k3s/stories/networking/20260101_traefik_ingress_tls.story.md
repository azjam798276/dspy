---
id: "20260101_traefik_ingress_tls"
difficulty: "medium"
tags: ["networking", "ingress", "traefik", "tls", "k3s", "kasm"]
tech_stack: "K3s, Traefik, cert-manager, TLS, Ingress"
---

# User Story
As a network engineer, I want to configure Traefik ingress for Kasm Workspaces with automatic TLS certificate provisioning via cert-manager.

# Context & Constraints
Configure HTTPS access to Kasm via K3s Traefik:

**Components:**
- Traefik IngressRoute or Ingress resource
- TLS certificate (cert-manager or manual)
- HTTP to HTTPS redirect
- WebSocket support for session streaming

**Requirements:**
- Automatic TLS via Let's Encrypt (cert-manager)
- HTTP → HTTPS redirect middleware
- Valid certificate for kasm.example.com
- WebSocket upgrade headers preserved
- Sticky sessions for API

**Technical Constraints:**
- K3s includes Traefik v2.x by default
- Use Kubernetes Ingress API (not IngressRoute CRD)
- cert-manager ClusterIssuer for Let's Encrypt
- Port 80/443 must be open on cluster nodes

# Acceptance Criteria
- [ ] Create Ingress resource with TLS annotation
- [ ] Configure cert-manager ClusterIssuer
- [ ] Verify automatic certificate issuance
- [ ] Test HTTPS access to Kasm
- [ ] Confirm WebSocket connections work
