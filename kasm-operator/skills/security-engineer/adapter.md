# Security Engineering: VDI Platform Hardening

## Core Principles
1. **Zero Trust Architecture:** Never trust, always verify. Every request between users, the dashboard, and the Kubernetes API must be authenticated via OIDC and authorized via RBAC.
2. **Strict Least Privilege:** Both the VDI Operator and individual session pods must operate with the absolute minimum set of permissions. Use namespace isolation and specific resource names where possible.
3. **Hardware-Level Isolation:** Leverage NVIDIA GPU time-slicing and strict memory limits to prevent cross-session resource exhaustion or side-channel attacks.
4. **Secure by Default Lifecycle:** From image scanning to session auto-termination (finalizers), security is baked into the entire lifecycle of a `VDISession`.

## Authentication & Authorization Flow
Implement a secure "Impersonation" flow for the dashboard to interact with the K8s API:
```
User (Browser) → Keycloak (MFA) → Dashboard (OIDC Token)
                                       │
                                       ▼
                               qlkube (Verifies Token)
                                       │
                                       ▼
                               K8s API (User Impersonation)
```
- **Constraint:** Dashboard must never use a high-privilege ServiceAccount to perform actions on behalf of users. Use `qlkube` to translate OIDC identities to K8s User identities.

## RBAC Configuration
### Operator Permissions (Minimal)
The operator requires `patch` permissions for status updates and finalizer management (`vdi.kasm.io/session-cleanup`).
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: vdi-operator
rules:
  - apiGroups: ["vdi.kasm.io"]
    resources: ["vdisessions", "vditemplates"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["pods", "services", "persistentvolumeclaims"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["traefik.io"]
    resources: ["ingressroutes"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

### User Session Control
Users should only be able to view and manage their own sessions.
- **Enforcement:** Use an Admission Webhook or `qlkube` filters to ensure `VDISession.spec.user` matches the authenticated OIDC sub.

## Pod Security Standards
Sessions must adhere to the Restricted Pod Security Standard:
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop: ["ALL"]
    add: ["SYS_PTRACE"] # Only if required for specific desktop apps
```
- **GPU Security:** Ensure `nvidia.com/gpu: 1` is strictly enforced via limits to prevent OOM in time-sliced environments.

## Network Isolation (Multi-Tenant)
Prevent lateral movement between sessions and access to cluster internals.
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: session-isolation
  namespace: vdi
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: vdi-session
  policyTypes: ["Ingress", "Egress"]
  ingress:
    - from:
        - namespaceSelector: { matchLabels: { name: "traefik" } }
      ports:
        - port: 8080
  egress:
    - to: [{ ipBlock: { cidr: "0.0.0.0/0", except: ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"] } }]
    - to: # Allow DNS
        - namespaceSelector: { matchLabels: { name: "kube-system" } }
      ports: [{ port: 53, protocol: "UDP" }, { port: 53, protocol: "TCP" }]
    - to: # Allow TURN/STUN for WebRTC
        - podSelector: { matchLabels: { app: "coturn" } }
      ports: [{ port: 3478 }]
```

## Secrets & Data Plane Security
- **Dynamic Credentials:** `SELKIES_BASIC_AUTH_PASSWORD` must be unique per session and never stored in cleartext in the `VDISession` object.
- **TLS 1.3:** Enforce TLS 1.3 for all Traefik `IngressRoute` objects using `TLSOption`.
- **Image Trust:** Only allow images from signed/trusted registries. Implement `ImagePolicyWebhook` if possible.

## Threat Model & Mitigation
| Threat | Mitigation |
|--------|------------|
| GPU Resource Exhaustion | Enforce `nvidia.com/gpu` replicas limits (Max 8 per physical GPU). |
| Data Exfiltration | Disable clipboard/drive sharing in `VDITemplate` properties. |
| Ingress Spoofing | Use `Host(`{user}.vdi.example.com`)` with sanitized usernames in IngressRoutes. |
| Stale Sessions | Implement auto-termination logic using `VDISession.spec.timeout`. |

## Compliance Checklist
- [ ] Operator RBAC contains no wildcard `*` permissions.
- [ ] `VDITemplate` changes are audited via K8s Audit Policy.
- [ ] NetworkPolicy blocks access to Cloud Metadata APIs (169.254.169.254).
- [ ] Persistent volumes use encrypted storage classes (where supported by `local-path`).
- [ ] Coturn server is host-networked but restricted via firewall to UDP 3478 and 49152-65535.

## Demonstrations

### Example 1
**Problem:**
Configure a zero-trust NetworkPolicy for Kasm Workspaces on K3s that blocks all pod traffic by default while explicitly allowing DNS resolution to CoreDNS. The policy must prevent lateral movement between pods while ensuring applications can still resolve hostnames.

**Solution:**
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

---

### Example 2
**Problem:**
Enable secrets encryption at rest for K3s to protect sensitive data stored in the database (etcd/SQLite). Implement a custom encryption configuration with AES-CBC, support for key rotation, and verification that secrets are properly encrypted.

**Solution:**
```bash
#!/bin/bash
# K3s Secrets Encryption Setup Script
set -euo pipefail

ENCRYPTION_CONFIG="/etc/k3s/encryption-config.yaml"
K3S_CONFIG="/etc/rancher/k3s/config.yaml"

# Generate cryptographically secure 32-byte key
generate_key() {
    head -c 32 /dev/urandom | base64
}

# Create encryption configuration
create_encryption_config() {
    local key1=$(generate_key)
    local key2=$(generate_key)
    
    sudo mkdir -p /etc/k3s
    cat <<EOF | sudo tee "$ENCRYPTION_CONFIG"
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
      - configmaps  # Optional: also encrypt ConfigMaps
    providers:
      # PRIMARY: AES-CBC encryption
      - aescbc:
          keys:
            - name: aescbc-key-1
              secret: ${key1}
      
      # FALLBACK: Identity (unencrypted) for migration
      - identity: {}
EOF
    
    echo "[INFO] Encryption config created at $ENCRYPTION_CONFIG"
    echo "[INFO] PRIMARY KEY: aescbc-key-1"
}

# Configure K3s to use encryption
configure_k3s() {
    sudo mkdir -p /etc/rancher/k3s
    cat <<EOF | sudo tee "$K3S_CONFIG"
secrets-encryption: true
kube-apiserver-arg:
  - "encryption-provider-config=${ENCRYPTION_CONFIG}"
EOF
    
    echo "[INFO] K3s config updated at $K3S_CONFIG"
}

# Install K3s with encryption enabled (fresh install)
install_k3s_encrypted() {
    curl -sfL https://get.k3s.io | \
      INSTALL_K3S_VERSION="v1.28.5+k3s1" \
      K3S_KUBECONFIG_MODE="644" \
      INSTALL_K3S_EXEC="--secrets-encryption" \
      sh -
}

# Verify secrets are encrypted
verify_encryption() {
    # Check encryption status
    sudo k3s secrets-encrypt status
    
    # Create test secret
    kubectl create secret generic test-encryption --from-literal=password=testpass123 --dry-run=client -o yaml | kubectl apply -f -
    
    # Verify in database (K3s uses SQLite by default)
    echo "[INFO] Checking database for encrypted secret..."
    local encrypted=$(sudo sqlite3 /var/lib/rancher/k3s/server/db/state.db \
      "SELECT value FROM kine WHERE name LIKE '%/secrets/default/test-encryption';" 2>/dev/null || echo "")
    
    if echo "$encrypted" | grep -q "k8s:enc:aescbc:v1"; then
        echo "[SUCCESS] Secret is encrypted with AES-CBC"
    else
        echo "[WARNING] Secret may not be encrypted - verify manually"
    fi
    
    # Cleanup
    kubectl delete secret test-encryption --ignore-not-found
}

# Key rotation (zero downtime)
rotate_keys() {
    echo "[INFO] Starting key rotation..."
    
    # Stage 1: Prepare new key
    sudo k3s secrets-encrypt prepare
    
    # Stage 2: Re-encrypt all secrets with new key
    sudo k3s secrets-encrypt rotate
    
    # Stage 3: Complete rotation (remove old key)
    sudo k3s secrets-encrypt reencrypt
    
    echo "[SUCCESS] Key rotation complete"
}

# Main
case "${1:-setup}" in
    setup)
        create_encryption_config
        configure_k3s
        echo "[INFO] Restart K3s to apply: sudo systemctl restart k3s"
        ;;
    install)
        install_k3s_encrypted
        ;;
    verify)
        verify_encryption
        ;;
    rotate)
        rotate_keys
        ;;
    *)
        echo "Usage: $0 {setup|install|verify|rotate}"
        exit 1
        ;;
esac
```

---

### Example 3
**Problem:**
Configure Traefik IngressRoute on K3s with automatic TLS certificate provisioning via cert-manager and Let's Encrypt. The setup must include security headers middleware, rate limiting, and HTTP to HTTPS redirection for Kasm Workspaces.

**Solution:**
```yaml
# 1. ClusterIssuer for Let's Encrypt
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
  namespace: cert-manager
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
    - http01:
        ingress:
          class: traefik

---
# 2. Certificate resource (auto-creates TLS Secret)
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: kasm-tls-cert
  namespace: kasm
spec:
  secretName: kasm-tls-cert
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - kasm.example.com
  usages:
    - digital signature
    - key encipherment
  renewBefore: 720h  # 30 days before expiry

---
# 3. Security Headers Middleware
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: security-headers
  namespace: kasm
spec:
  headers:
    customResponseHeaders:
      X-Frame-Options: "SAMEORIGIN"
      X-Content-Type-Options: "nosniff"
      X-XSS-Protection: "1; mode=block"
      Referrer-Policy: "strict-origin-when-cross-origin"
      Strict-Transport-Security: "max-age=31536000; includeSubDomains"
      Content-Security-Policy: "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

---
# 4. Rate Limiting Middleware
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: rate-limit
  namespace: kasm
spec:
  rateLimit:
    average: 100      # Requests per second
    period: 1s
    burst: 200        # Max burst size
    sourceCriterion:
      ipStrategy:
        depth: 1      # Use X-Forwarded-For header

---
# 5. HTTPS Redirect Middleware
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: https-redirect
  namespace: kasm
spec:
  redirectScheme:
    scheme: https
    permanent: true
    port: "443"

---
# 6. HTTPS IngressRoute (main)
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: kasm-workspace-https
  namespace: kasm
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`kasm.example.com`)
      kind: Rule
      services:
        - name: kasm-web
          port: 443
          scheme: https
      middlewares:
        - name: security-headers
        - name: rate-limit
  tls:
    secretName: kasm-tls-cert

---
# 7. HTTP to HTTPS Redirect IngressRoute
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: kasm-workspace-http
  namespace: kasm
spec:
  entryPoints:
    - web
  routes:
    - match: Host(`kasm.example.com`)
      kind: Rule
      services:
        - name: kasm-web
          port: 80
      middlewares:
        - name: https-redirect
```

---

### Example 4
**Problem:**
Configure a Kasm Workspaces deployment with hardened security context: non-root execution, read-only root filesystem, dropped capabilities, and seccomp profile. The configuration must mount emptyDir volumes for required writable paths (/tmp, /var/run, /.cache) to allow the application to function while maintaining immutability.

**Solution:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kasm-workspace
  namespace: kasm
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kasm-workspace
  template:
    metadata:
      labels:
        app: kasm-workspace
        tier: application
    spec:
      # Pod-level security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000    # Kasm user UID
        runAsGroup: 1000   # Kasm group GID
        fsGroup: 1000      # File system group
        seccompProfile:
          type: RuntimeDefault
      
      containers:
      - name: kasm-workspace
        image: kasmweb/desktop:1.14.0
        
        # Container-level security context
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true  # CRITICAL: Immutable container
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
              - ALL              # Drop all capabilities
            add:
              - NET_BIND_SERVICE # Only if binding to port <1024
        
        ports:
        - containerPort: 6901
          name: vnc
          protocol: TCP
        - containerPort: 8443
          name: https
          protocol: TCP
        
        # Required volume mounts for readOnlyRootFilesystem
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: var-run
          mountPath: /var/run
        - name: kasm-data
          mountPath: /home/kasm
        - name: cache
          mountPath: /.cache
        - name: config
          mountPath: /.config
        
        env:
        - name: VNC_PW
          valueFrom:
            secretKeyRef:
              name: kasm-secrets
              key: vnc-password
        
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      
      # Volumes for writable paths (readOnlyRootFilesystem requirement)
      volumes:
      - name: tmp
        emptyDir:
          sizeLimit: 500Mi
      - name: var-run
        emptyDir:
          sizeLimit: 100Mi
      - name: cache
        emptyDir:
          sizeLimit: 200Mi
      - name: config
        emptyDir:
          sizeLimit: 100Mi
      - name: kasm-data
        persistentVolumeClaim:
          claimName: kasm-workspace-pvc
```

---

### Example 5
**Problem:**
---
id: "20260101_init_container_debug"
difficulty: "hard"
tags: ["troubleshooting", "kubernetes", "init-containers", "kasm", "debugging"]
tech_stack: "Kubernetes, K3s, Kasm Workspaces, PostgreSQL, Redis"
---

# User Story
As a K8s operator, I want to diagnose and fix Kasm pods stuck in Init:X/Y state by identifying failing init containers and their root causes.

# Context & Constraints
Debug kasm-proxy-default-deployment stuck in Init:1/5:

**Init Container Sequence:**
1. wait-for-db: Waits for PostgreSQL
2. wait-for-redis: Waits for Redis
3. init-config: Generates configuration
4. init-certs: Sets up TLS certificates
5. db-migrate: Runs database migrations

**Symptoms:**
- Pod status shows Init:1/5 (second container failing)
- Pod never reaches Running state
- Services unavailable

**Pot

**Solution:**
{
  "session_id": "7e2e0e3b-992c-44e4-bef6-f3f71118e783",
  "response": "Based on the symptoms described in the story and the diagnosis patterns in the TDD and Golden Examples, I have identified the root cause as a likely permissions issue with the K3s `local-path` storage provisioner preventing the Redis container (a dependency for the failing init container) from starting. I have generated a fix script that adjusts the provisioner configuration and recreates the affected volume.\n\n```json\n{\n  \"reasoning\": \"The pod `kasm-proxy-default-deployment` is stuck in `Init:1/5`, which corresponds to the 2nd init container `wait-for-redis` (index 1) failing to complete. This implies the `kasm-redis` service is unreachable.\\n\\nRoot Cause Analysis:\\n1.  **Dependency Failure**: The `wait-for-redis` container is looping because the `kasm-redis` pod is likely not Ready.\\n2.  **K3s Storage Constraint**: K3s uses the `local-path` provisioner by default, which creates host directories with `0700` (root-only) permissions. If the Redis container image runs as a non-root user (standard security practice), it will fail to write to its mounted PVC, resulting in a `CrashLoopBackOff` or `Pending` state due to `Permission denied` errors.\\n3.  **Confirmation**: This matches the 'Golden Example' scenario for DB failures, applicable here to Redis as well.\\n\\nCorrective Action:\\n1.  Patch the `local-path-config` ConfigMap in the `kube-system` namespace to use `mkdir -m 0777` instead of `0700`, allowing non-root access.\\n2.  Restart the provisioner to apply the config.\\n3.  Delete the Redis PVC and Pod to force the creation of a new volume with the correct permissions.\",\n  \"code_changes\": {\n    \"solutions/fix_redis_init_stall.sh\": \"#!/bin/bash\\nset -euo pipefail\\n\\nNAMESPACE=\\\"kasm\\\"\\nREDIS_APP=\\\"kasm-redis\\\"\\n\\necho \\\"=== Kasm Init:1/5 Debug & Fix ===\\\"\\n\\n# 1. Identify the blocking Pod\\necho \\\"[1/5] Identifying stuck proxy pod...\\\"\\nPOD=$(kubectl get pods -n $NAMESPACE -l app=kasm-proxy --field-selector=status.phase=Pending -o name | head -1)\\nif [ -z \\\"$POD\\\" ]; then\\n  echo \\\"No pending proxy pods found. Exiting.\\\"\\n  exit 0\\nfi\\n\\n# 2. Verify Init Container State (Index 1 = wait-for-redis)\\necho \\\"[2/5] Checking init container status for $POD...\\\"\\nINIT_NAME=$(kubectl get $POD -n $NAMESPACE -o jsonpath='{.status.initContainerStatuses[1].name}')\\nINIT_READY=$(kubectl get $POD -n $NAMESPACE -o jsonpath='{.status.initContainerStatuses[1].ready}')\\n\\nif [ \\\"$INIT_NAME\\\" == \\\"wait-for-redis\\\" ] && [ \\\"$INIT_READY\\\" == \\\"false\\\" ]; then\\n  echo \\\"Verified: Pod is stuck on '$INIT_NAME'.\\\"\\nelse\\n  echo \\\"Mismatch: Pod is stuck on '$INIT_NAME' (Ready: $INIT_READY). Expected 'wait-for-redis'. Aborting fix.\\\"\\n  exit 1\\nfi\\n\\n# 3. Apply Local-Path Permission Fix\\n# Changes default directory creation from 0700 to 0777 for non-root containers\\necho \\\"[3/5] Patching local-path-

---

### Example 6
**Problem:**
---
id: "20260101_traefik_ingress_tls"
difficulty: "medium"
tags: ["networking", "ingress", "traefik", "tls", "k3s", "kasm"]
tech_stack: "K3s, Traefik, cert-manager, TLS, Ingress"
---

# User Story
As a network engineer, I want to configure Traefik ingress for Kasm Workspaces with automatic TLS certificate provisioning via cert-manager.

# Context & Constraints
Configure HTTPS access to Kasm via K3s Traefik:

**Components:**
- Traefik IngressRoute or Ingress resource
- TLS certificate (cert-manager or manual)
- HTTP to HTTPS redirect
- WebSocket support for session streaming

**Requirements:**
- Automatic TLS via Let's Encrypt (cert-manager)
- HTTP → HTTPS redirect middleware
- Valid certificate for kasm.example.com
- WebSocket upgrade headers preserved
- Sticky sessions for API

**Technic

**Solution:**
{
  "session_id": "8e8dfce2-6da2-45de-ae6a-93c703706c19",
  "response": "```json\n{\n  \"reasoning\": \"I have designed a Kubernetes manifest `manifests/kasm-ingress.yaml` to satisfy the networking requirements for Kasm Workspaces, adhering to the provided Golden Example and Story Constraints.\\n\\n1.  **ClusterIssuer**: Defines a `letsencrypt-prod` issuer using the HTTP-01 challenge. This is the standard method for `cert-manager` to automate TLS certificate provisioning on K3s.\\n2.  **Middleware**: Defines a `https-redirect` middleware in the `kasm` namespace. This meets the requirement for 'HTTP → HTTPS redirect middleware' and is referenced by the Ingress.\\n3.  **Ingress Configuration**:\\n    *   **Sticky Sessions**: Enabled via `affinity` and `sticky.cookie` annotations. This is identified as 'Critical' in the Golden Example for Kasm's multi-container architecture.\\n    *   **TLS Termination**: Configured with `router.tls: \\\"true\\\"` and the `cert-manager.io/cluster-issuer` annotation to automatically provision the `kasm-tls` secret.\\n    *   **Entrypoints**: Explicitly restricted to `websecure` (port 443) as per the Golden Example to ensure secure access. \\n    *   **Backend**: Routes to the `kasm-proxy` service on port 443, preserving the internal HTTPS communication expected by Kasm components.\",\n  \"code_changes\": [\n    {\n      \"file\": \"manifests/kasm-ingress.yaml\",\n      \"content\": \"apiVersion: cert-manager.io/v1\\nkind: ClusterIssuer\\nmetadata:\\n  name: letsencrypt-prod\\nspec:\\n  acme:\\n    server: https://acme-v02.api.letsencrypt.org/directory\\n    email: admin@example.com\\n    privateKeySecretRef:\\n      name: letsencrypt-prod\\n    solvers:\\n    - http01:\\n        ingress:\\n          class: traefik\\n---\\napiVersion: traefik.containo.us/v1alpha1\\nkind: Middleware\\nmetadata:\\n  name: https-redirect\\n  namespace: kasm\\nspec:\\n  redirectScheme:\\n    scheme: https\\n    permanent: true\\n---\\napiVersion: networking.k8s.io/v1\\nkind: Ingress\\nmetadata:\\n  name: kasm-ingress\\n  namespace: kasm\\n  annotations:\\n    kubernetes.io/ingress.class: traefik\\n    cert-manager.io/cluster-issuer: letsencrypt-prod\\n    traefik.ingress.kubernetes.io/router.entrypoints: websecure\\n    traefik.ingress.kubernetes.io/router.tls: \\\"true\\\"\\n    traefik.ingress.kubernetes.io/affinity: \\\"true\\\"\\n    traefik.ingress.kubernetes.io/service.sticky.cookie: \\\"true\\\"\\n    traefik.ingress.kubernetes.io/service.sticky.cookie.name: kasm_session\\n    traefik.ingress.kubernetes.io/router.middlewares: kasm-https-redirect@kubernetescrd\\n    traefik.ingress.kubernetes.io/service.server.port: \\\"443\\\"\\nspec:\\n  tls:\\n  - hosts:\\n    - kasm.example.com\\n    secretName: kasm-tls\\n  rules:\\n  - host: kasm.example.com\\n    http:\\n      paths:\\n      - path: /\\n        pathType: Prefix\\n        backend:\\n          service:\\n            name: kasm-proxy\\n            port:\\n              number: 4

---

### Example 7
**Problem:**
---
id: "20260101_init_container_debug"
difficulty: "hard"
tags: ["troubleshooting", "kubernetes", "init-containers", "kasm", "debugging"]
tech_stack: "Kubernetes, K3s, Kasm Workspaces, PostgreSQL, Redis"
---

# User Story
As a K8s operator, I want to diagnose and fix Kasm pods stuck in Init:X/Y state by identifying failing init containers and their root causes.

# Context & Constraints
Debug kasm-proxy-default-deployment stuck in Init:1/5:

**Init Container Sequence:**
1. wait-for-db: Waits for PostgreSQL
2. wait-for-redis: Waits for Redis
3. init-config: Generates configuration
4. init-certs: Sets up TLS certificates
5. db-migrate: Runs database migrations

**Symptoms:**
- Pod status shows Init:1/5 (second container failing)
- Pod never reaches Running state
- Services unavailable

**Pot

**Solution:**
{
  "session_id": "85cabb41-f0a6-42cb-b541-fcef46855beb",
  "response": "```json\n{\n  \"reasoning\": \"The 'Init:1/5' status indicates the 'wait-for-db' container is failing to connect to the PostgreSQL database. This blockage prevents the Kasm proxy from starting. Based on the K3s/Kasm deployment context, the two primary suspects are: 1) Storage Permissions: The K3s 'local-path' provisioner defaults to 0700 permissions, preventing the non-root PostgreSQL container (UID 1001) from writing to its volume, leading to a CrashLoopBackOff. 2) Network Isolation: A 'Default Deny' NetworkPolicy might be blocking the init container's connection attempt to 'kasm-db:5432'. The solution involves a diagnostic script to pinpoint the failure (Pod status vs. Network) and a fix script that patches the storage provisioner and ensures internal connectivity.\",\n  \"code_changes\": {\n    \"diagnose_init_1_5.sh\": \"#!/bin/bash\\nset -euo pipefail\\nNAMESPACE=\\\"kasm\\\"\\n\\necho \\\"=== Kasm Init:1/5 Diagnostic ===\\\"\\n\\n# 1. Identify Blocking Init Container\\necho \\\"[1] Checking Pod Init Status...\\\"\\nPOD=$(kubectl get pods -n $NAMESPACE -l app=kasm-proxy -o name | head -1)\\nkubectl get $POD -n $NAMESPACE -o jsonpath='{.status.initContainerStatuses[*].name}' | tr ' ' '\\\\n' | nl\\n\\n# 2. Check Database Pod Health (Target of Init:1/5)\\necho \\\"\\\\n[2] Checking Database Pod (kasm-db)...\\\"\\nDB_STATUS=$(kubectl get pods -n $NAMESPACE -l app=kasm-db --no-headers | awk '{print $3}')\\necho \\\"DB Pod Status: $DB_STATUS\\\"\\n\\nif [[ \\\"$DB_STATUS\\\" != \\\"Running\\\" ]]; then\\n  echo \\\"-> FAILURE: Database is not running.\\\"\\n  echo \\\"-> Checking for PVC issues (Pending?)...\\\"\\n  kubectl get pvc -n $NAMESPACE -l app=kasm-db\\n  echo \\\"-> Checking for CrashLoopBackOff (Logs)...\\\"\\n  kubectl logs -n $NAMESPACE -l app=kasm-db --tail=20\\nelse\\n  echo \\\"-> SUCCESS: Database is running.\\\"\\n  # 3. Check Connectivity (Only if DB is running)\\n  echo \\\"\\\\n[3] Testing Connectivity...\\\"\\n  kubectl run -it --rm debug-net --image=busybox -n $NAMESPACE --restart=Never -- nc -zv kasm-db 5432\\nfi\\n\",\n    \"fix_init_1_5.sh\": \"#!/bin/bash\\nset -euo pipefail\\nNAMESPACE=\\\"kasm\\\"\\n\\necho \\\"=== Applying Fixes for Init:1/5 ===\\\"\\n\\n# Fix 1: K3s local-path Permission Denied (Root Cause for DB CrashLoop)\\n# Updates provisioner to create volumes with 0777 so non-root DB can write.\\necho \\\"[1] Patching local-path-provisioner permissions...\\\"\\nkubectl patch cm local-path-config -n kube-system --type=merge -p '{\\\"data\\\":{\\\"setupCommand\\\":\\\"/opt/local-path-provisioner/bin/entrypoint.sh -D /opt/local-path-provisioner/bin/ -p -m 0777\\\"}}'\\n\\n# Restart provisioner to apply config\\nkubectl delete pod -l app=local-path-provisioner -n kube-system\\necho \\\"-> local-path-provisioner patched.\\\"\\n\\n# Fix 2: Ensure Network Connectivity\\n# Applies a NetworkPolicy allowing internal traffic within the namespace.\\n

---

### Example 8
**Problem:**
Implement database pod isolation on K3s to restrict PostgreSQL and Redis access only to authorized Kasm application pods. The policy must allow monitoring from Prometheus while blocking all other traffic, ensuring defense-in-depth for sensitive data stores.

**Solution:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kasm-database-isolation
  namespace: kasm
  annotations:
    policy.kubernetes.io/description: "Restrict database access to app pods only"
spec:
  # Apply to database pods (PostgreSQL/Redis)
  podSelector:
    matchLabels:
      app: kasm-database
      tier: database
  policyTypes:
    - Ingress
    - Egress
  
  # Ingress: Only allow from Kasm application pods
  ingress:
    # PostgreSQL access from app pods
    - from:
        - podSelector:
            matchLabels:
              app: kasm-workspace
              tier: application
      ports:
        - protocol: TCP
          port: 5432  # PostgreSQL
    
    # Redis access from app pods
    - from:
        - podSelector:
            matchLabels:
              app: kasm-workspace
              tier: application
      ports:
        - protocol: TCP
          port: 6379  # Redis
    
    # Allow monitoring pods (Prometheus)
    - from:
        - namespaceSelector:
            matchLabels:
              name: monitoring
          podSelector:
            matchLabels:
              app: prometheus
      ports:
        - protocol: TCP
          port: 9187  # PostgreSQL exporter
        - protocol: TCP
          port: 9121  # Redis exporter
  
  # Egress: Allow DNS and external DB backups
  egress:
    # DNS resolution
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    
    # S3/Object storage for backups (adjust CIDR for your cloud)
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8      # Block internal networks
              - 172.16.0.0/12
              - 192.168.0.0/16
      ports:
        - protocol: TCP
          port: 443  # HTTPS for S3/backups
```

---

### Example 9
**Problem:**
Harden Kasm namespace by blocking external access to Database/Redis and defaulting to Deny All.

**Solution:**
### 1. Default Deny Policy
Blocks all ingress/egress unless explicitly allowed.
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: kasm
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### 2. Allow API/Manager Access to Postgres
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-db-access
  namespace: kasm
spec:
  podSelector:
    matchLabels:
      app: postgres  # Verify label matches helm chart (often: kasm-db)
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: kasm-manager
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: kasm-api
    ports:
    - protocol: TCP
      port: 5432
```

### 3. Allow Manager Access to Redis
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-redis-access
  namespace: kasm
spec:
  podSelector:
    matchLabels:
      app: redis # Verify label (often: kasm-redis)
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: kasm-manager
    ports:
    - protocol: TCP
      port: 6379
```

---

### Example 10
**Problem:**
---
id: "20260101_network_policy_isolation"
difficulty: "medium"
tags: ["security", "network-policy", "kubernetes", "kasm", "isolation"]
tech_stack: "Kubernetes, K3s, NetworkPolicy, Kasm Workspaces"
---

# User Story
As a security engineer, I want to implement NetworkPolicies to isolate Kasm database and internal services from unauthorized pod-to-pod traffic.

# Context & Constraints
Implement defense-in-depth for Kasm namespace:

**Components:**
- Default deny ingress policy
- Allow rules for kasm-api → kasm-db
- Allow rules for kasm-manager → kasm-redis
- Ingress from Traefik to kasm-proxy

**Requirements:**
- PostgreSQL only accessible from API/manager
- Redis only accessible from manager
- External access only via Traefik ingress
- Block all other pod-to-pod traffic

**Technical Constr

**Solution:**
{
  "session_id": "2328f8c0-282b-4ca9-9c67-96f3c742096e",
  "response": "```json\n{\n  \"reasoning\": \"I have designed a set of Kubernetes NetworkPolicies to implement a defense-in-depth strategy for the Kasm namespace on K3s. \\n\\n1.  **Default Deny**: A `default-deny` policy is established to block all ingress traffic by default, creating a zero-trust baseline.\\n2.  **Database Isolation**: The `allow-db-access` policy strictly limits access to the PostgreSQL database (port 5432) to only the `kasm-api` and `kasm-manager` pods, preventing unauthorized access from other components.\\n3.  **Redis Isolation**: The `allow-redis-access` policy restricts Redis (port 6379) access solely to the `kasm-manager`, protecting session state.\\n4.  **Ingress Access**: The `allow-proxy-ingress` policy explicitly permits traffic to the `kasm-proxy` from the Traefik Ingress Controller, which typically resides in the `kube-system` namespace in K3s distributions. This ensures external connectivity via the ingress while maintaining internal isolation.\",\n  \"changes\": [\n    {\n      \"file\": \"kasm-network-policies.yaml\",\n      \"content\": \"apiVersion: networking.k8s.io/v1\\nkind: NetworkPolicy\\nmetadata:\\n  name: default-deny\\n  namespace: kasm\\nspec:\\n  podSelector: {}\\n  policyTypes:\\n  - Ingress\\n---\\napiVersion: networking.k8s.io/v1\\nkind: NetworkPolicy\\nmetadata:\\n  name: allow-db-access\\n  namespace: kasm\\nspec:\\n  podSelector:\\n    matchLabels:\\n      app: kasm-db\\n  policyTypes:\\n  - Ingress\\n  ingress:\\n  - from:\\n    - podSelector:\\n        matchLabels:\\n          app: kasm-api\\n    - podSelector:\\n        matchLabels:\\n          app: kasm-manager\\n    ports:\\n    - protocol: TCP\\n      port: 5432\\n---\\napiVersion: networking.k8s.io/v1\\nkind: NetworkPolicy\\nmetadata:\\n  name: allow-redis-access\\n  namespace: kasm\\nspec:\\n  podSelector:\\n    matchLabels:\\n      app: kasm-redis\\n  policyTypes:\\n  - Ingress\\n  ingress:\\n  - from:\\n    - podSelector:\\n        matchLabels:\\n          app: kasm-manager\\n    ports:\\n    - protocol: TCP\\n      port: 6379\\n---\\napiVersion: networking.k8s.io/v1\\nkind: NetworkPolicy\\nmetadata:\\n  name: allow-proxy-ingress\\n  namespace: kasm\\nspec:\\n  podSelector:\\n    matchLabels:\\n      app: kasm-proxy\\n  policyTypes:\\n  - Ingress\\n  ingress:\\n  - from:\\n    - namespaceSelector:\\n        matchLabels:\\n          kubernetes.io/metadata.name: kube-system\\n      podSelector:\\n        matchLabels:\\n          app.kubernetes.io/name: traefik\\n\"\n    }\n  ]\n}\n```",
  "stats": {
    "models": {
      "gemini-2.5-flash-lite": {
        "api": {
          "totalRequests": 1,
          "totalErrors": 0,
          "totalLatencyMs": 1930
        },
        "tokens": {
          "input": 2382,
          "prompt": 2382,
          "candidates": 109,
          "total": 2847,
          "cached": 0,
          "thoughts": 356,
          "tool": 0
        }
      },

---

### Example 11
**Problem:**
---
id: "20260101_init_container_debug"
difficulty: "hard"
tags: ["troubleshooting", "kubernetes", "init-containers", "kasm", "debugging"]
tech_stack: "Kubernetes, K3s, Kasm Workspaces, PostgreSQL, Redis"
---

# User Story
As a K8s operator, I want to diagnose and fix Kasm pods stuck in Init:X/Y state by identifying failing init containers and their root causes.

# Context & Constraints
Debug kasm-proxy-default-deployment stuck in Init:1/5:

**Init Container Sequence:**
1. wait-for-db: Waits for PostgreSQL
2. wait-for-redis: Waits for Redis
3. init-config: Generates configuration
4. init-certs: Sets up TLS certificates
5. db-migrate: Runs database migrations

**Symptoms:**
- Pod status shows Init:1/5 (second container failing)
- Pod never reaches Running state
- Services unavailable

**Pot

**Solution:**
{
  "session_id": "51bfd6b9-93fd-4038-b81e-4aec10c303ed",
  "response": "```json\n{\n  \"reasoning\": \"The pod status 'Init:1/5' combined with the symptom 'second container failing' indicates that the first init container (wait-for-db) completed successfully, and the deployment is blocked at the second container (wait-for-redis). This suggests the kasm-redis service is unhealthy or unreachable. In K3s environments, a common root cause for backing services failing to start is the `local-path-provisioner` defaulting to `0700` (root-only) permissions, which prevents non-root containers (like Redis, often UID 1001) from writing to their persistent volumes. The remediation involves diagnosing the specific error logs, patching the storage provisioner to allow `0777` permissions, and recycling the affected Redis PVC/Pod to ensure the volume is re-provisioned with the correct access rights.\",\n  \"code_changes\": {\n    \"filename\": \"fix_kasm_redis_init.sh\",\n    \"content\": \"#!/bin/bash\\nset -euo pipefail\\n\\n# 1. Diagnostic: Check logs for the failing init container (wait-for-redis)\\necho \\\">>> Checking logs for failing init container (wait-for-redis)...\\\"\\nkubectl logs -n kasm -l app=kasm-proxy -c wait-for-redis --tail=20 || true\\n\\n# 2. Diagnostic: Inspect Redis pod state and events\\n# Look for 'CrashLoopBackOff' or 'Pending' and 'FailedMount' events\\necho \\\">>> Checking kasm-redis pod status and events...\\\"\\nkubectl get pods -n kasm -l app=kasm-redis\\nkubectl describe pod -n kasm -l app=kasm-redis | grep -A 10 \\\"Events\\\"\\n\\n# 3. Fix: Patch K3s local-path-provisioner for non-root access\\n# Changes permission mode from default 0700 to 0777 to allow non-root UIDs to write\\necho \\\">>> Patching local-path-config to use mode 0777...\\\"\\nkubectl patch cm local-path-config -n kube-system --type=merge -p '{\\\"data\\\":{\\\"setupCommand\\\":\\\"/opt/local-path-provisioner/bin/entrypoint.sh -D /opt/local-path-provisioner/bin/ -p -m 0777\\\"}}'\\n\\n# 4. Apply: Restart the provisioner to load new config\\necho \\\">>> Restarting local-path-provisioner...\\\"\\nkubectl delete pod -l app=local-path-provisioner -n kube-system --wait=true\\n\\n# 5. Recovery: Recycle Redis PVC and Pod\\n# This forces the volume to be re-created with the new 0777 permissions\\n# WARNING: This destroys existing data in the Redis volume\\necho \\\">>> Recycling Redis PVC and Pod...\\\"\\nkubectl delete pvc -n kasm -l app=kasm-redis --wait=true\\nkubectl delete pod -n kasm -l app=kasm-redis --wait=true\\n\\n# 6. Verification\\necho \\\">>> Waiting for kasm-proxy deployment to proceed...\\\"\\nkubectl rollout status deployment/kasm-proxy -n kasm --timeout=120s\"\n  }\n}\n```",
  "stats": {
    "models": {
      "gemini-2.5-flash-lite": {
        "api": {
          "totalRequests": 1,
          "totalErrors": 0,
          "totalLatencyMs": 2138
        },
        "tokens": {
          "input": 5855,
          "prompt": 5855,
          "candidates": 11

---
