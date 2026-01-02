---
id: "20260102_coturn_deployment"
difficulty: "medium"
tags: ["webrtc", "turn", "stun", "nat", "coturn"]
tech_stack: "Coturn, Kubernetes, UDP, TLS"
---

# User Story
As a streaming engineer, I want a Coturn TURN server deployment, so WebRTC connections work through restrictive NATs and firewalls.

# Context & Constraints
**Deployment Configuration:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coturn
spec:
  template:
    spec:
      hostNetwork: true
      containers:
        - name: coturn
          image: coturn/coturn:latest
          args:
            - -n
            - --log-file=stdout
            - --external-ip=$(POD_IP)
            - --listening-port=3478
            - --min-port=49152
            - --max-port=65535
            - --realm=vdi.example.com
```

**Network Requirements:**
| Port | Protocol | Purpose |
|------|----------|---------|
| 3478 | TCP/UDP | STUN/TURN signaling |
| 49152-65535 | UDP | Media relay range |

**Security:**
- Long-term credentials: `--lt-cred-mech`
- Shared secret for credential generation
- TLS for signaling (optional)

**Selkies Integration:**
```bash
# Pass TURN config to Selkies
SELKIES_TURN_HOST=turn.vdi.example.com
SELKIES_TURN_PORT=3478
SELKIES_TURN_USERNAME=vdi
SELKIES_TURN_PASSWORD=$(TURN_SECRET)
```

# Acceptance Criteria
- [ ] **Deployment:** Create Coturn Deployment with hostNetwork: true
- [ ] **Ports:** Expose UDP 3478 and relay port range
- [ ] **External IP:** Configure --external-ip for NAT
- [ ] **Credentials:** Use long-term credentials with secret
- [ ] **Integration:** Pass TURN config to Selkies pods via env vars
- [ ] **Service:** Create LoadBalancer or NodePort Service for external access
