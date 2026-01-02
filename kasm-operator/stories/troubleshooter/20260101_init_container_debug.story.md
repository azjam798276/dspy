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

**Potential Causes:**
- Database pod not running or PVC pending
- Redis connection failure
- ConfigMap or Secret missing
- DNS resolution issues
- Network policy blocking traffic
- Resource constraints (OOM, CPU throttling)

**Technical Constraints:**
- Must use kubectl for diagnosis
- Init container logs may be empty if container didn't start
- Events section provides startup error details

# Acceptance Criteria
- [ ] Identify which init container is failing
- [ ] Extract logs from failing init container
- [ ] Diagnose root cause (PVC, DNS, Secret, etc.)
- [ ] Apply fix and verify pod reaches Running state
- [ ] Document troubleshooting steps for future reference
