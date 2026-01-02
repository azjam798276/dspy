# DevOps Engineering: Kasm VDI Operator Platform (K3s)

## Core Principles
1. **Validation-Driven Infrastructure:** Validate the Selkies-GStreamer data plane (WebRTC streaming) manually before implementing operator automation.
2. **GPU Density Optimization:** Enforce NVIDIA Time-Slicing to achieve the target of 8 users per physical GPU.
3. **WebRTC Connectivity Stability:** Prioritize low-latency paths via host-networked Coturn and Traefik IngressRoutes with dynamic subdomain routing.
4. **Persistent State Management:** Utilize K3s `local-path-provisioner` with node affinity for high-performance user home directory storage.

## K3s & GPU Configuration
```bash
# 1. K3s Installation (GPU Optimized)
curl -sfL https://get.k3s.io | sh -s - --disable=traefik --write-kubeconfig-mode 644

# 2. NVIDIA Time-Slicing Setup (8x Density)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: time-slicing-config
  namespace: gpu-operator
data:
  any: |
    version: v1
    sharing:
      timeSlicing:
        resources:
        - name: nvidia.com/gpu
          replicas: 8
EOF

# 3. Patch ClusterPolicy for GPU Operator
kubectl patch clusterpolicy/cluster-policy -n gpu-operator --type merge \
  -p '{"spec":{"devicePlugin":{"config":{"name":"time-slicing-config"}}}}'
```

## Helm Chart Strategy
- **Operator Chart:** Manages lifecycle of `VDISession` and `VDITemplate` CRDs and the Go-based controller.
- **VDI Pod Templates:** Must specify:
  - `nvidia.com/gpu: 1` (mapped to time-sliced replicas).
  - `/dev/shm` volume (EmptyDir/Memory) for browser acceleration.
  - `SELKIES_ENCODER=nvh264enc` environment variable for hardware encoding.

## Dynamic Networking (Traefik)
```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: vdi-dynamic-ingress
spec:
  entryPoints: [websecure]
  routes:
  - match: HostRegexp(`{user:[a-z0-9-]+}.vdi.example.com`)
    kind: Rule
    services:
    - name: vdi-session-service
      port: 8080
  tls:
    certResolver: letsencrypt
    domains: [{ main: "*.vdi.example.com" }]
```

## Observability & SLOs
| Metric | Target (SLO) | Tooling |
|--------|--------------|---------|
| Session Startup Ready | < 30 seconds | Prometheus Exporter |
| Glass-to-Glass Latency | < 50ms | GStreamer Trace Logs |
| GPU Utilization | > 80% (Aggregated) | NVIDIA DCGM Exporter |

## Security Hardening
- **NetworkPolicy:** Default-deny ingress; allow only Traefik -> Session Pod (8080) and Session Pod -> Coturn (3478).
- **RBAC:** Least-privilege ServiceAccount for the operator, restricted to the `vdi-sessions` namespace.