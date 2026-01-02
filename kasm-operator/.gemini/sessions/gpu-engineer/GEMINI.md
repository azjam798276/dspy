# GPU Engineering: NVIDIA Time-Slicing and Multi-Tenant Resource Management

## Core Principles
1. **Validate First, Build Second**: Always verify the data plane (WebRTC streaming, GPU time-slicing) manually via `manifests/phase-0/` before implementing operator automation.
2. **Time-Slicing over MIG**: For VDI workloads, time-slicing provides better density than MIG partitioning, targeting the project goal of 8 concurrent sessions per physical GPU.
3. **Strict Resource Discipline**: Resource `limits` and `requests` for `nvidia.com/gpu` must be identical and set to `1` per session to ensure deterministic time-slice scheduling and prevent oversubscription.
4. **Hardware-Accelerated Encoding**: Mandatory use of `SELKIES_ENCODER=nvh264enc` (NVENC) to meet the <50ms glass-to-glass latency SLO. Fallback to CPU encoding only if hardware resources are unavailable.
5. **Memory Isolation**: Enforce per-session memory limits to prevent OOM cascades and protect GPU stability.

## Phase 0: Validation Manifest
Before deploying the operator, verify GPU slicing with a standalone pod:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-validation-pod
spec:
  containers:
  - name: selkies
    image: ghcr.io/selkies-project/selkies-gstreamer/gst-web:latest
    env:
    - name: SELKIES_ENCODER
      value: "nvh264enc"
    resources:
      limits:
        nvidia.com/gpu: "1"
        memory: "4Gi"
      requests:
        nvidia.com/gpu: "1"
    volumeMounts:
    - name: shm
      mountPath: /dev/shm
  volumes:
  - name: shm
    emptyDir: { medium: Memory }
```

## GPU Operator Configuration
```yaml
# time-slicing-config ConfigMap in gpu-operator namespace
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

## Verification & Monitoring
```bash
# Verify time-slices appear as capacity (Target: 8)
kubectl describe node <gpu-node> | grep nvidia.com/gpu

# Verify NVENC availability and session count
nvidia-smi -q | grep -A 5 "Encoder"

# Check GPU operator pods
kubectl get pods -n gpu-operator
```

## Scheduling & Resource Constraints
```yaml
# Pod Spec Requirements
resources:
  limits:
    nvidia.com/gpu: "1"    # One time-slice
    memory: "4Gi"          # Bounded memory
  requests:
    nvidia.com/gpu: "1"    # Must match limit

nodeSelector:
  nvidia.com/gpu.present: "true"

tolerations:
- key: nvidia.com/gpu
  operator: Exists
  effect: NoSchedule
```

## Time-Slice Sizing Guidelines
| GPU Model | VRAM | Max Replicas | Target Latency |
|-----------|------|--------------|----------------|
| RTX 3090  | 24GB | 8            | < 50ms         |
| RTX 4090  | 24GB | 8-12         | < 30ms         |
| Tesla T4  | 16GB | 4-6          | < 50ms         |
| A10 / L4  | 24GB | 8            | < 50ms         |

## Failure Modes & Recovery
| Failure | Detection | Recovery |
|---------|-----------|----------|
| OOM Killed | `kubectl describe pod` | Reduce memory limit or replicas |
| NVENC Saturated | Encoder lag in logs | Reduce concurrent sessions |
| Starvation | High latency / Stutter | Verify time-slice replicas vs active pods |
| Driver Crash | Node NotReady | Cordon node, drain sessions |

## Monitoring Metrics (PromQL)
```promql
# GPU utilization per pod
DCGM_FI_DEV_GPU_UTIL{pod=~"vdi-.*"}

# Memory usage (Framebuffer)
DCGM_FI_DEV_FB_USED{pod=~"vdi-.*"}

# Encoder utilization
DCGM_FI_DEV_ENC_UTIL{pod=~"vdi-.*"}
```