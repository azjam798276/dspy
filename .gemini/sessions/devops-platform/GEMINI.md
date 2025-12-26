---
name: devops-platform
description: Manages the CI/CD pipeline for Autonomous Optimization.
---



# Infrastructure Patterns

## IaC Principles
1. **Immutability:** Never modify running servers; replace them.
2. **Declarative:** Define state in code (Terraform/K8s).
3. **Observability:** Logs, Metrics, and Traces for every service.

## Deployment
- Blue/Green deployments for zero downtime.
- Automated rollback on health check failure.

## Optimization Strategy
- Refined based on feedback: Focus on pipeline velocity and self-healing infrastructure.

# React Infrastructure Patterns

## Delivery
1. **CDN Caching:** Cache immutable assets (hashes) forever, index.html for 0 seconds.
2. **Build Optimization:** Tree-shaking and code splitting validation in CI.

## Deployment
- Atomic uploads of assets before switching the main pointer.

# Security Infrastructure Patterns
## Network Security
1. **Zero Trust Network:** mTLS between all microservices.
2. **Segmentation:** strict VPC peering and security groups.

## Container Security
- Distroless images to minimize attack surface.
- Runtime scanning (Falco) for anomaly detection.