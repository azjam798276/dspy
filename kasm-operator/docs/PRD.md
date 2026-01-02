# Kasm Operator for K3s - Hybrid Architecture

## Product Requirements Document (PRD) v2.0

---

## 1. Executive Summary

This document defines a **hybrid approach** to building a Kubernetes-native VDI platform that combines:

1. **Selkies-GStreamer** - Open-source WebRTC streaming (lowest latency)
2. **Custom Kubernetes Operator** - Session lifecycle management via CRDs
3. **NVIDIA GPU Time-Slicing** - Multi-user GPU sharing for cost efficiency

The strategy is **"Validate First, Build Second"**: deploy a working Selkies VDI immediately, then wrap it with operator automation over 4 weeks.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          K3s Cluster                                 │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    CONTROL PLANE                                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │ │
│  │  │ VDI Operator │  │   qlkube     │  │  Dashboard   │          │ │
│  │  │  (Week 2+)   │  │  (GraphQL)   │  │   (React)    │          │ │
│  │  └──────┬───────┘  └──────────────┘  └──────────────┘          │ │
│  │         │ reconciles                                            │ │
│  └─────────┼──────────────────────────────────────────────────────┘ │
│            │                                                         │
│            ▼                                                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    DATA PLANE (GPU Node)                        │ │
│  │                                                                  │ │
│  │   Physical GPU: NVIDIA RTX/Tesla                                │ │
│  │   Time-Slicing: 4-8 replicas                                    │ │
│  │                                                                  │ │
│  │   ┌─────────────────┐  ┌─────────────────┐                      │ │
│  │   │ Selkies Pod     │  │ Selkies Pod     │  ...                 │ │
│  │   │ ┌─────────────┐ │  │ ┌─────────────┐ │                      │ │
│  │   │ │ Desktop Env │ │  │ │ Desktop Env │ │                      │ │
│  │   │ │ (XFCE/KDE)  │ │  │ │ (XFCE/KDE)  │ │                      │ │
│  │   │ └─────────────┘ │  │ └─────────────┘ │                      │ │
│  │   │ ┌─────────────┐ │  │ ┌─────────────┐ │                      │ │
│  │   │ │ GStreamer   │ │  │ │ GStreamer   │ │                      │ │
│  │   │ │ + NVENC     │ │  │ │ + NVENC     │ │                      │ │
│  │   │ └─────────────┘ │  │ └─────────────┘ │                      │ │
│  │   │ ┌─────────────┐ │  │ ┌─────────────┐ │                      │ │
│  │   │ │ WebRTC Out  │ │  │ │ WebRTC Out  │ │                      │ │
│  │   │ └──────┬──────┘ │  │ └──────┬──────┘ │                      │ │
│  │   │  gpu: 1 slice   │  │  gpu: 1 slice   │                      │ │
│  │   └────────┼────────┘  └────────┼────────┘                      │ │
│  │            │                    │                                │ │
│  └────────────┼────────────────────┼────────────────────────────────┘ │
│               │                    │                                  │
│               ▼                    ▼                                  │
│         [Traefik Ingress + TURN Server]                              │
│                      │                                                │
└──────────────────────┼────────────────────────────────────────────────┘
                       │ WebRTC (UDP)
                       ▼
                  🌐 Browser (60 FPS, <30ms latency)
```

---

## 3. Technology Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| **Streaming** | Selkies-GStreamer | WebRTC, lowest latency, NVENC support |
| **GPU Sharing** | NVIDIA Time-Slicing | 4-8x density, no MIG required |
| **Orchestration** | Kubernetes Operator | CRD-based, declarative, self-healing |
| **Ingress** | Traefik + Coturn | WebSocket upgrade, TURN relay for NAT |
| **Storage** | local-path-provisioner | K3s native, simple for POC |
| **Dashboard** | React + qlkube | GraphQL to K8s API |

---

## 4. Implementation Phases

### Phase 0: Immediate Validation (Day 1-2) ✅ PRIORITY

**Goal**: Prove GPU time-slicing + WebRTC streaming works on K3s

```yaml
# Deploy single Selkies pod with GPU slice
apiVersion: v1
kind: Pod
metadata:
  name: selkies-test
  namespace: vdi
spec:
  containers:
  - name: selkies
    image: ghcr.io/selkies-project/selkies-gstreamer/gst-web:latest
    env:
    - name: SELKIES_ENCODER
      value: "nvh264enc"
    - name: SELKIES_BASIC_AUTH_PASSWORD
      value: "test123"
    resources:
      limits:
        nvidia.com/gpu: "1"
        memory: "4Gi"
    ports:
    - containerPort: 8080
```

**Success Criteria**:
- [ ] Pod scheduled on GPU node
- [ ] NVENC encoder active (check logs)
- [ ] WebRTC stream accessible via browser
- [ ] Multiple pods share single GPU

---

### Phase 1: Multi-User Deployment (Week 1)

**Goal**: Deploy 4-8 concurrent Selkies desktops with time-slicing

**Tasks**:
- [ ] Configure GPU Operator with time-slicing (8 replicas)
- [ ] Create Deployment with 4 replicas
- [ ] Set up Traefik IngressRoute per user
- [ ] Deploy Coturn TURN server for NAT traversal
- [ ] Configure PVC templates for user persistence

**Deliverables**:
```
/manifests/
├── gpu-time-slicing-config.yaml
├── selkies-deployment.yaml
├── selkies-service.yaml
├── traefik-ingressroute.yaml
├── coturn-deployment.yaml
└── user-pvc-template.yaml
```

---

### Phase 2: CRD & Operator Scaffolding (Week 2)

**Goal**: Define custom resources and generate operator boilerplate

**Custom Resource Definitions**:

```yaml
# VDISession CRD - Represents a user's desktop session
apiVersion: vdi.kasm.io/v1alpha1
kind: VDISession
metadata:
  name: user-alice-session
  namespace: vdi
spec:
  user: alice@example.com
  template: ubuntu-desktop
  resources:
    gpu: 1        # Time-slice count
    memory: 4Gi
    cpu: 2
  persistence:
    enabled: true
    size: 10Gi
  timeout: 8h     # Auto-terminate after 8 hours
status:
  phase: Running  # Pending | Running | Terminating
  podName: selkies-alice-xyz
  url: https://alice.vdi.example.com
  startTime: "2026-01-02T10:00:00Z"
```

```yaml
# VDITemplate CRD - Defines available desktop environments
apiVersion: vdi.kasm.io/v1alpha1
kind: VDITemplate
metadata:
  name: ubuntu-desktop
spec:
  image: ghcr.io/selkies-project/selkies-gstreamer/gst-web:latest
  displayName: "Ubuntu 22.04 Desktop"
  description: "Full Ubuntu desktop with GPU acceleration"
  resources:
    defaultGPU: 1
    defaultMemory: 4Gi
    defaultCPU: 2
  applications:
    - name: Firefox
      icon: firefox.svg
    - name: VS Code
      icon: vscode.svg
```

**Operator Scaffolding**:
```bash
# Initialize with kubebuilder
kubebuilder init --domain kasm.io --repo github.com/user/vdi-operator
kubebuilder create api --group vdi --version v1alpha1 --kind VDISession
kubebuilder create api --group vdi --version v1alpha1 --kind VDITemplate
```

---

### Phase 3: Operator Logic Implementation (Week 3)

**Goal**: Implement reconciliation loops for session lifecycle

**VDISession Controller Logic**:

```go
func (r *VDISessionReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    session := &vdiv1alpha1.VDISession{}
    if err := r.Get(ctx, req.NamespacedName, session); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    // 1. Fetch the template
    template := &vdiv1alpha1.VDITemplate{}
    if err := r.Get(ctx, types.NamespacedName{Name: session.Spec.Template}, template); err != nil {
        return ctrl.Result{}, err
    }

    // 2. Create or update the Pod
    pod := r.buildPod(session, template)
    if err := controllerutil.SetControllerReference(session, pod, r.Scheme); err != nil {
        return ctrl.Result{}, err
    }
    if err := r.Create(ctx, pod); err != nil && !errors.IsAlreadyExists(err) {
        return ctrl.Result{}, err
    }

    // 3. Create Service and IngressRoute
    // ...

    // 4. Update status
    session.Status.Phase = "Running"
    session.Status.PodName = pod.Name
    session.Status.URL = fmt.Sprintf("https://%s.vdi.example.com", session.Spec.User)
    return ctrl.Result{RequeueAfter: 30 * time.Second}, r.Status().Update(ctx, session)
}
```

**Key Features**:
- [ ] Pod creation from template
- [ ] Automatic PVC provisioning
- [ ] Traefik IngressRoute generation
- [ ] Session timeout enforcement (via CronJob or controller)
- [ ] Graceful shutdown with finalizers

---

### Phase 4: Dashboard & API (Week 4)

**Goal**: User-facing interface for session management

**Components**:

1. **qlkube Middleware** (from CrownLabs)
   - Exposes K8s API as GraphQL
   - Enforces RBAC per user
   - Handles OIDC authentication

2. **React Dashboard**
   - List available templates
   - Launch/terminate sessions
   - Display session URL
   - Show resource usage

**API Examples**:
```graphql
# List user's sessions
query {
  vdiSessions(user: "alice@example.com") {
    name
    status { phase, url }
    spec { template, resources { gpu } }
  }
}

# Create new session
mutation {
  createVDISession(input: {
    user: "alice@example.com"
    template: "ubuntu-desktop"
  }) {
    name
    status { url }
  }
}
```

---

## 5. GPU Time-Slicing Configuration

### Cluster Setup (Prerequisites)

```yaml
# gpu-time-slicing-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: time-slicing-config
  namespace: gpu-operator
data:
  any: |-
    version: v1
    flags:
      migStrategy: none
    sharing:
      timeSlicing:
        renameByDefault: false
        failRequestsGreaterThanOne: false
        resources:
        - name: nvidia.com/gpu
          replicas: 8
```

### Apply to GPU Operator

```bash
# Patch the ClusterPolicy
kubectl patch clusterpolicy/cluster-policy \
  -n gpu-operator --type merge \
  -p '{"spec": {"devicePlugin": {"config": {"name": "time-slicing-config"}}}}'
```

### Verify

```bash
# Node should show 8x GPU capacity
kubectl describe node gpu-node | grep nvidia.com/gpu
# Expected: nvidia.com/gpu: 8
```

---

## 6. Success Metrics

| Metric | Phase 0 | Phase 4 |
|--------|---------|---------|
| Session startup time | <60s | <30s |
| Streaming latency | <50ms | <30ms |
| GPU utilization | >50% | >80% |
| Concurrent users per GPU | 2 | 8 |
| Dashboard login to desktop | N/A | <10s |

---

## 7. Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| NVENC encoder fails | Medium | Fallback to x264enc (CPU) |
| Time-slicing OOM | Medium | Set memory limits, monitor usage |
| WebRTC NAT issues | High | Deploy Coturn TURN server |
| Session leak on crash | Medium | Implement Pod finalizers |
| User data loss | Low | PVC with reclaim policy Retain |

---

## 8. File Structure

```
kasm-operator/
├── docs/
│   ├── PRD.md                    # This document
│   ├── research-prompts.md       # Research queries
│   └── kasm_vdi_on_kubernetes_research.md
├── manifests/
│   ├── phase-0/
│   │   └── selkies-test-pod.yaml
│   ├── phase-1/
│   │   ├── gpu-time-slicing-config.yaml
│   │   ├── selkies-deployment.yaml
│   │   └── coturn-deployment.yaml
│   └── phase-2/
│       ├── vdisession-crd.yaml
│       └── vditemplate-crd.yaml
├── operator/
│   ├── api/v1alpha1/
│   │   ├── vdisession_types.go
│   │   └── vditemplate_types.go
│   ├── controllers/
│   │   └── vdisession_controller.go
│   └── main.go
├── dashboard/
│   ├── src/
│   └── package.json
└── charts/
    └── vdi-operator/
        ├── Chart.yaml
        └── values.yaml
```

---

## 9. Next Steps (Immediate)

1. **Today**: Deploy Phase 0 test pod on K3s
2. **Verify**: GPU time-slicing works with Selkies
3. **Document**: Record latency and FPS metrics
4. **Commit**: Push manifests to git
5. **Week 1**: Scale to multi-user deployment

---

## Appendix A: Key Repositories

| Project | URL | License |
|---------|-----|---------|
| Selkies-GStreamer | https://github.com/selkies-project/selkies-gstreamer | MPL-2.0 |
| CrownLabs (reference) | https://github.com/netgroup-polito/CrownLabs | Apache-2.0 |
| NVIDIA GPU Operator | https://github.com/NVIDIA/gpu-operator | Apache-2.0 |
| Kubebuilder | https://github.com/kubernetes-sigs/kubebuilder | Apache-2.0 |
| Coturn | https://github.com/coturn/coturn | BSD-3 |
