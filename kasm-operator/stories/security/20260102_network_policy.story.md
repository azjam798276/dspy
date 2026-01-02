---
id: "20260102_network_policy"
difficulty: "medium"
tags: ["security", "networkpolicy", "kubernetes", "isolation"]
tech_stack: "Kubernetes NetworkPolicy, Calico/Cilium"
---

# User Story
As a security engineer, I want NetworkPolicies isolating VDI sessions, so compromised sessions cannot attack other pods or internal services.

# Context & Constraints
**Session Isolation Policy:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: vdi-session-isolation
  namespace: vdi
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: vdi-session
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: traefik-system
      ports:
        - port: 8080
          protocol: TCP
  egress:
    # Allow DNS
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - port: 53
          protocol: UDP
    # Allow internet (for user applications)
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
```

**Operator Policy:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: vdi-operator
  namespace: vdi-operator
spec:
  podSelector:
    matchLabels:
      app: vdi-operator
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: monitoring
      ports:
        - port: 8080  # metrics
```

# Acceptance Criteria
- [ ] **Session Ingress:** Only Traefik can reach session pods
- [ ] **Session Egress:** Block internal networks, allow internet
- [ ] **DNS:** Allow DNS resolution
- [ ] **Operator:** Only monitoring can scrape metrics
- [ ] **Default Deny:** Default deny policy for vdi namespace
- [ ] **Test:** Verify policies with network test pods
