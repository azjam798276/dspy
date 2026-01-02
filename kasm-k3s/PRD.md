# PRD: Kasm Workspaces on K3s

## Problem Statement
Deploying Kasm Workspaces on a K3s (lightweight Kubernetes) cluster with pods stuck in `Init:1/5` state, specifically `kasm-proxy-default-deployment`.

## Objective
Establish a reliable Kasm Workspaces installation on K3s with all pods running successfully.

---

## Prerequisites

### Kubernetes Environment
| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| K3s Version | 1.25+ | 1.28+ |
| Nodes | 1 | 3+ |
| CPU (per node) | 2 cores | 4 cores |
| RAM (per node) | 4 GB | 8 GB |
| Storage | 50 GB SSD | 100 GB SSD |

### Required Tools
- **kubectl** configured for your k3s cluster
- **Helm** v3.x
- **git** (to clone Kasm-Helm repo)

### Network Requirements
- LoadBalancer or Ingress Controller (Traefik comes with K3s)
- DNS hostname resolving to cluster nodes
- Ports: 443 (HTTPS), 3389 (RDP over HTTPS)

---

## Installation Steps

### 1. Clone Kasm Helm Repository
```bash
git clone https://github.com/kasmtech/kasm-helm.git
cd kasm-helm
```

### 2. Configure `values.yaml`
Edit `values.yaml` with your settings:
```yaml
global:
  namespace: kasm
  hostname: kasm.yourdomain.com  # Must resolve to your cluster
  clusterDomain: cluster.local

# For k3s, ensure correct storage class
storageClass: local-path  # Default k3s storage class
```

### 3. Create Namespace & Install
```bash
kubectl create namespace kasm
helm install kasm . -n kasm -f values.yaml
```

---

## Troubleshooting: `Init:1/5` State

### Current Error
```
kasm-proxy-default-deployment-68749c644c-c2l9w  0/1  Init:1/5  0  68s
```

This means **1 of 5 init containers** completed, but the 2nd is failing.

### Step 1: Identify Failing Init Container
```bash
kubectl describe pod kasm-proxy-default-deployment-68749c644c-c2l9w -n kasm
```
Look for:
- `Init Containers:` section → find which one has `State: Waiting` or `State: Terminated` with error
- `Events:` section → look for errors like `ImagePullBackOff`, `CrashLoopBackOff`

### Step 2: Get Init Container Logs
```bash
# List init container names first
kubectl get pod <pod-name> -n kasm -o jsonpath='{.spec.initContainers[*].name}'

# Get logs for specific init container (replace <init-container-name>)
kubectl logs <pod-name> -n kasm -c <init-container-name>
```

### Step 3: Common Causes & Fixes

#### ❌ Image Pull Failures
```bash
# Check if images are accessible
kubectl get events -n kasm --field-selector reason=Failed
```
**Fix:** Verify registry credentials or network access to Docker Hub/Kasm registry.

#### ❌ PVC/Storage Issues
```bash
kubectl get pvc -n kasm
kubectl describe pvc <pvc-name> -n kasm
```
**Fix:** Ensure `local-path-provisioner` is running:
```bash
kubectl get pods -n kube-system | grep local-path
```

#### ❌ ConfigMap/Secret Missing
```bash
kubectl get configmaps -n kasm
kubectl get secrets -n kasm
```
**Fix:** Re-run Helm install or check if values.yaml has required secrets.

#### ❌ DNS Resolution Issues (kasm services not resolving)
```bash
# Test DNS from a debug pod
kubectl run -it --rm debug --image=busybox --restart=Never -n kasm -- nslookup kasm-db
```
**Fix:** Check CoreDNS is healthy:
```bash
kubectl get pods -n kube-system | grep coredns
```

#### ❌ Resource Constraints
```bash
kubectl describe node | grep -A5 "Allocated resources"
kubectl top nodes
```
**Fix:** Increase node resources or reduce replica count in values.yaml.

---

## Validation Checklist

| Check | Command | Expected |
|-------|---------|----------|
| All pods running | `kubectl get pods -n kasm` | No `Init:*`, `Pending`, `CrashLoop` |
| Services exposed | `kubectl get svc -n kasm` | External IPs or ClusterIPs assigned |
| PVCs bound | `kubectl get pvc -n kasm` | All `Bound` |
| Ingress configured | `kubectl get ingress -n kasm` | Hostname mapped |
| Web UI accessible | `curl -k https://kasm.yourdomain.com` | HTTP 200 or redirect |

---

## Quick Diagnostic Script
```bash
#!/bin/bash
NAMESPACE="kasm"
echo "=== Pod Status ==="
kubectl get pods -n $NAMESPACE

echo -e "\n=== Recent Events (errors only) ==="
kubectl get events -n $NAMESPACE --field-selector type=Warning | tail -20

echo -e "\n=== PVC Status ==="
kubectl get pvc -n $NAMESPACE

echo -e "\n=== Failing Init Containers ==="
kubectl get pods -n $NAMESPACE -o json | jq -r '
  .items[] | 
  select(.status.initContainerStatuses[]?.state.waiting != null) |
  "\(.metadata.name): \(.status.initContainerStatuses[] | select(.state.waiting != null) | .name) - \(.state.waiting.reason)"
'
```

---

## Architecture Note

> [!IMPORTANT]
> **Kasm Agents must be installed separately on VMs/bare-metal, not in K3s.**
> The Helm chart only deploys core services (API, manager, proxy). Session containers run on external Agents.

---

## Next Steps
1. Run `kubectl describe pod` on the stuck pod
2. Identify which init container (1-5) is failing
3. Check logs for that specific init container
4. Match error to fixes above
5. If unresolved, share the output of the diagnostic script
