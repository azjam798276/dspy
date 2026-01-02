# Architecture Design Document (ADD)

## VDI Operator for K3s with GPU Time-Slicing

**Version**: 1.0.0 | **Date**: 2026-01-02 | **Status**: Draft

---

## 1. Overview

This document defines the architecture for a Kubernetes-native VDI platform combining:
- **Selkies-GStreamer** for WebRTC streaming
- **Kubernetes Operator** for session lifecycle
- **NVIDIA Time-Slicing** for GPU sharing

## 2. System Context

```
                    ┌─────────────────┐
                    │   End Users     │
                    │   (Browsers)    │
                    └────────┬────────┘
                             │ WebRTC (UDP)
                             ▼
┌────────────────────────────────────────────────────────────┐
│                      K3S CLUSTER                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Control Plane: Operator, Dashboard, qlkube          │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Data Plane: Selkies Session Pods (GPU Time-Sliced)  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Infra: Traefik, GPU Operator, local-path, Coturn    │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

## 3. Component Architecture

### 3.1 Control Plane

| Component | Purpose | Technology |
|-----------|---------|------------|
| VDI Operator | Session lifecycle management | Go + kubebuilder |
| qlkube | GraphQL API to K8s | Node.js |
| Dashboard | User interface | React |
| Coturn | TURN relay for NAT | C |

### 3.2 Data Plane (Session Pod)

```
┌─────────────────────────────────────────────┐
│              SELKIES POD                     │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐    │
│  │  X11    │─▶│ GStreamer│─▶│ WebRTC  │─▶UDP│
│  │ (Xvfb)  │  │ (NVENC)  │  │ Server  │    │
│  └─────────┘  └──────────┘  └─────────┘    │
│  ┌─────────┐  ┌──────────┐                  │
│  │ Desktop │  │  Apps    │                  │
│  │ (XFCE)  │  │(Firefox) │                  │
│  └─────────┘  └──────────┘                  │
│  Resources: nvidia.com/gpu: 1 (time-slice) │
│  Volumes: /home → PVC, /dev/shm → emptyDir │
└─────────────────────────────────────────────┘
```

## 4. Data Flows

### 4.1 Session Creation

```
User ──▶ Dashboard ──▶ qlkube ──▶ K8s API ──▶ Operator
                                                  │
                      ┌───────────────────────────┘
                      ▼
              Creates: Pod + PVC + IngressRoute
                      │
                      ▼
              Updates: VDISession.status.url
                      │
User ◀── Redirect ◀───┘
```

### 4.2 Streaming Pipeline

```
X11 Display ──▶ GStreamer Capture ──▶ NVENC H.264
                                          │
Browser ◀── WebRTC/UDP ◀── RTP Packetize ◀┘
```

## 5. Custom Resource Definitions

### 5.1 VDISession

```yaml
apiVersion: vdi.kasm.io/v1alpha1
kind: VDISession
spec:
  user: alice@example.com
  template: ubuntu-desktop
  resources:
    gpu: 1
    memory: 4Gi
status:
  phase: Running
  url: https://alice.vdi.example.com
```

### 5.2 VDITemplate

```yaml
apiVersion: vdi.kasm.io/v1alpha1
kind: VDITemplate
spec:
  image: ghcr.io/selkies-project/selkies-gstreamer/gst-web:latest
  displayName: Ubuntu Desktop
  resources:
    defaultGPU: 1
    defaultMemory: 4Gi
```

## 6. Deployment Topology

### Single Node (Dev)

| Resource | Allocation |
|----------|------------|
| CPU | 8+ cores |
| RAM | 32GB+ |
| GPU | 1x NVIDIA (8 time-slices) |
| Sessions | Up to 8 concurrent |

### Multi-Node (Prod)

- **Control Node**: Operator, Dashboard (no GPU)
- **Worker Nodes**: Session Pods (GPU, tainted)

## 7. Security Model

| Layer | Mechanism |
|-------|-----------|
| User Auth | OIDC via Keycloak |
| API Auth | Bearer tokens + RBAC |
| Session Auth | Basic Auth / OIDC passthrough |
| Network | NetworkPolicy isolation |
| Pod Security | Non-root, read-only rootfs |

## 8. Quality Attributes

| Attribute | Target |
|-----------|--------|
| Session startup | < 30s |
| Streaming latency | < 50ms |
| Frame rate | 60 FPS @ 1080p |
| Concurrent users/GPU | 8 |

## 9. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Streaming | Selkies-GStreamer | Lowest latency (WebRTC) |
| Operator Framework | kubebuilder | K8s standard |
| API Gateway | qlkube | Proven in CrownLabs |
| GPU Sharing | Time-Slicing | Better than MIG for VDI |

## 10. Risks

| Risk | Mitigation |
|------|------------|
| NVENC unavailable | Fallback to CPU encoding |
| NAT traversal fails | Deploy Coturn TURN server |
| GPU OOM | Strict memory limits |
| Session leak | Pod finalizers |
