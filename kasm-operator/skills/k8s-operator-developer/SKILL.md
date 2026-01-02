---
name: k8s-operator-developer
description: Kubernetes Operator Developer using kubebuilder for VDI Session Management
---









# Kubernetes Operator Development: CRDs, Controllers, and Reconciliation

## Core Principles
1. **Declarative State Management:** Controllers reconcile desired state (CRD spec) with actual state (cluster resources).
2. **Idempotent Reconciliation:** Every `Reconcile()` call must be safe to re-run; never assume previous state.
3. **Finalizer Discipline:** Use finalizers for cleanup; always remove finalizer after successful cleanup.
4. **Status Subresource:** Update status separately from spec; use `Status().Update()` not `Update()`.

## CRD Design Patterns
- Required fields in `spec` must be validated with `+kubebuilder:validation:Required`
- Use enums for phase fields: `+kubebuilder:validation:Enum=Pending;Creating;Running;Terminating;Failed`
- Add printer columns for `kubectl get` readability
- Scope: Namespaced for sessions, Cluster for templates

```go
// VDISession spec example
type VDISessionSpec struct {
    // +kubebuilder:validation:Required
    User     string `json:"user"`
    Template string `json:"template"`
    Resources ResourceSpec `json:"resources,omitempty"`
    Timeout  string `json:"timeout,omitempty"`
}
```

## Controller Implementation
```go
func (r *VDISessionReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    // 1. Fetch resource - return if not found (deleted)
    // 2. Handle deletion with finalizers
    // 3. Add finalizer if missing
    // 4. Fetch referenced resources (templates)
    // 5. Reconcile owned resources (Pod, PVC, Service, Ingress)
    // 6. Update status
    // 7. Check timeouts/expiry
    // 8. Requeue with appropriate interval
    return ctrl.Result{RequeueAfter: 30 * time.Second}, nil
}
```

## Owned Resource Management
- Set `controllerutil.SetControllerReference()` on all created resources
- Use `CreateOrUpdate()` pattern for idempotency:
```go
_, err := ctrl.CreateOrUpdate(ctx, r.Client, pod, func() error {
    // Mutate pod here
    return controllerutil.SetControllerReference(session, pod, r.Scheme)
})
```

## Finalizer Pattern
```go
const sessionFinalizer = "vdi.kasm.io/session-cleanup"

// On deletion
if !session.DeletionTimestamp.IsZero() {
    if controllerutil.ContainsFinalizer(session, sessionFinalizer) {
        // Cleanup owned resources
        if err := r.cleanupResources(ctx, session); err != nil {
            return ctrl.Result{}, err
        }
        controllerutil.RemoveFinalizer(session, sessionFinalizer)
        return ctrl.Result{}, r.Update(ctx, session)
    }
    return ctrl.Result{}, nil
}
```

## Status Updates
- Phase transitions: `Pending` → `Creating` → `Running` → `Terminating`
- Include message field for error details
- Track startTime for timeout enforcement
- URL field for user access endpoint

## Error Handling
- Transient errors: return `ctrl.Result{RequeueAfter: time.Second}` with error
- Permanent errors: update status with Failed phase, don't requeue
- Use `client.IgnoreNotFound(err)` for GET operations

## Testing Strategy
- Unit tests: mock client, test reconcile logic
- Integration tests: envtest with real API server
- Use Ginkgo/Gomega: `Eventually()` for async assertions

## Performance Targets
| Metric | Threshold |
|--------|-----------|
| Reconcile latency | < 100ms |
| Session startup | < 30s total |
| Status update | Every 30s |