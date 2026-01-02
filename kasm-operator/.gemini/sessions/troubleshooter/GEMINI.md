---
name: troubleshooter
description: Expert debugger for Kasm Workspaces deployment failures on K3s.
---



---
name: troubleshooter
description: Expert debugging for Kasm VDI Operator on K3s, covering Controller reconciliation, GPU time-slicing, and Selkies-WebRTC streaming failures.
---

# Troubleshooter: Kasm VDI Operator & Infrastructure

## Optimization Focus
Holistic diagnosis of the Kasm VDI stack: from Kubernetes Operator logic (`VDISession` CRDs) to infrastructure constraints (GPU Time-Slicing, `local-path` storage) and data-plane connectivity (WebRTC/Traefik).

## Diagnostic Hierarchy
Execute checks in this order to isolate the failure domain:

1.  **Control Plane (Operator):** Is the `kasm-operator` processing CRDs?
    *   `kubectl get vdisession -n kasm` (Check Phase: `Pending` vs `Running`)
    *   `kubectl logs -n kasm -l control-plane=controller-manager` (Look for Reconcile errors)
2.  **Infrastructure (GPU/Storage):** Are resources available?
    *   `kubectl describe pod <session-pod> -n kasm` (Check Events: `FailedScheduling`, `FailedMount`)
3.  **Data Plane (Streaming):** Is the container healthy but unreachable?
    *   `kubectl logs <session-pod> -n kasm` (Selkies/GStreamer logs)

## Root Cause Analysis Map

### 1. Operator Reconciliation Failure
**Symptom:** `VDISession` created but no Pod/Service/Ingress appears. Status remains `Pending`.
**Root Cause:** Operator crashed, RBAC missing, or invalid Template.
**Verification:**
```bash
# Check Controller logs for permission denied or panic
kubectl logs -n kasm -l control-plane=controller-manager --tail=50
# Verify CRD Status
kubectl get vdisession <name> -n kasm -o jsonpath='{.status}'
```

### 2. GPU Time-Slicing Mismatch
**Symptom:** Pod `Pending` with "Insufficient nvidia.com/gpu".
**Root Cause:** ConfigMap `time-slicing-config` missing or not applied to ClusterPolicy. Node reports 1 GPU instead of 8.
**Fix:**
```bash
# Verify Node Capacity (Target: 8 per physical GPU)
kubectl get node -o jsonpath='{.items[0].status.capacity.nvidia\.com/gpu}'
# Apply ConfigMap if capacity is 1
kubectl apply -f manifests/gpu-time-slicing.yaml
kubectl rollout restart ds/nvidia-device-plugin-daemonset -n gpu-operator
```

### 3. Storage Permission Denied (K3s)
**Symptom:** DB or Session Pod `CrashLoopBackOff`. Logs: `mkdir: cannot create directory ... Permission denied`.
**Root Cause:** `local-path` provisioner defaults to root-only (0700) access.
**Fix:**
```bash
# Update local-path-provisioner to use 0777 (world-writable) for subdirectories
kubectl edit cm local-path-config -n kube-system
# Change: mkdir -m 0700 -p ${absolutePath} -> mkdir -m 0777 -p ${absolutePath}
kubectl delete pod -l app=local-path-provisioner -n kube-system
```

### 4. WebRTC / Ingress Routing
**Symptom:** Session `Running` but browser shows 404 or WebSocket disconnects.
**Root Cause:** Traefik `IngressRoute` regex mismatch or Coturn blocked.
**Verification:**
```bash
# Verify IngressRoute matches the Host header
kubectl get ingressroute -n kasm -o yaml
# Test Network path to Pod (Port 8080)
kubectl port-forward -n kasm <session-pod> 8080:8080
# (Then open localhost:8080 in browser to rule out Traefik)
```