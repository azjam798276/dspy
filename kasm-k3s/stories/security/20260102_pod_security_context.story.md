---
id: "20260102_pod_security_context"
difficulty: "easy"
tags: ["security", "pod-security", "kubernetes", "kasm", "hardening"]
tech_stack: "Kubernetes, K3s, SecurityContext"
---

# User Story
As a security engineer, I want to configure Kasm Workspaces pods with hardened security context: non-root execution, read-only root filesystem, and dropped Linux capabilities.

# Context & Constraints
Implement container hardening for Kasm deployments:

**Requirements:**
- Run containers as non-root user (UID 1000)
- Enable `readOnlyRootFilesystem: true`
- Mount emptyDir volumes for writable paths (/tmp, /var/run)
- Drop all Linux capabilities
- Enable seccomp RuntimeDefault profile

**Pod Security Context:**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
```

**Container Security Context:**
```yaml
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
```

# Acceptance Criteria
- [ ] Pod runs as UID 1000 (non-root)
- [ ] Root filesystem is read-only
- [ ] /tmp mounted as emptyDir with sizeLimit
- [ ] All capabilities dropped
- [ ] seccompProfile type RuntimeDefault
