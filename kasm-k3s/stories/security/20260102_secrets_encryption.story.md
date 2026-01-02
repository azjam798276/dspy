---
id: "20260102_secrets_encryption"
difficulty: "easy"
tags: ["security", "secrets", "encryption", "kubernetes", "kasm"]
tech_stack: "Kubernetes, K3s, Secrets Encryption"
---

# User Story
As a security engineer, I want to enable secrets encryption at rest for K3s to protect sensitive data stored in the database.

# Context & Constraints
Implement secrets encryption for K3s cluster:

**Requirements:**
- Enable K3s native secrets encryption
- Use AES-CBC with 256-bit keys (32 bytes base64)
- Create EncryptionConfiguration resource
- Support key rotation without downtime

**K3s Commands:**
```bash
# Fresh install with encryption
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--secrets-encryption" sh -

# Check status
sudo k3s secrets-encrypt status

# Rotate keys
sudo k3s secrets-encrypt prepare
sudo k3s secrets-encrypt rotate
sudo k3s secrets-encrypt reencrypt
```

# Acceptance Criteria
- [ ] K3s installed with --secrets-encryption flag
- [ ] EncryptionConfiguration uses aescbc provider
- [ ] Encryption key is 32 bytes (256-bit)
- [ ] Verify secrets are encrypted in database
- [ ] Document key rotation procedure
