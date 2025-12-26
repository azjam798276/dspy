---
id: "20251226_kubernetes_deployment"
difficulty: "hard"
tags: ["devops", "kubernetes", "helm", "deployment"]
tech_stack: "Kubernetes, Helm, Node.js, nginx"
---

# User Story
As a DevOps engineer, I want to create Kubernetes deployment manifests with proper health checks and resource limits.

# Context & Constraints
Deploy Node.js application to Kubernetes:

**Components:**
- Deployment with rolling update strategy
- Service with ClusterIP
- Ingress with TLS termination
- ConfigMap and Secrets
- HorizontalPodAutoscaler

**Requirements:**
- Liveness and readiness probes
- Resource requests and limits
- Pod disruption budget
- Rolling update with zero downtime
- Environment-specific configurations

**Technical Constraints:**
- Use Helm for templating
- Support multiple environments (dev, staging, prod)
- Secrets from external secret store
- Prometheus metrics annotations

# Acceptance Criteria
- [ ] Create Helm chart with deployment templates
- [ ] Implement proper health check probes
- [ ] Add HPA based on CPU/memory
- [ ] Configure ingress with cert-manager TLS
- [ ] Support values files for each environment
