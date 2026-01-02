---
id: "20260101_network_policy_isolation"
difficulty: "medium"
tags: ["security", "network-policy", "kubernetes", "kasm", "isolation"]
tech_stack: "Kubernetes, K3s, NetworkPolicy, Kasm Workspaces"
---

# User Story
As a security engineer, I want to implement NetworkPolicies to isolate Kasm database and internal services from unauthorized pod-to-pod traffic.

# Context & Constraints
Implement defense-in-depth for Kasm namespace:

**Components:**
- Default deny ingress policy
- Allow rules for kasm-api → kasm-db
- Allow rules for kasm-manager → kasm-redis
- Ingress from Traefik to kasm-proxy

**Requirements:**
- PostgreSQL only accessible from API/manager
- Redis only accessible from manager
- External access only via Traefik ingress
- Block all other pod-to-pod traffic

**Technical Constraints:**
- K3s needs network plugin with NetworkPolicy support
- Flannel (default) may not support NetworkPolicies
- May need Calico or Cilium for full support
- Test policies in non-blocking mode first

# Acceptance Criteria
- [ ] Create default-deny-ingress policy
- [ ] Allow Traefik → kasm-proxy
- [ ] Allow kasm-api → kasm-db on port 5432
- [ ] Allow kasm-manager → kasm-redis on port 6379
- [ ] Verify policies don't break application
