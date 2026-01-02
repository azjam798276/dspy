---
id: "helm_values_k3s_golden"
source_story: "kasm-k3s/stories/helm/20260101_helm_values_config.story.md"
source_url: "https://github.com/kasmtech/kasm-helm/tree/release/1.18.0/kasm-single-zone"
tags: ["helm", "kubernetes", "k3s", "kasm", "configuration", "low-resource"]
---

## Problem
Configure Kasm Workspaces Helm chart for a resource-constrained K3s cluster (4-8GB RAM).
- Override default storage class to `local-path`.
- reduce connection/resource limits for single-node.
- Disable internal Ingress/LB to use existing external Traefik.

## Solution

### Optimized values.yaml
```yaml
# path: helm/k3s-values.yaml
global:
  hostname: kasm.example.com
  storageClass: local-path
  image:
    pullPolicy: IfNotPresent  # Use IfNotPresent for dev speed, Always for prod
  ingress:
    enabled: false  # Disable internal LB/Ingress (we use external Traefik)

# PostgreSQL overrides for K3s local-path
postgres:
  primary:
    persistence:
      storageClass: local-path
    resources:
      requests:
        cpu: 250m
        memory: 512Mi
      limits:
        cpu: 500m
        memory: 1Gi

# Low-resource Redis settings
redis:
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 200m
      memory: 512Mi

# Manager tuned for single-node
kasmManager:
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1000m
      memory: 2Gi

# API tuned for single-node
kasmApi:
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: 500m
      memory: 1Gi
```

### Installation Command
```bash
# Verify overrides are applied
helm install kasm ./kasm-single-zone \
  -n kasm \
  --create-namespace \
  -f k3s-values.yaml \
  --wait --timeout 10m
```

## Key Techniques
- **Low Resource Tuning**: Capped CPU/Memory limits prevent OOM on small nodes (4-8GB).
- **Storage Class**: Explicitly set `local-path` for all persistent components (Postgres, etc.).
- **Ingress Strategy**: `global.ingress.enabled: false` prevents conflicts with existing K3s Traefik controller.
