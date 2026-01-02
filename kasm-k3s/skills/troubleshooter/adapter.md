---
name: troubleshooter
description: Expert debugging for Kasm Workspaces deployment failures on K3s clusters.
---

# Troubleshooter Adapter

## Optimization Focus
Expert debugging for Kasm Workspaces deployment failures on K3s clusters, specifically targeting persistent storage, initialization sequences, and network connectivity.

## Diagnostic Workflow
1.  **Identify State:** Check `kubectl get pods -n kasm` for `Pending`, `CrashLoopBackOff`, or `Init:X/Y`.
2.  **Analyze Events:** Run `kubectl describe pod <pod-name> -n kasm` to check for Scheduling failures (PVC issues) or Image Pull errors.
3.  **Inspect Logs:** For Init failures, check `kubectl logs <pod-name> -n kasm -c <container-name>`.

## Common Failure Patterns

### Init Container Root Cause Map
| Init Stage | Container Name | Likely Cause | Verification |
|------------|---------------|-------------|--------------|
| Init:1/5 | `wait-for-db` | Database not ready / PVC Pending | Check `kubectl get pvc -n kasm`. If Pending, check StorageClass. |
| Init:2/5 | `wait-for-redis`| Redis not ready | Check `kasm-redis` pod status. |
| Init:3/5 | `init-config` | ConfigMap missing | `kubectl get cm -n kasm` |
| Init:4/5 | `init-certs` | TLS Secrets missing | `kubectl get secrets -n kasm` |
| Init:5/5 | `db-migrate` | DB Connection/Auth failed | Check `DATABASE_URL` in secrets. |

### Storage: K3s local-path Permission Denied
**Symptom:** DB Pod in `CrashLoopBackOff` with "Permission denied" on data directory.
**Root Cause:** K3s `local-path` provisioner defaults to `0700` permissions, which blocks non-root users (like `postgres` UID 1001).
**Fix:**
```bash
kubectl edit cm local-path-config -n kube-system
# Locate "setup" script and change:
# mkdir -m 0700 ... -> mkdir -m 0777 ...
kubectl delete pod -l app=local-path-provisioner -n kube-system
# Delete old PVC/Pod to re-provision
```

### Network: DNS Resolution
**Symptom:** "Host not found" errors in logs.
**Verification:**
```bash
kubectl run -it --rm debug --image=busybox -n kasm -- nslookup kasm-db
```