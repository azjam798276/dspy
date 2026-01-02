---
id: "20260102_vdisession_crd"
difficulty: "medium"
tags: ["kubernetes", "crd", "openapi", "kubebuilder", "validation"]
tech_stack: "Go 1.21, kubebuilder, OpenAPI v3"
---

# User Story
As a platform engineer, I want a VDISession Custom Resource Definition with proper validation and printer columns, so users can create desktop sessions using kubectl.

# Context & Constraints
**CRD Specification:**
```yaml
apiVersion: vdi.kasm.io/v1alpha1
kind: VDISession
metadata:
  name: alice-desktop
spec:
  user: alice@example.com
  template: ubuntu-desktop
  resources:
    gpu: 1
    memory: "4Gi"
  timeout: "8h"
status:
  phase: Running
  url: https://alice.vdi.example.com
```

**Required Fields:**
| Field | Type | Validation |
|-------|------|------------|
| spec.user | string | Required, email pattern |
| spec.template | string | Required, reference |
| spec.resources.gpu | int | Default: 1, Min: 1 |
| spec.resources.memory | string | Default: "4Gi" |
| spec.timeout | string | Default: "8h", duration |

**Status Fields:**
| Field | Type | Description |
|-------|------|-------------|
| phase | enum | Pending, Creating, Running, Terminating, Failed |
| podName | string | Name of owned Pod |
| url | string | Access URL for session |
| startTime | dateTime | Session start timestamp |
| message | string | Error or status message |

# Acceptance Criteria
- [ ] **Types:** Define VDISessionSpec and VDISessionStatus Go structs
- [ ] **Validation:** Add kubebuilder markers for Required, Default, Enum
- [ ] **PrinterColumns:** Show User, Phase, URL in `kubectl get`
- [ ] **ShortName:** Register `vdi` as shortname
- [ ] **Scope:** Namespaced resource
- [ ] **Subresource:** Enable status subresource
- [ ] **Generate:** Run `make manifests` to create YAML CRD
