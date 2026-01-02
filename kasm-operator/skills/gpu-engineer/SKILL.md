---
name: gpu-engineer
description: GPU Infrastructure Engineer for NVIDIA Time-Slicing and Resource Management
---



# GPU Engineering: NVIDIA Time-Slicing and Multi-Tenant Resource Management

## Core Principles
1. **Time-Slicing over MIG:** For VDI workloads, time-slicing provides better density than MIG partitioning.
2. **Memory Limits:** Enforce per-session memory limits to prevent OOM cascades.
3. **NVENC Prioritization:** Ensure encoding has priority over compute workloads.
4. **No Oversubscription:** Never allocate more slices than configured replicas.

## GPU Operator Configuration
```yaml
# time-slicing-config ConfigMap
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

## ClusterPolicy Patch
```bash
kubectl patch clusterpolicy/cluster-policy \
  -n gpu-operator --type merge \
  -p '{"spec":{"devicePlugin":{"config":{"name":"time-slicing-config"}}}}'
```

## Verification Commands
```bash
# Verify time-slices appear as capacity
kubectl describe node <gpu-node> | grep nvidia.com/gpu
# Expected: nvidia.com/gpu: 8

# Check GPU operator pods
kubectl get pods -n gpu-operator

# Verify NVENC availability
nvidia-smi -q | grep Encoder
```

## Pod GPU Resource Requests
```yaml
resources:
  limits:
    nvidia.com/gpu: "1"    # One time-slice
    memory: "4Gi"          # Bounded memory
  requests:
    nvidia.com/gpu: "1"    # Must match limit
```

## Memory Management
- Each time-slice shares full GPU memory by default
- Enforce process-level limits via `CUDA_MPS_PINNED_DEVICE_MEM_LIMIT`
- Monitor with `nvidia-smi dmon -s u` for utilization

## Time-Slice Sizing Guidelines
| GPU Model | VRAM | Max Replicas | Use Case |
|-----------|------|--------------|----------|
| RTX 3090 | 24GB | 8 | Heavy desktop |
| RTX 4090 | 24GB | 8-12 | Mixed workload |
| Tesla T4 | 16GB | 4-6 | Cloud VDI |
| A10 | 24GB | 8 | Enterprise |

## NVENC Session Limits
```bash
# Check encoder sessions
nvidia-smi -q | grep -A 5 "Encoder"

# Common limits:
# - Consumer GPUs: 3-5 concurrent sessions (driver limited)
# - Professional GPUs: Unlimited
# - Use nvidia-patch for consumer GPU unlocking (if licensed)
```

## Scheduling Constraints
```yaml
# Ensure VDI pods only schedule on GPU nodes
nodeSelector:
  nvidia.com/gpu.present: "true"

tolerations:
- key: nvidia.com/gpu
  operator: Exists
  effect: NoSchedule
```

## Failure Modes & Recovery
| Failure | Detection | Recovery |
|---------|-----------|----------|
| OOM Killed | `kubectl describe pod` | Reduce memory limit or replicas |
| NVENC saturated | Encoder lag in logs | Reduce concurrent sessions |
| Driver crash | Node NotReady | Cordon node, drain sessions |
| Time-slice starvation | High latency | Reduce replicas per GPU |

## Monitoring Metrics
```promql
# GPU utilization per pod
DCGM_FI_DEV_GPU_UTIL{pod=~"vdi-.*"}

# Memory usage
DCGM_FI_DEV_FB_USED{pod=~"vdi-.*"}

# Encoder utilization
DCGM_FI_DEV_ENC_UTIL{pod=~"vdi-.*"}
```

## Performance Targets
| Metric | Threshold |
|--------|-----------|
| GPU utilization | > 80% aggregate |
| Sessions per GPU | 4-8 concurrent |
| OOM events | 0 per day |
| Scheduling latency | < 5s |