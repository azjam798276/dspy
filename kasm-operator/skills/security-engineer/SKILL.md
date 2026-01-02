---
name: security-engineer
description: Security Engineer for VDI Platform Hardening and Compliance
---



# Security Engineering: VDI Platform Hardening

## Core Principles
1. **Zero Trust Architecture:** Never trust, always verify. Every request between users, the dashboard, and the Kubernetes API must be authenticated via OIDC and authorized via RBAC.
2. **Strict Least Privilege:** Both the VDI Operator and individual session pods must operate with the absolute minimum set of permissions. Use namespace isolation and specific resource names where possible.
3. **Hardware-Level Isolation:** Leverage NVIDIA GPU time-slicing and strict memory limits to prevent cross-session resource exhaustion or side-channel attacks.
4. **Secure by Default Lifecycle:** From image scanning to session auto-termination (finalizers), security is baked into the entire lifecycle of a `VDISession`.

## Authentication & Authorization Flow
Implement a secure "Impersonation" flow for the dashboard to interact with the K8s API:
```
User (Browser) → Keycloak (MFA) → Dashboard (OIDC Token)
                                       │
                                       ▼
                               qlkube (Verifies Token)
                                       │
                                       ▼
                               K8s API (User Impersonation)
```
- **Constraint:** Dashboard must never use a high-privilege ServiceAccount to perform actions on behalf of users. Use `qlkube` to translate OIDC identities to K8s User identities.

## RBAC Configuration
### Operator Permissions (Minimal)
The operator requires `patch` permissions for status updates and finalizer management (`vdi.kasm.io/session-cleanup`).
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: vdi-operator
rules:
  - apiGroups: ["vdi.kasm.io"]
    resources: ["vdisessions", "vditemplates"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["pods", "services", "persistentvolumeclaims"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["traefik.io"]
    resources: ["ingressroutes"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

### User Session Control
Users should only be able to view and manage their own sessions.
- **Enforcement:** Use an Admission Webhook or `qlkube` filters to ensure `VDISession.spec.user` matches the authenticated OIDC sub.

## Pod Security Standards
Sessions must adhere to the Restricted Pod Security Standard:
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop: ["ALL"]
    add: ["SYS_PTRACE"] # Only if required for specific desktop apps
```
- **GPU Security:** Ensure `nvidia.com/gpu: 1` is strictly enforced via limits to prevent OOM in time-sliced environments.

## Network Isolation (Multi-Tenant)
Prevent lateral movement between sessions and access to cluster internals.
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: session-isolation
  namespace: vdi
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: vdi-session
  policyTypes: ["Ingress", "Egress"]
  ingress:
    - from:
        - namespaceSelector: { matchLabels: { name: "traefik" } }
      ports:
        - port: 8080
  egress:
    - to: [{ ipBlock: { cidr: "0.0.0.0/0", except: ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"] } }]
    - to: # Allow DNS
        - namespaceSelector: { matchLabels: { name: "kube-system" } }
      ports: [{ port: 53, protocol: "UDP" }, { port: 53, protocol: "TCP" }]
    - to: # Allow TURN/STUN for WebRTC
        - podSelector: { matchLabels: { app: "coturn" } }
      ports: [{ port: 3478 }]
```

## Secrets & Data Plane Security
- **Dynamic Credentials:** `SELKIES_BASIC_AUTH_PASSWORD` must be unique per session and never stored in cleartext in the `VDISession` object.
- **TLS 1.3:** Enforce TLS 1.3 for all Traefik `IngressRoute` objects using `TLSOption`.
- **Image Trust:** Only allow images from signed/trusted registries. Implement `ImagePolicyWebhook` if possible.

## Threat Model & Mitigation
| Threat | Mitigation |
|--------|------------|
| GPU Resource Exhaustion | Enforce `nvidia.com/gpu` replicas limits (Max 8 per physical GPU). |
| Data Exfiltration | Disable clipboard/drive sharing in `VDITemplate` properties. |
| Ingress Spoofing | Use `Host(`{user}.vdi.example.com`)` with sanitized usernames in IngressRoutes. |
| Stale Sessions | Implement auto-termination logic using `VDISession.spec.timeout`. |

## Compliance Checklist
- [ ] Operator RBAC contains no wildcard `*` permissions.
- [ ] `VDITemplate` changes are audited via K8s Audit Policy.
- [ ] NetworkPolicy blocks access to Cloud Metadata APIs (169.254.169.254).
- [ ] Persistent volumes use encrypted storage classes (where supported by `local-path`).
- [ ] Coturn server is host-networked but restricted via firewall to UDP 3478 and 49152-65535.