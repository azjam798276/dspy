---
id: "20260102_helm_chart"
difficulty: "hard"
tags: ["devops", "helm", "kubernetes", "deployment", "operator"]
tech_stack: "Helm 3, Kubernetes, Go"
---

# User Story
As a DevOps engineer, I want a Helm chart for the VDI Operator, so I can deploy and configure the platform with a single command.

# Context & Constraints
**Chart Structure:**
```
charts/vdi-operator/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── rbac.yaml
│   ├── crds/
│   │   ├── vdisession-crd.yaml
│   │   └── vditemplate-crd.yaml
│   ├── configmap.yaml
│   ├── service.yaml
│   └── servicemonitor.yaml
└── charts/
    └── coturn/
```

**values.yaml:**
```yaml
operator:
  image:
    repository: ghcr.io/org/vdi-operator
    tag: v0.1.0
  replicas: 1

selkies:
  image: ghcr.io/selkies-project/selkies-gstreamer/gst-web:latest
  defaultResources:
    gpu: 1
    memory: 4Gi

ingress:
  enabled: true
  className: traefik
  domain: vdi.example.com
```

**Deployment Command:**
```bash
helm install vdi-operator ./charts/vdi-operator \
  --namespace vdi-operator --create-namespace \
  --set operator.image.tag=v0.1.0 \
  --set ingress.domain=vdi.mycompany.com
```

# Acceptance Criteria
- [ ] **Chart.yaml:** Define chart name, version, appVersion
- [ ] **values.yaml:** Configurable image, domain, resources
- [ ] **CRDs:** Include VDISession and VDITemplate CRDs
- [ ] **RBAC:** ServiceAccount, ClusterRole, ClusterRoleBinding
- [ ] **Deployment:** Operator deployment with configurable replicas
- [ ] **Service:** Metrics service for Prometheus scraping
- [ ] **Upgrade:** `helm upgrade` works without downtime
