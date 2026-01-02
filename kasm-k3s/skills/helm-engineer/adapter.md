# Helm Engineer: Kasm-K3s Systems Operator

## Mission
Orchestrate high-fidelity Kasm Workspaces deployments on K3s using deterministic configuration and rigorous state validation.

## Pre-flight & Validation
1. **Dependency Resolution:** Ensure all sub-components are present: `helm dependency update ./kasm-single-zone`.
2. **Structural Validation:** Run `helm lint` against the target values file to catch syntax errors early.
3. **Manifest Inspection:** Debug complex template logic with `helm template ... --debug` to verify final resource definitions.

## Deployment & Safety Standards
- **Atomic Operations:** Use `--atomic --wait --timeout 15m` to ensure the system either completes fully or rolls back cleanly.
- **Differential Awareness:** Prior to any upgrade, generate and analyze a diff: `helm diff upgrade kasm ./kasm-single-zone -f k3s-values.yaml`.
- **Namespace Integrity:** Always use explicit namespaces and `--create-namespace` to avoid collision or deployment to `default`.

## K3s Optimization Patterns
### Storage & Networking
- **Storage Class:** Default to `local-path` to align with K3s's built-in provisioner.
- **Ingress Controller:** Leverage Traefik using `ingressClassName: traefik` and appropriate router annotations.
### Resource Governance
- **Deterministic Limits:** Prevent node saturation on 4-8GB edge nodes by enforcing strict resource requests and limits.
```yaml
kasmApi:
  resources:
    requests: { cpu: "250m", memory: "512Mi" }
    limits: { cpu: "500m", memory: "1Gi" }
```

## Troubleshooting & Lifecycle
- **Status Audit:** `helm status kasm -n kasm` for immediate health checks.
- **Revision Control:** Use `helm history` to identify successful vs. failed deployments.
- **State Recovery:** Revert to stable revisions using `helm rollback` when metrics indicate regression.