---
name: k8s-operator
description: Kubernetes Operator for Kasm Workspaces lifecycle management on K3s.
---



# Kubernetes Operator Adapter

## Kasm on K3s: Advanced Troubleshooting

### 1. Precise Init-Container Targeting
- **Status Analysis:** `Init:X/Y` indicates the container at index `X` is the current blocker.
- **Name Resolution:** Use `kubectl get pod <pod> -n kasm -o jsonpath='{.spec.initContainers[X].name}'` to resolve the container name reliably.
- **Log Retrieval:** `kubectl logs <pod> -n kasm -c <resolved_name> --previous` (toggles to `--previous` if restarted).

### 2. Storage Permission Patterns
- **Root Cause:** K3s `local-path` provisioner creates root-owned host directories; Kasm services (UID 1000) fail with `PermissionDenied`.
- **Remediation:** Verify host path permissions (force `0777` or `chown 1000:1000`).
- **Validation:** Check `kubectl get pvc -n kasm` is `Bound` and watch for `FailedMount` events.

### 3. Contextual Diagnostics
```bash
# Capture full event context
kubectl describe pod <pod> -n kasm | grep -A30 "Events:"
# Verify internal service connectivity
kubectl get endpoints,svc -n kasm
```