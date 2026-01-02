---
id: "network_policy_isolation_golden"
source_story: "kasm-k3s/stories/security/20260101_network_policy_isolation.story.md"
source_url: "https://docs.kasm.com/docs/latest/how-to/infrastructure_components/pools"
tags: ["security", "network-policy", "kubernetes", "kasm", "isolation"]
---

## Problem
Harden Kasm namespace by blocking external access to Database/Redis and defaulting to Deny All.

## Solution

### 1. Default Deny Policy
Blocks all ingress/egress unless explicitly allowed.
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: kasm
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### 2. Allow API/Manager Access to Postgres
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-db-access
  namespace: kasm
spec:
  podSelector:
    matchLabels:
      app: postgres  # Verify label matches helm chart (often: kasm-db)
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: kasm-manager
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: kasm-api
    ports:
    - protocol: TCP
      port: 5432
```

### 3. Allow Manager Access to Redis
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-redis-access
  namespace: kasm
spec:
  podSelector:
    matchLabels:
      app: redis # Verify label (often: kasm-redis)
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: kasm-manager
    ports:
    - protocol: TCP
      port: 6379
```

## Key Techniques
- **Zero Trust**: Start with `default-deny` for both Ingress and Egress.
- **Service Isolation**: Only Kasm API/Manager need DB access; Proxy and Guacamole do not.
- **Label Matching**: Critical to verify `matchLabels` against running pods (`kubectl get pods --show-labels`) as Helm chart labels vary by version.
