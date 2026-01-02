---
id: "20260102_default_deny_networkpolicy"
difficulty: "easy"
tags: ["security", "network-policy", "kubernetes", "kasm", "zero-trust"]
tech_stack: "Kubernetes, K3s, NetworkPolicy"
---

# User Story
As a security engineer, I want to create a default-deny NetworkPolicy for the Kasm namespace that blocks all ingress and egress traffic while explicitly allowing DNS resolution to CoreDNS.

# Context & Constraints
Implement zero-trust networking for Kasm Workspaces:

**Requirements:**
- Block ALL ingress traffic by default (empty ingress rules)
- Block ALL egress traffic by default
- Explicitly allow DNS egress to CoreDNS (UDP/TCP port 53)
- Use label selectors for CoreDNS pods in kube-system namespace

**K3s-Specific:**
- CoreDNS uses label `k8s-app=kube-dns` or `k8s-app=coredns`
- K3s default service CIDR is `10.43.0.0/16`
- Must specify both UDP and TCP for DNS

# Acceptance Criteria
- [ ] Create NetworkPolicy with `policyTypes: [Ingress, Egress]`
- [ ] Empty `ingress: []` for default deny
- [ ] Egress rule allowing DNS to kube-system namespace
- [ ] DNS rule includes both UDP and TCP port 53
- [ ] Use namespaceSelector and podSelector for CoreDNS
