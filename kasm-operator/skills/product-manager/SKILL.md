---
name: product-manager
description: Product Manager for VDI Platform Requirements and Roadmap
---

# Product Management: VDI Platform Strategy and Requirements

## Vision Statement
Deliver a Kubernetes-native VDI platform that enables organizations to provide GPU-accelerated cloud desktops with enterprise-grade security and sub-50ms latency.

## Target Users
1. **End Users:** Knowledge workers needing GPU workstations (CAD, ML, video editing)
2. **IT Admins:** Managing desktop fleets via Kubernetes-native tools
3. **DevOps Engineers:** Deploying and scaling the platform

## Core Value Propositions
| Stakeholder | Value |
|-------------|-------|
| End Users | Low-latency, GPU-powered desktops from anywhere |
| IT Admins | Self-service, centralized management, usage visibility |
| Finance | 4-8x GPU density vs dedicated machines, pay-per-use |

## Success Metrics
| Metric | Phase 0 | Phase 4 |
|--------|---------|---------|
| Session startup | < 60s | < 30s |
| Video latency | < 50ms | < 30ms |
| GPU utilization | > 50% | > 80% |
| Users per GPU | 2 | 8 |
| Dashboard to desktop | N/A | < 10s |

## Feature Roadmap

### Phase 0: Validation (Day 1-2)
- [ ] Single Selkies pod with GPU time-slice
- [ ] WebRTC streaming verified < 50ms
- [ ] NVENC encoding confirmed
- [ ] Multi-pod GPU sharing tested

### Phase 1: Multi-User (Week 1)
- [ ] 4-8 concurrent sessions
- [ ] Traefik routing per user
- [ ] Coturn TURN server deployed
- [ ] PVC persistence per session

### Phase 2: Operator (Week 2)
- [ ] VDISession CRD defined
- [ ] VDITemplate CRD defined
- [ ] Kubebuilder scaffolding
- [ ] Basic reconciliation loop

### Phase 3: Automation (Week 3)
- [ ] Full session lifecycle management
- [ ] Automatic Ingress creation
- [ ] Session timeout enforcement
- [ ] Finalizer-based cleanup

### Phase 4: Dashboard (Week 4)
- [ ] React dashboard deployed
- [ ] qlkube GraphQL gateway
- [ ] OIDC authentication
- [ ] Real-time session status

## User Stories

### US-001: Launch Desktop Session
```
As an end user
I want to launch a cloud desktop from a web browser
So that I can access GPU-accelerated applications remotely

Acceptance Criteria:
- User can select from available templates
- Session starts within 30 seconds
- WebRTC stream connects automatically
- Session URL is unique to user
```

### US-002: Terminate Session
```
As an end user
I want to terminate my desktop session
So that resources are freed when I'm done

Acceptance Criteria:
- Terminate button in dashboard
- Confirmation dialog
- Session resources cleaned up within 10s
- User data persisted in PVC
```

### US-003: Session Timeout
```
As an IT admin
I want sessions to auto-terminate after inactivity
So that GPU resources are not wasted

Acceptance Criteria:
- Configurable timeout per template
- Warning notification before termination
- Graceful shutdown with state save
```

### US-004: Resource Quotas
```
As an IT admin
I want to limit sessions per user
So that resources are fairly distributed

Acceptance Criteria:
- Max sessions per user configurable
- Clear error message when limit exceeded
- Admin override capability
```

## Competitive Analysis
| Feature | Kasm (Commercial) | Our Platform |
|---------|-------------------|--------------|
| Streaming | Proprietary | Selkies (OSS) |
| GPU Support | Yes | Yes (time-slicing) |
| K8s Native | No | Yes (CRDs) |
| Pricing | Per-seat license | Self-hosted |

## Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| NVENC limits | Medium | High | Use professional GPUs |
| NAT traversal | High | Medium | Mandatory TURN |
| GPU OOM | Medium | High | Memory limits |
| Adoption | Low | High | Phased rollout |

## Go/No-Go Criteria (Phase 0)
- [ ] GPU time-slicing verified on K3s
- [ ] WebRTC latency < 50ms measured
- [ ] 4+ concurrent sessions stable
- [ ] NVENC encoder functional
