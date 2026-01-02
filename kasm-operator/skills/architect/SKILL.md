---
name: architect
description: System Architect for VDI Platform Design and Integration
---

# VDI Platform Architecture: Design Patterns and Governance

## Architectural Integrity
1. **Control Plane / Data Plane Separation:** Operator and Dashboard run independently from session pods.
2. **Declarative State:** All session state flows through CRDs; no imperative side channels.
3. **Loose Coupling:** Components communicate via well-defined APIs (K8s API, GraphQL).
4. **Failure Isolation:** Session pod failures must not cascade to operator or other sessions.

## System Context
```
┌─────────────────────────────────────────────────────────────┐
│                        K3s Cluster                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Control Plane                                            ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   ││
│  │  │ VDI Operator │  │   qlkube     │  │  Dashboard   │   ││
│  │  │  (Go)        │  │  (GraphQL)   │  │   (React)    │   ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘   ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Data Plane (GPU Nodes)                                   ││
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐           ││
│  │  │ Session 1 │  │ Session 2 │  │ Session N │  ...      ││
│  │  │ (Selkies) │  │ (Selkies) │  │ (Selkies) │           ││
│  │  └───────────┘  └───────────┘  └───────────┘           ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Infrastructure                                           ││
│  │  Traefik │ Coturn │ GPU Operator │ local-path-provisioner││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Streaming | Selkies-GStreamer | Lowest latency (WebRTC), NVENC support |
| GPU Sharing | Time-Slicing | 4-8x density, simpler than MIG |
| API | CRDs + GraphQL | Kubernetes-native, developer-friendly |
| Ingress | Traefik | WebSocket support, dynamic routing |
| Storage | local-path | K3s native, sufficient for POC |

## Data Flow Patterns

### Session Creation
```
User → Dashboard → qlkube → K8s API → Operator
                                         │
         ┌───────────────────────────────┘
         ▼
   Create: Pod + PVC + Service + IngressRoute
         │
         ▼
   Update: VDISession.status.url
         │
User ◀── Redirect to session URL
```

### Streaming Pipeline
```
X11 → GStreamer → NVENC → RTP → WebRTC → Browser
                                    ↑
                              TURN (if needed)
```

## Interface Contracts

### VDISession CRD
- **spec.user**: Owner identity (email/OIDC subject)
- **spec.template**: Reference to VDITemplate
- **spec.resources**: Resource requests (GPU, memory, CPU)
- **spec.timeout**: Auto-terminate duration
- **status.phase**: Lifecycle state machine
- **status.url**: Connection endpoint

### VDITemplate CRD
- **spec.image**: Container image for sessions
- **spec.displayName**: Human-readable name
- **spec.resources**: Default resource allocation

## Quality Attributes
| Attribute | Target | Measurement |
|-----------|--------|-------------|
| Latency | < 50ms video | WebRTC stats |
| Startup | < 30s | CRD creation to Running |
| Density | 8 sessions/GPU | Concurrent count |
| Availability | 99.5% | Session uptime |

## Security Architecture
- **Authentication:** OIDC via Keycloak → Dashboard → qlkube
- **Authorization:** RBAC binding users to namespaces
- **Isolation:** NetworkPolicy per session, PodSecurityPolicy
- **Secrets:** External secrets, never in CRD spec

## Risk Register
| Risk | Impact | Mitigation |
|------|--------|------------|
| NVENC fails | Degraded UX | CPU fallback encoder |
| GPU OOM | Session crash | Memory limits, monitoring |
| NAT issues | Connection fail | Mandatory TURN server |
| Session leak | Resource waste | Finalizers, timeout CronJob |

## Evolution Roadmap
1. **Phase 1:** Manual manifests, single GPU node
2. **Phase 2:** Operator + CRDs, multi-session
3. **Phase 3:** Dashboard + auth, self-service
4. **Phase 4:** Multi-node, auto-scaling
