---
id: "networkpolicy_database_isolation"
source: "https://github.com/amartingarcia/kubernetes-cks-training"
tags: ["security", "networkpolicy", "database", "postgres", "redis"]
---

## Problem
Implement database pod isolation on K3s to restrict PostgreSQL and Redis access only to authorized Kasm application pods. The policy must allow monitoring from Prometheus while blocking all other traffic, ensuring defense-in-depth for sensitive data stores.

## Solution
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kasm-database-isolation
  namespace: kasm
  annotations:
    policy.kubernetes.io/description: "Restrict database access to app pods only"
spec:
  # Apply to database pods (PostgreSQL/Redis)
  podSelector:
    matchLabels:
      app: kasm-database
      tier: database
  policyTypes:
    - Ingress
    - Egress
  
  # Ingress: Only allow from Kasm application pods
  ingress:
    # PostgreSQL access from app pods
    - from:
        - podSelector:
            matchLabels:
              app: kasm-workspace
              tier: application
      ports:
        - protocol: TCP
          port: 5432  # PostgreSQL
    
    # Redis access from app pods
    - from:
        - podSelector:
            matchLabels:
              app: kasm-workspace
              tier: application
      ports:
        - protocol: TCP
          port: 6379  # Redis
    
    # Allow monitoring pods (Prometheus)
    - from:
        - namespaceSelector:
            matchLabels:
              name: monitoring
          podSelector:
            matchLabels:
              app: prometheus
      ports:
        - protocol: TCP
          port: 9187  # PostgreSQL exporter
        - protocol: TCP
          port: 9121  # Redis exporter
  
  # Egress: Allow DNS and external DB backups
  egress:
    # DNS resolution
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    
    # S3/Object storage for backups (adjust CIDR for your cloud)
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8      # Block internal networks
              - 172.16.0.0/12
              - 192.168.0.0/16
      ports:
        - protocol: TCP
          port: 443  # HTTPS for S3/backups
```

## Key Techniques
- Defense-in-depth for database layer
- Label selectors for pod identification (survives rescheduling)
- Separate ingress rules for PostgreSQL (5432) and Redis (6379)
- Monitoring allowlist for Prometheus exporters
- Egress restricted to DNS and external backup storage only
