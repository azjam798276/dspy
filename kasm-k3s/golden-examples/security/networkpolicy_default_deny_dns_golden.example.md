---
id: "networkpolicy_default_deny_dns"
source: "https://github.com/Klavis-AI/klavis"
tags: ["security", "networkpolicy", "k3s", "zero-trust"]
---

## Problem
Configure a zero-trust NetworkPolicy for Kasm Workspaces on K3s that blocks all pod traffic by default while explicitly allowing DNS resolution to CoreDNS. The policy must prevent lateral movement between pods while ensuring applications can still resolve hostnames.

## Solution
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kasm-default-deny-with-dns
  namespace: kasm
  annotations:
    policy.kubernetes.io/description: "Default deny all traffic with explicit DNS allowlist"
spec:
  podSelector:
    matchLabels:
      app: kasm-workspace
  policyTypes:
    - Ingress
    - Egress
  
  # Deny all ingress by default (no rules = deny all)
  ingress: []
  
  # Explicit egress allowlist
  egress:
    # CRITICAL: Allow DNS resolution (CoreDNS for K3s)
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    
    # Alternative: CoreDNS label selector
    - to:
        - namespaceSelector:
            matchLabels:
              name: kube-system
          podSelector:
            matchLabels:
              k8s-app: coredns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    
    # CRITICAL: Kubernetes API server access (K3s default service CIDR)
    - to:
        - ipBlock:
            cidr: 10.43.0.0/16  # K3s default service CIDR
      ports:
        - protocol: TCP
          port: 443
```

## Key Techniques
- Zero-trust networking (default deny all)
- Explicit DNS allowlist for CoreDNS (UDP/TCP 53)
- Label selectors instead of IP addresses
- K3s-specific service CIDR (10.43.0.0/16)
- Both kube-dns and coredns labels for compatibility
