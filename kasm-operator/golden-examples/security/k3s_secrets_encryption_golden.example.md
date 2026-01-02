---
id: "k3s_secrets_encryption"
source: "https://github.com/k3s-io/k3s/wiki/secrets-encryption-test-plan"
tags: ["security", "secrets", "encryption", "k3s", "etcd"]
---

## Problem
Enable secrets encryption at rest for K3s to protect sensitive data stored in the database (etcd/SQLite). Implement a custom encryption configuration with AES-CBC, support for key rotation, and verification that secrets are properly encrypted.

## Solution
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

## Key Techniques
- AES-CBC encryption with 256-bit keys (32 bytes base64)
- EncryptionConfiguration with provider fallback chain
- Zero-downtime key rotation via k3s secrets-encrypt commands
- Verification using SQLite database inspection
- Secure key generation from /dev/urandom
- K3s-native --secrets-encryption flag for fresh installs
