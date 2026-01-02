---
id: "20260102_vdisession_controller"
difficulty: "hard"
tags: ["kubernetes", "operator", "kubebuilder", "go", "reconciliation"]
tech_stack: "Go 1.21, kubebuilder, controller-runtime, client-go"
---

# User Story
As a platform engineer, I want a Kubernetes controller that reconciles VDISession CRDs into running desktop pods, so users can declaratively request GPU-accelerated desktop sessions.

# Context & Constraints
**Controller Architecture:**
```go
type VDISessionReconciler struct {
    client.Client
    Scheme *runtime.Scheme
}
```

**Reconcile Flow:**
```
1. Fetch VDISession → if not found, stop
2. Handle deletion (finalizer cleanup)
3. Add finalizer if missing
4. Fetch VDITemplate reference
5. Reconcile: Pod, PVC, Service, IngressRoute
6. Update VDISession.status
7. Check session timeout
8. Requeue after 30s
```

**Status Phases:**
| Phase | Description |
|-------|-------------|
| Pending | Waiting for resources |
| Creating | Pod starting |
| Running | Session active |
| Terminating | Cleanup in progress |
| Failed | Error state |

**Performance Requirements:**
| Metric | Threshold |
|--------|-----------|
| Reconcile latency | < 100ms |
| Session startup | < 30s total |
| Status update interval | 30s |

# Acceptance Criteria
- [ ] **Fetch:** Get VDISession, return if NotFound
- [ ] **Finalizer:** Add `vdi.kasm.io/session-cleanup` finalizer on create
- [ ] **Template:** Lookup VDITemplate, set Failed status if not found
- [ ] **Pod:** Create Pod with owner reference to VDISession
- [ ] **PVC:** Create PersistentVolumeClaim if persistence.enabled
- [ ] **Service:** Create ClusterIP Service for Pod port 8080
- [ ] **Ingress:** Create Traefik IngressRoute with user-specific host
- [ ] **Status:** Update phase, podName, url, startTime fields
- [ ] **Timeout:** Delete session if startTime + timeout exceeded
- [ ] **Cleanup:** On deletion, remove owned resources before removing finalizer
