# Perplexity AI Prompts for Kasm K3s Golden Examples

Copy and paste these prompts into Perplexity AI (or similar tools) to find high-quality, verified examples from GitHub and StackOverflow.

---

## 1. Helm Configuration (K3s Optimized)
**Goal:** Find real-world `values.yaml` configurations for running Kasm on K3s/smaller clusters.

**Prompt:**
```text
Find GitHub repositories or Gists containing "kasm-helm" values.yaml configurations specifically tuned for K3s or single-node Kubernetes clusters. 
I need "golden examples" of:
1. `k3s` specific overrides (storageClass: local-path).
2. Resource limits (cpu/memory) optimized for 4GB/8GB nodes.
3. Configuration for disabling the internal LoadBalancer in favor of an existing Ingress controller.

Search queries: 
- "site:github.com kasm helm values.yaml k3s"
- "site:github.com kasm-helm traefik ingress"
- "kasm workspaces helm chart resource limits for small cluster"

Output format: Please provide raw YAML snippets and links to the specific GitHub files.
```

## 2. Troubleshooting Init Containers
**Goal:** Find real error logs and solutions for `Init:1/5` (wait-for-db) failures.

**Prompt:**
```text
Search StackOverflow, Reddit (r/kasmweb, r/kubernetes), and GitHub Issues for Kasm Workspaces deployments stuck in "Init:1/5" or "Init:Create/Wait".
I need detailed examples of:
1. `kubectl describe pod` output showing the specific failing init container event.
2. `kubectl logs` output for "wait-for-db" or "wait-for-redis" containers.
3. Solutions related to "local-path-provisioner" permission issues or PVC binding/pending states in K3s.

Search queries:
- "kasm workspaces kubernetes init:1/5 stuck"
- "kasm proxy pod wait-for-db connection refused"
- "k3s local-path-provisioner permission denied postgres"

Output format: Provide the error message, the root cause (e.g., "DNS resolution failed"), and the verified fix command details.
```

## 3. Traefik Ingress & TLS
**Goal:** Find verified Ingress configurations for Traefik v2 + cert-manager + WebSockets.

**Prompt:**
```text
Find working Kubernetes `Ingress` (apiVersion: networking.k8s.io/v1) examples for Kasm Workspaces that specifically work with Traefik v2 and cert-manager.
I need "golden examples" that demonstrate:
1. The exact `traefik.ingress.kubernetes.io` annotations required for WebSocket headers (Connection: Upgrade).
2. Configuration for "sticky sessions" (affinity) which is required for Kasm's API.
3. A `Middleware` resource for HTTP-to-HTTPS redirection.

Search queries:
- "site:github.com kasm ingress traefik websocket"
- "k8s ingress sticky session annotation traefik kasm"
- "kasm workspaces traefik middleware redirect scheme"

Output format: Provide the complete YAML manifest for the Ingress and Middleware resources.
```

## 4. Security & Network Policies
**Goal:** Find restrictive NetworkPolicy examples for isolating Kasm databases.

**Prompt:**
```text
Find examples of Kubernetes `NetworkPolicy` manifests used to harden Kasm Workspaces deployments.
I need examples that:
1. Deny all ingress traffic by default in the namespace.
2. Explicitly allow the Kasm API and Manager pods to talk to PostgreSQL (port 5432) and Redis (port 6379).
3. Block direct external access to the database pods.

Search queries:
- "site:github.com kasm networkpolicy postgres"
- "kubernetes networkpolicy isolate database namespace"
- "calico networkpolicy deny-default example yaml"

Output format: Provide the YAML for a "Default Deny" policy and a "Allow DB Access" policy.
```
