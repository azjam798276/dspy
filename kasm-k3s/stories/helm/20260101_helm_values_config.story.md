---
id: "20260101_helm_values_config"
difficulty: "medium"
tags: ["helm", "kubernetes", "k3s", "kasm", "configuration"]
tech_stack: "Kubernetes, Helm, K3s, Kasm Workspaces"
---

# User Story
As a DevOps engineer, I want to configure Kasm Workspaces Helm values.yaml for K3s deployment with proper storage, ingress, and resource settings.

# Context & Constraints
Configure Helm chart for Kasm Workspaces on K3s:

**Components:**
- Global namespace and hostname configuration
- K3s local-path storage class integration
- Traefik ingress class configuration
- Resource requests and limits for all pods
- TLS secret configuration

**Requirements:**
- Use K3s default storage class (local-path)
- Configure Traefik ingress annotations
- Set appropriate resource limits for API, proxy, manager
- Support environment-specific overrides (dev/prod)
- Database and Redis internal deployment settings

**Technical Constraints:**
- Single-node K3s cluster (development)
- Traefik as ingress controller (K3s default)
- No external LoadBalancer (use ClusterIP + Ingress)
- PostgreSQL and Redis deployed in-cluster

# Acceptance Criteria
- [ ] Create base values.yaml with all required settings
- [ ] Create k3s-specific override file
- [ ] Configure proper resource limits
- [ ] Set up Traefik ingress annotations
- [ ] Document all configurable parameters
