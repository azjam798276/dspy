---
id: "20260102_vditemplate_crd"
difficulty: "easy"
tags: ["kubernetes", "crd", "template", "kubebuilder"]
tech_stack: "Go 1.21, kubebuilder"
---

# User Story
As a platform admin, I want a VDITemplate CRD to define available desktop environments, so users can choose from pre-configured templates.

# Context & Constraints
**CRD Specification:**
```yaml
apiVersion: vdi.kasm.io/v1alpha1
kind: VDITemplate
metadata:
  name: ubuntu-desktop
spec:
  image: ghcr.io/selkies-project/selkies-gstreamer/gst-web:latest
  displayName: "Ubuntu 22.04 Desktop"
  description: "Full Ubuntu desktop with GPU acceleration"
  resources:
    defaultGPU: 1
    defaultMemory: "4Gi"
    defaultCPU: "2"
  env:
    - name: SELKIES_ENCODER
      value: "nvh264enc"
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| spec.image | string | Container image (required) |
| spec.displayName | string | Human-readable name |
| spec.description | string | Template description |
| spec.resources | object | Default resource allocations |
| spec.env | []EnvVar | Environment variables |

# Acceptance Criteria
- [ ] **Types:** Define VDITemplateSpec Go struct
- [ ] **Image:** Required image field with kubebuilder marker
- [ ] **Defaults:** Default values for resources
- [ ] **Scope:** Cluster-scoped resource (not namespaced)
- [ ] **Generate:** Create CRD YAML via `make manifests`
