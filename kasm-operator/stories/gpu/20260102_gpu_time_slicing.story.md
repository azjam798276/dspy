---
id: "20260102_gpu_time_slicing"
difficulty: "medium"
tags: ["gpu", "nvidia", "time-slicing", "device-plugin", "k8s"]
tech_stack: "NVIDIA GPU Operator, K3s, ConfigMap"
---

# User Story
As a GPU engineer, I want to configure NVIDIA time-slicing on K3s, so multiple VDI sessions can share a single GPU efficiently.

# Context & Constraints
**Time-Slicing Configuration:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: time-slicing-config
  namespace: gpu-operator
data:
  any: |-
    version: v1
    flags:
      migStrategy: none
    sharing:
      timeSlicing:
        renameByDefault: false
        failRequestsGreaterThanOne: false
        resources:
        - name: nvidia.com/gpu
          replicas: 8
```

**ClusterPolicy Patch:**
```bash
kubectl patch clusterpolicy/cluster-policy \
  -n gpu-operator --type merge \
  -p '{"spec":{"devicePlugin":{"config":{"name":"time-slicing-config"}}}}'
```

**Verification:**
```bash
# Node should show 8x GPU capacity
kubectl describe node gpu-node | grep nvidia.com/gpu
# Expected: nvidia.com/gpu: 8
```

**Sizing Guidelines:**
| GPU | VRAM | Max Replicas |
|-----|------|--------------|
| RTX 3090 | 24GB | 8 |
| Tesla T4 | 16GB | 4-6 |
| A10 | 24GB | 8 |

# Acceptance Criteria
- [ ] **ConfigMap:** Create time-slicing-config with 8 replicas
- [ ] **Patch:** Apply ClusterPolicy patch to GPU Operator
- [ ] **Verify:** Node shows multiplied GPU capacity
- [ ] **Pod:** Pods can request nvidia.com/gpu: 1 (time-slice)
- [ ] **Concurrent:** Verify 4+ pods running simultaneously
- [ ] **Memory:** Document memory limits per session
