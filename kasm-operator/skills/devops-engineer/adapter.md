# DevOps Engineering: Kasm VDI Operator Platform (K3s)

## Core Mandates
1. **Validate First:** Prioritize manual verification of the Selkies-GStreamer data plane (streaming performance, audio/video sync) before implementing operator automation.
2. **High-Density GPU:** Enforce NVIDIA Time-Slicing (8 replicas per physical GPU) via `gpu-operator` ConfigMaps to maximize resource utilization (`nvidia.com/gpu: 1` per session).
3. **Low-Latency WebRTC:** Architecture connectivity via host-networked Coturn and Traefik `IngressRoute` resources to minimize network hops and ensure stable UDP streams.

## Configuration & Standards
- **K3s Setup:** Deploy with `--disable=traefik` to allow custom IngressRoute management. Use `local-path-provisioner` with node affinity for performant, persistent user home directories.
- **Helm Strategy:** Structure the Operator chart to manage `VDISession` lifecycles. Ensure Pod templates inject `SELKIES_ENCODER=nvh264enc` and mount `/dev/shm` (EmptyDir) for browser acceleration.
- **Security:** Implement "Zero Trust" networking. Apply Default-Deny NetworkPolicies; explicitly allow only Traefik (8080) and Coturn (3478) traffic to session pods.

## Observability & SLOs
- **Startup:** < 30s session availability (Pending -> Running).
- **Latency:** < 50ms glass-to-glass latency.
- **Utilization:** > 80% aggregate GPU load via DCGM monitoring.