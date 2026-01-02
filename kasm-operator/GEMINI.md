# Kasm Operator for K3s - VDI Platform

## 1. Project Overview
**Project Name:** Kasm Operator (VDI Platform for K3s)
**Goal:** Build a Kubernetes-native VDI platform combining Selkies-GStreamer WebRTC streaming, a custom Kubernetes Operator for session lifecycle, and NVIDIA GPU time-slicing for multi-tenant desktop delivery.
**Core Innovation:** "Validate First, Build Second" - Deploy working Selkies VDI immediately, then wrap with operator automation.

## 2. Current Workspace Status
**Type:** Design & Implementation Repository
**Status:** Phase 0-1 (Validation & Multi-User Deployment)
**Note:** Contains design documentation (PRD, ADD, TDD) and skill definitions. Manifests and operator code to be developed.

## 3. Key Documentation Files
*   **`docs/PRD.md` (Product Requirements Document):**
    *   Hybrid architecture combining Selkies-GStreamer + Custom Operator + GPU Time-Slicing
    *   4-phase implementation plan (Validation → Multi-User → Operator → Dashboard)
    *   Success metrics: <30s startup, <50ms latency, 8 users/GPU
*   **`docs/ADD.md` (Architecture Design Document):**
    *   Control Plane: Operator, qlkube, Dashboard
    *   Data Plane: Selkies session pods with GPU time-slices
    *   CRD definitions: VDISession, VDITemplate
*   **`docs/TDD.md` (Technical Design Document):**
    *   CRD schemas with OpenAPI validation
    *   Controller implementation in Go (kubebuilder)
    *   Traefik IngressRoute generation
    *   Coturn TURN server configuration

## 4. Directory Structure
```text
kasm-operator/
├── docs/                        # Project documentation
│   ├── PRD.md                   # Product requirements
│   ├── ADD.md                   # Architecture design
│   └── TDD.md                   # Technical design
├── skills/                      # Agent persona definitions
│   ├── k8s-operator-developer/  # Go/kubebuilder operator dev
│   ├── webrtc-engineer/         # Selkies/GStreamer streaming
│   ├── gpu-engineer/            # NVIDIA time-slicing
│   ├── dashboard-developer/     # React + qlkube UI
│   ├── devops-engineer/         # K3s deployment, Helm
│   ├── architect/               # System design
│   ├── qa-engineer/             # Testing strategies
│   ├── security-engineer/       # Platform hardening
│   └── product-manager/         # Requirements & roadmap
├── manifests/                   # Kubernetes manifests (TBD)
│   ├── phase-0/                 # Validation manifests
│   ├── phase-1/                 # Multi-user deployment
│   └── phase-2/                 # CRD definitions
├── operator/                    # Go operator code (TBD)
├── dashboard/                   # React dashboard (TBD)
└── charts/                      # Helm charts (TBD)
```

## 5. Technology Stack
| Layer | Technology | Purpose |
|-------|------------|---------|
| Streaming | Selkies-GStreamer | WebRTC, NVENC, lowest latency |
| GPU Sharing | NVIDIA Time-Slicing | 4-8x density |
| Orchestration | Kubernetes Operator (kubebuilder) | CRD-based session lifecycle |
| Ingress | Traefik + Coturn | WebSocket, TURN relay |
| Storage | local-path-provisioner | K3s native PVCs |
| Dashboard | React + qlkube | GraphQL to K8s API |

## 6. Key Constraints
- **Latency:** Video streaming < 50ms glass-to-glass
- **Density:** 4-8 concurrent sessions per GPU
- **Startup:** Session ready in < 30 seconds
- **Platform:** K3s on bare metal with NVIDIA GPU

## 7. Usage Guidelines
*   **For Context:** Refer to `docs/PRD.md` for requirements and phases
*   **For Architecture:** Use `docs/ADD.md` for system design
*   **For Implementation:** Use `docs/TDD.md` for controller code and CRD schemas
*   **For Skills:** Reference `skills/` for persona-specific patterns
