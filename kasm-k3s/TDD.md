# TDD: Kasm Workspaces on K3s

## Technical Design Document

This document provides implementation specifications for deploying and operating Kasm Workspaces on K3s.

---

## 1. Helm Chart Configuration

### 1.1 values.yaml Structure

```yaml
# Global settings
global:
  namespace: kasm
  hostname: kasm.example.com
  clusterDomain: cluster.local
  imageRegistry: kasmweb

# Storage configuration
storage:
  storageClass: local-path  # k3s default
  dbSize: 10Gi
  redisSize: 1Gi

# Resource limits
resources:
  api:
    requests:
      memory: 256Mi
      cpu: 250m
    limits:
      memory: 512Mi
      cpu: 500m
  proxy:
    requests:
      memory: 128Mi
      cpu: 100m
    limits:
      memory: 256Mi
      cpu: 250m

# TLS configuration
tls:
  enabled: true
  secretName: kasm-tls
  # If using cert-manager:
  # issuer: letsencrypt-prod

# Database
database:
  internal: true  # Deploy PostgreSQL in cluster
  host: kasm-db
  port: 5432
  # For external DB:
  # internal: false
  # host: external-postgres.example.com
  # existingSecret: kasm-db-credentials
```

### 1.2 K3s-Specific Overrides

```yaml
# k3s-values.yaml
ingress:
  enabled: true
  className: traefik
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: websecure
    traefik.ingress.kubernetes.io/router.tls: "true"

# Disable LoadBalancer (use Traefik)
service:
  type: ClusterIP

# Local-path storage
persistence:
  storageClass: local-path
```

---

## 2. Init Container Specifications

### 2.1 Init Container Sequence

The `kasm-proxy` deployment has 5 init containers:

| Order | Name | Purpose | Dependencies |
|-------|------|---------|--------------|
| 1 | `wait-for-db` | PostgreSQL readiness | Database pod |
| 2 | `wait-for-redis` | Redis readiness | Redis pod |
| 3 | `init-config` | Generate configs | ConfigMaps |
| 4 | `init-certs` | TLS certificate setup | Secrets |
| 5 | `db-migrate` | Schema migrations | Database connection |

### 2.2 Init Container Implementation

```yaml
initContainers:
  - name: wait-for-db
    image: busybox:1.36
    command:
      - sh
      - -c
      - |
        until nc -z kasm-db 5432; do
          echo "Waiting for PostgreSQL..."
          sleep 2
        done
        echo "PostgreSQL is ready"
    
  - name: wait-for-redis
    image: busybox:1.36
    command:
      - sh
      - -c
      - |
        until nc -z kasm-redis 6379; do
          echo "Waiting for Redis..."
          sleep 2
        done
        echo "Redis is ready"
    
  - name: init-config
    image: kasmweb/kasm-config:latest
    volumeMounts:
      - name: config-volume
        mountPath: /config
    env:
      - name: KASM_HOSTNAME
        valueFrom:
          configMapKeyRef:
            name: kasm-config
            key: hostname
    
  - name: init-certs
    image: kasmweb/kasm-certs:latest
    volumeMounts:
      - name: certs-volume
        mountPath: /certs
      - name: tls-secret
        mountPath: /tls
        readOnly: true
    
  - name: db-migrate
    image: kasmweb/kasm-api:latest
    command: ["kasm-migrate", "--up"]
    env:
      - name: DATABASE_URL
        valueFrom:
          secretKeyRef:
            name: kasm-db-credentials
            key: url
```

---

## 3. Troubleshooting Procedures

### 3.1 Debug Init:1/5 (wait-for-db failed)

**Symptom:** Second init container waiting indefinitely.

**Diagnosis:**
```bash
# Check if database pod exists
kubectl get pods -n kasm -l app=kasm-db

# Check database logs
kubectl logs -n kasm deployment/kasm-db

# Test connectivity from debug pod
kubectl run -it --rm debug --image=busybox -n kasm -- nc -zv kasm-db 5432
```

**Fixes:**
```bash
# If PVC pending
kubectl get pvc -n kasm
kubectl describe pvc kasm-db-pvc -n kasm

# Force recreate database
kubectl delete pod -n kasm -l app=kasm-db
```

### 3.2 Debug Init:2/5 (wait-for-redis failed)

```bash
# Check Redis pod
kubectl get pods -n kasm -l app=kasm-redis
kubectl logs -n kasm deployment/kasm-redis

# Test Redis connectivity
kubectl run -it --rm debug --image=redis:alpine -n kasm -- redis-cli -h kasm-redis ping
```

### 3.3 Debug Init:3/5 (init-config failed)

```bash
# Check ConfigMap exists
kubectl get configmap kasm-config -n kasm -o yaml

# Check init container logs
POD=$(kubectl get pods -n kasm -l app=kasm-proxy -o name | head -1)
kubectl logs -n kasm $POD -c init-config
```

### 3.4 Debug Init:4/5 (init-certs failed)

```bash
# Check TLS secret exists
kubectl get secret kasm-tls -n kasm

# Verify certificate validity
kubectl get secret kasm-tls -n kasm -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text -noout
```

### 3.5 Debug Init:5/5 (db-migrate failed)

```bash
# Check migration logs
kubectl logs -n kasm $POD -c db-migrate

# Common issues:
# - DATABASE_URL secret missing
# - Schema version mismatch
# - Connection refused (DB not ready despite wait-for-db)
```

---

## 4. Deployment Scripts

### 4.1 install.sh

```bash
#!/bin/bash
set -euo pipefail

NAMESPACE="${KASM_NAMESPACE:-kasm}"
HOSTNAME="${KASM_HOSTNAME:-kasm.local}"
STORAGE_CLASS="${STORAGE_CLASS:-local-path}"

echo "=== Deploying Kasm Workspaces to K3s ==="

# Clone Helm chart
if [ ! -d "kasm-helm" ]; then
    git clone https://github.com/kasmtech/kasm-helm.git
fi
cd kasm-helm

# Create namespace
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Generate values
cat > k3s-values.yaml <<EOF
global:
  namespace: $NAMESPACE
  hostname: $HOSTNAME
storage:
  storageClass: $STORAGE_CLASS
EOF

# Install
helm upgrade --install kasm . -n $NAMESPACE -f k3s-values.yaml

# Wait for pods
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=kasm -n $NAMESPACE --timeout=300s

echo "=== Installation Complete ==="
echo "Access Kasm at: https://$HOSTNAME"
```

### 4.2 diagnose.sh

```bash
#!/bin/bash
NAMESPACE="${1:-kasm}"

echo "=== Kasm K3s Diagnostic Report ==="
echo "Namespace: $NAMESPACE"
echo "Timestamp: $(date -Iseconds)"
echo ""

echo "--- Pod Status ---"
kubectl get pods -n $NAMESPACE -o wide

echo ""
echo "--- PVC Status ---"
kubectl get pvc -n $NAMESPACE

echo ""
echo "--- Services ---"
kubectl get svc -n $NAMESPACE

echo ""
echo "--- Recent Events (Warnings) ---"
kubectl get events -n $NAMESPACE --field-selector type=Warning --sort-by='.lastTimestamp' | tail -20

echo ""
echo "--- Init Container Status ---"
for pod in $(kubectl get pods -n $NAMESPACE -o name); do
    status=$(kubectl get $pod -n $NAMESPACE -o jsonpath='{.status.initContainerStatuses[*].ready}')
    if echo "$status" | grep -q "false"; then
        echo "$pod has failing init containers:"
        kubectl get $pod -n $NAMESPACE -o jsonpath='{range .status.initContainerStatuses[*]}{.name}: {.ready} ({.state.waiting.reason}){"\n"}{end}'
    fi
done

echo ""
echo "--- Resource Usage ---"
kubectl top pods -n $NAMESPACE 2>/dev/null || echo "(metrics-server not available)"
```

### 4.3 uninstall.sh

```bash
#!/bin/bash
NAMESPACE="${1:-kasm}"

echo "=== Uninstalling Kasm from K3s ==="

helm uninstall kasm -n $NAMESPACE || true

echo "Deleting PVCs (data will be lost)..."
read -p "Continue? [y/N] " confirm
if [[ $confirm == [yY] ]]; then
    kubectl delete pvc --all -n $NAMESPACE
fi

kubectl delete namespace $NAMESPACE

echo "=== Uninstall Complete ==="
```

---

## 5. Monitoring & Observability

### 5.1 Health Probes

```yaml
# Added to each deployment
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### 5.2 Prometheus Metrics

```yaml
# ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kasm-metrics
  namespace: kasm
spec:
  selector:
    matchLabels:
      app: kasm-api
  endpoints:
    - port: metrics
      interval: 30s
```

### 5.3 Log Aggregation

```bash
# Stream all Kasm logs
kubectl logs -n kasm -l app.kubernetes.io/instance=kasm -f --max-log-requests=10

# Export logs to file
kubectl logs -n kasm deployment/kasm-api --since=1h > kasm-api.log
```

---

## 6. Backup & Recovery

### 6.1 Database Backup

```bash
#!/bin/bash
NAMESPACE="kasm"
BACKUP_DIR="/backups/kasm"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Get DB pod
DB_POD=$(kubectl get pods -n $NAMESPACE -l app=kasm-db -o name | head -1)

# Run pg_dump
kubectl exec -n $NAMESPACE $DB_POD -- pg_dump -U kasm kasm > "$BACKUP_DIR/kasm-db-$TIMESTAMP.sql"

# Compress
gzip "$BACKUP_DIR/kasm-db-$TIMESTAMP.sql"

echo "Backup saved: $BACKUP_DIR/kasm-db-$TIMESTAMP.sql.gz"
```

### 6.2 Full Namespace Backup

```bash
# Export all resources
kubectl get all,cm,secrets,pvc -n kasm -o yaml > kasm-namespace-backup.yaml
```

---

## 7. Security Hardening

### 7.1 Network Policies

```yaml
# Deny all ingress by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: kasm
spec:
  podSelector: {}
  policyTypes:
    - Ingress

---
# Allow only necessary internal traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-kasm-internal
  namespace: kasm
spec:
  podSelector: {}
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kasm
```

### 7.2 Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: kasm
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

---

## 8. Integration Points

### 8.1 Agent Registration

```bash
# On Agent VM, after installation:
/opt/kasm/bin/utils/agent_register.py \
    --server https://kasm.example.com \
    --token <REGISTRATION_TOKEN> \
    --zone default
```

### 8.2 LDAP/SSO Configuration

```yaml
# In values.yaml
auth:
  ldap:
    enabled: true
    host: ldap.example.com
    port: 636
    baseDN: dc=example,dc=com
    bindDN: cn=admin,dc=example,dc=com
    bindPasswordSecret: ldap-bind-password
```
