---
id: "20260102_rbac_security"
difficulty: "medium"
tags: ["security", "rbac", "kubernetes", "serviceaccount", "permissions"]
tech_stack: "Kubernetes RBAC, Go"
---

# User Story
As a security engineer, I want least-privilege RBAC for the VDI operator and users, so the platform follows security best practices.

# Context & Constraints
**Operator ServiceAccount:**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vdi-operator
  namespace: vdi-operator
```

**ClusterRole (Operator):**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: vdi-operator
rules:
  - apiGroups: ["vdi.kasm.io"]
    resources: ["vdisessions", "vdisessions/status"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["vdi.kasm.io"]
    resources: ["vditemplates"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods", "services", "persistentvolumeclaims"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["traefik.io"]
    resources: ["ingressroutes"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

**User Role (Per-Namespace):**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: vdi-user
  namespace: vdi
rules:
  - apiGroups: ["vdi.kasm.io"]
    resources: ["vdisessions"]
    verbs: ["get", "list", "create", "delete"]
    # Note: Cannot update/patch - prevents hijacking
```

# Acceptance Criteria
- [ ] **ServiceAccount:** Create operator ServiceAccount
- [ ] **ClusterRole:** Minimal permissions for operator
- [ ] **User Role:** Namespace-scoped role for users
- [ ] **No Secrets Access:** Operator cannot read arbitrary secrets
- [ ] **No Pod Exec:** Users cannot exec into session pods
- [ ] **Audit:** Enable audit logging for VDI resources
