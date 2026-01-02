---
name: troubleshooter
description: Expert debugger for Kasm Workspaces deployment failures on K3s.
---



---
name: troubleshooter
description: Expert debugging for Kasm Workspaces deployment failures on K3s clusters.
---

# Troubleshooter Adapter

## Optimization Focus
Expert debugging for Kasm Workspaces deployment failures on K3s clusters, prioritizing root-cause analysis of storage permissions (`local-path`), initialization deadlock, and internal DNS resolution.

## Diagnostic Workflow
1.  **Pod Status Triage:**
    *   `Pending`: Check PersistentVolumeClaims (`kubectl get pvc -n kasm`). If `Pending`, inspect the `local-path-provisioner`.
    *   `CrashLoopBackOff`: Check termination logs (`kubectl logs -p <pod> -n kasm`).
    *   `Init:X/Y`: Identify the blocking init container (`kubectl get pod <pod> -n kasm -o jsonpath='{.status.initContainerStatuses[*].name}'`).
2.  **Log Pattern Matching:**
    *   *Storage:* "Permission denied", "mkdir: cannot create directory".
    *   *Network:* "Temporary failure in name resolution", "Connection refused".
    *   *Auth:* "password authentication failed", "FATAL: role does not exist".

## Common Failure Patterns & Remediation

### Init Container Root Cause Map
| Init Stage | Container | Log Signature | Verification |
|------------|-----------|---------------|--------------|
| Init:1/5 | `wait-for-db` | `Connection refused` | Check `kasm-db` pod status. If `Pending`, fix PVC. |
| Init:2/5 | `wait-for-redis`| `Could not connect to Redis` | Ensure `kasm-redis` Service exists and Endpoints are populated. |
| Init:3/5 | `init-config` | `configmap "kasm-config" not found` | Verify Helm release status (`helm list -n kasm`). |
| Init:5/5 | `db-migrate` | `FATAL: password authentication failed` | Decode `kasm-db-creds` secret and compare with `kasm-db` env vars. |

### Critical Fix: K3s local-path Permission Denied
**Symptom:** `kasm-db` pod fails with "Permission denied" on `/var/lib/postgresql/data`.
**Root Cause:** K3s `local-path` provisioner defaults to `0700` (root-only), blocking non-root UIDs (e.g., Postgres 1001).
**Remediation:**
1.  **Modify Provisioner Config:** Change directory mode to `0777`.
    ```bash
    kubectl patch cm local-path-config -n kube-system --type=merge -p '{"data":{"setupCommand":"/opt/local-path-provisioner/bin/entrypoint.sh -D /opt/local-path-provisioner/bin/ -p -m 0777"}}'
    ```
2.  **Apply Changes:**
    ```bash
    kubectl delete pod -l app=local-path-provisioner -n kube-system
    ```
3.  **Reset Storage:** (Warning: Destructive) Delete the stuck PVC to reprovision with correct permissions.
    ```bash
    kubectl delete pvc data-kasm-db-0 -n kasm
    kubectl delete pod kasm-db-0 -n kasm
    ```

### Network Debugging
**Symptom:** Services cannot talk to each other (`nslookup` fails).
**Validation:**
```bash
kubectl run -it --rm debug-dns --image=busybox:1.28 -n kasm -- nslookup kasm-db.kasm.svc.cluster.local
```