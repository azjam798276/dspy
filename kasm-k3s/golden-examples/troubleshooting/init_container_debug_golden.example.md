---
id: "init_container_debug_golden"
source_story: "kasm-k3s/stories/troubleshooting/20260101_init_container_debug.story.md"
source_url: "https://github.com/k3s-io/k3s/issues/3704"
tags: ["troubleshooting", "kubernetes", "init-containers", "kasm", "k3s", "local-path"]
---

## Problem
Debug Kasm pods stuck in `Init:1/5` (wait-for-db) or `CrashLoopBackOff` on K3s.
- "Failed to attach volume" timeout errors.
- "connection refused" for Postgres 5432.
- Permission denied issues with local-path-provisioner.

## Solution

### Scenario 1: PVC Permission/Mount Failure
**Symptom:**
`kubectl describe pod kasm-db-0` shows:
> Warning FailedMount 0s kubelet Failed to attach volume: timeout expired waiting for volumes to attach

**Root Cause:**
`local-path-provisioner` creates directories with `0700` permissions by default, but the Postgres container (running as non-root) needs access.

**Fix:**
```bash
# 1. Edit the local-path-provisioner configmap
kubectl edit cm local-path-config -n kube-system

# 2. Find the "setup" script section and change "mkdir -m 0700" to "0777"
# Before: mkdir -m 0700 -p ${absolutePath}
# After:  mkdir -m 0777 -p ${absolutePath}

# 3. Restart the provisioner to apply changes
kubectl delete pod -l app=local-path-provisioner -n kube-system

# 4. Delete the failing PVC to trigger recreation (DATA LOSS WARNING)
kubectl delete pvc data-kasm-db-0 -n kasm
kubectl delete pod kasm-db-0 -n kasm
```

### Scenario 2: Connection Refused (DNS/Network)
**Symptom:**
Logs from init container:
```bash
kubectl logs kasm-proxy-init-wait-db -c wait-for-db --previous
# Output: "dial tcp postgres:5432: connect: connection refused"
```

**Root Cause:**
Database pod is not ready (due to PVC bind failure above) or stale network state.

**Fix:**
```bash
# 1. Nuke deployment (if fresh install)
helm uninstall kasm -n kasm
kubectl delete pvc --all -n kasm

# 2. Clean up stale local-path data on the node (requires sudo)
sudo rm -rf /var/lib/rancher/k3s/storage/*kasm*

# 3. Reinstall
helm install kasm ./kasm-single-zone -n kasm -f k3s-values.yaml
```

## Key Techniques
- **Event Analysis**: "FailedMount" points to PVC/StorageClass issues.
- **Log Inspection**: `kubectl logs ... --previous` captures errors from crashed init containers.
- **K3s Specifics**: modifying `local-path-config` is often required for non-root containers like Postgres.
