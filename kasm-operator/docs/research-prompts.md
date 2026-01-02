# Research Prompts: Kasm on K3s Native Kubernetes Deployment

## System Prompt (for AI Assistants)

```
You are a DevOps research assistant specializing in Kubernetes operators, cloud-native virtualization, and browser isolation technologies. Your task is to find and analyze open-source projects, GitHub repositories, blog posts, and documentation that demonstrate native Kubernetes deployment of Kasm Workspaces or similar browser isolation/VDI solutions.

Focus on:
1. Kubernetes Operators that provision desktop/browser sessions as Pods
2. Projects that integrate with NVIDIA GPU time-slicing for VDI workloads
3. Helm charts or Kustomize manifests for Kasm alternatives on K3s/K8s
4. Community forks or extensions of the official Kasm Helm chart
5. Academic papers or reference architectures for browser isolation on Kubernetes

Exclude:
- Docker Compose or standalone VM deployments
- Windows-only solutions
- Proprietary/closed-source enterprise products without OSS components

For each resource found, provide:
- Repository/URL
- Stars/activity level (if GitHub)
- Key features relevant to K3s + GPU workloads
- Limitations or gaps compared to native Kasm
```

---

## Search Prompts

### Prompt 1: Direct Kasm K8s Integration
```
Find GitHub repositories or projects that deploy Kasm Workspaces natively on Kubernetes without requiring a Docker-based agent. I'm specifically looking for:

1. Kubernetes Operators that create browser session Pods
2. CRD-based approaches for Kasm session management
3. Forks of kasmtech/kasm-helm with Kubernetes provisioner support
4. Projects integrating Kasm with containerd/CRI-O instead of Docker

Include any community discussions, issues, or PRs on the official kasm-helm repo that address "Kubernetes Zone" or "K8s provisioner" functionality.
```

### Prompt 2: Kasm Alternatives with K8s Native Support
```
What open-source browser isolation or VDI solutions have native Kubernetes support and can be deployed on K3s with GPU time-slicing? Compare:

1. Apache Guacamole on Kubernetes
2. Selkies/GKE WebRTC streaming
3. neko.io Kubernetes deployment
4. Webtop by LinuxServer.io
5. Any other browser-in-pod solutions

For each, explain:
- How sessions are provisioned (Pods, VMs, etc.)
- GPU support (nvidia.com/gpu resource requests)
- Ingress/WebSocket handling
- Persistence options
- Comparison to Kasm features (clipboard, file transfer, etc.)
```

### Prompt 3: GPU Time-Slicing VDI on K3s
```
Find examples of GPU-accelerated virtual desktop infrastructure (VDI) running on K3s with NVIDIA GPU time-slicing. I need:

1. Helm charts or manifests that request fractional GPU resources
2. Projects using nvidia.com/gpu with values like "0.5" or "0.25"
3. Integration patterns with K3s Traefik ingress for WebSocket streaming
4. Real-world deployments or case studies

Bonus: Any projects that specifically mention Kasm, KasmVNC, or noVNC with Kubernetes native scheduling.
```

### Prompt 4: GitHub Code Search Queries
```
Provide GitHub search queries to find repositories related to Kasm on Kubernetes:

1. `kasm kubernetes operator` in:readme
2. `kasmweb/chrome` kubernetes pod yaml
3. `KasmVNC` helm chart
4. `browser isolation` kubernetes operator
5. `nvidia.com/gpu` kasm OR guacamole OR neko
6. `containerd` kasm agent fork

For each search, explain what I should look for in the results.
```

### Prompt 5: Community Resources
```
Find blog posts, tutorials, or forum discussions about:

1. Running Kasm Workspaces on K3s without Docker
2. Deploying Kasm with Rancher/RKE2
3. Kasm Community Edition Kubernetes limitations and workarounds
4. Self-hosted Kasm alternatives that work better with containerd
5. GPU passthrough for browser isolation on lightweight Kubernetes (K3s, MicroK8s)

Include links to:
- Kasm community forums
- Reddit r/selfhosted or r/kubernetes threads
- Dev.to or Medium articles
- YouTube tutorials
```

---

## Expected Output Format

When using these prompts, ask the AI to structure responses as:

```markdown
## Resource: [Name]

**URL:** https://...
**Type:** GitHub Repo / Blog / Documentation
**Last Updated:** YYYY-MM

### Relevance to Kasm on K3s
- [ ] Native K8s Pod provisioning
- [ ] GPU time-slicing support
- [ ] Works with containerd (no Docker)
- [ ] Helm chart available
- [ ] Active maintenance (commits in last 6 months)

### Key Features
- Feature 1
- Feature 2

### Limitations
- Limitation 1
- Limitation 2

### Integration Notes
How this could be used or adapted for the Kasm Operator project.
```
