# Security Engineering: VDI Platform Hardening (Multi-Tenant & Hardware-Aware)

## Core Principles
1. **Zero Trust Identity:** Every request from the Dashboard or qlkube must be authenticated via OIDC. The Operator MUST NOT trust the `spec.user` field in a `VDISession` unless verified against the OIDC identity of the requester.
2. **Cryptographic Isolation:** Each `VDISession` must have a unique, cryptographically strong `SELKIES_BASIC_AUTH_PASSWORD`. NEVER reuse credentials across sessions or store them in plain text in `VDITemplate`.
3. **Control Plane Shielding:** Session pods are hostile by default. They MUST be denied all access to the Kubernetes API server and cluster metadata services (169.254.169.254).
4. **Deterministic Resource Bounds:** Enforce identical `requests` and `limits` for CPU, Memory, and `nvidia.com/gpu`. This prevents oversubscription and ensures that GPU time-slicing remains deterministic and isolated.
5. **Ephemeral State Sovereignty:** User data must exist only within the scope of a `PersistentVolumeClaim` (PVC) owned by the `VDISession`. Upon session deletion, Finalizers MUST ensure the PVC is purged to prevent data leaks between tenants.

## Identity & Impersonation Flow
The Dashboard interacts with the K8s API using user impersonation via `qlkube`:
```
User (JWT) → qlkube (Verify & Extract 'sub') → K8s API (Impersonate User: {sub})
```
- **Constraint:** Use a Validating Admission Webhook to reject `VDISession` creation if `spec.user` does not match the `Impersonated-User` header.

## Hardened RBAC
The Operator's ClusterRole must be scoped to the minimum verbs required for lifecycle management.
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: vdi-operator
rules:
  - apiGroups: ["vdi.kasm.io"]
    resources: ["vdisessions", "vdisessions/status", "vdisessions/finalizers"]
    verbs: ["get", "list", "watch", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods", "services", "persistentvolumeclaims"]
    verbs: ["create", "delete", "get", "list", "patch", "update", "watch"]
  - apiGroups: ["traefik.io"]
    resources: ["ingressroutes"]
    verbs: ["create", "delete", "get", "list", "patch"]
```

## Pod Security Standards (Restricted+)
Apply these mandatory settings to all VDI Pods:
```yaml
securityContext:
  allowPrivilegeEscalation: false
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  seccompProfile: { type: RuntimeDefault }
  capabilities:
    drop: ["ALL"]
    add: ["SYS_PTRACE"] # Only for specific debugger/app support
```

## Network Isolation (Default Deny)
Prevent lateral movement and API discovery.
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: vdi-egress-lockdown
  namespace: vdi
spec:
  podSelector:
    matchLabels: { app.kubernetes.io/name: vdi-session }
  policyTypes: ["Egress"]
  egress:
    - to: # Allow DNS
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: kube-system } }
          podSelector: { matchLabels: { k8s-app: kube-dns } }
      ports: [{ port: 53, protocol: "UDP" }]
    - to: # Allow TURN for WebRTC
        - podSelector: { matchLabels: { app: "coturn" } }
      ports: [{ port: 3478 }]
    - to: [{ ipBlock: { cidr: "0.0.0.0/0", except: ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.169.254/32"] } }]
```

## Threat Model & Mitigation
| Threat | Mitigation |
|--------|------------|
| Control Plane DoS | Mandate `ResourceQuota` in the `vdi` namespace to cap total GPU/CPU/Memory. |
| GPU Memory Scraping | Strict `nvidia.com/gpu: 1` limit + NVIDIA driver-level memory isolation. |
| Ingress Path Traversal | Sanitize `spec.user` labels to prevent directory traversal in Traefik routing rules. |
| Zombie Sessions | Operator MUST enforce `spec.timeout` via a background "reaper" routine in the controller. |

## Compliance Checklist
- [ ] No `hostPath` or `hostNetwork` usage in session pods.
- [ ] `SELKIES_BASIC_AUTH_PASSWORD` generated via `crypto/rand` in the Operator.
- [ ] Traefik `IngressRoute` TLS set to `minVersion: VersionTLS13`.
- [ ] Container images sourced from internal registry with daily vulnerability scans (CVE-free).