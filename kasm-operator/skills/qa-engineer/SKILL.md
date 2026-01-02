---
name: qa-engineer
description: QA Engineer for VDI Platform Testing and Validation
---



---
name: qa-engineer
description: Expert in Quality Assurance for Kubernetes-native VDI platforms, specializing in end-to-end, performance, and failure testing.
---

# QA Engineering: VDI Platform Testing Strategies

## Core Principles
1. **End-to-End Coverage:** Test complete user flows from login to streaming.
2. **Performance Baselines:** Establish latency and throughput thresholds.
3. **Failure Injection:** Verify graceful degradation under adverse conditions.
4. **Automation First:** All tests scriptable for CI/CD integration.

## Test Categories

### Unit Tests (Operator)
```go
func TestBuildPod(t *testing.T) {
    session := &vdiv1alpha1.VDISession{
        Spec: vdiv1alpha1.VDISessionSpec{
            User:     "alice@example.com",
            Template: "ubuntu-desktop",
        },
    }
    template := &vdiv1alpha1.VDITemplate{
        Spec: vdiv1alpha1.VDITemplateSpec{
            Image: "selkies:latest",
        },
    }
    
    pod := reconciler.buildPod(session, template)
    
    assert.Equal(t, "selkies:latest", pod.Spec.Containers[0].Image)
    assert.Contains(t, pod.Spec.Containers[0].Resources.Limits, "nvidia.com/gpu")
}
```

### Integration Tests (envtest)
```go
var _ = Describe("VDISession Controller", func() {
    Context("When creating a VDISession", func() {
        It("Should create a Pod with correct resources", func() {
            session := &vdiv1alpha1.VDISession{...}
            Expect(k8sClient.Create(ctx, session)).To(Succeed())
            
            Eventually(func() string {
                k8sClient.Get(ctx, key, session)
                return session.Status.Phase
            }, timeout).Should(Equal("Running"))
        })
    })
})
```

### E2E Tests (Real Cluster)
```bash
#!/bin/bash
# e2e_session_lifecycle.sh

# Create session
kubectl apply -f - <<EOF
apiVersion: vdi.kasm.io/v1alpha1
kind: VDISession
metadata:
  name: test-session
spec:
  user: test@example.com
  template: ubuntu-desktop
EOF

# Wait for Running
kubectl wait vdisession/test-session --for=jsonpath='{.status.phase}'=Running --timeout=60s

# Verify Pod exists
kubectl get pod -l vdi.kasm.io/session=test-session

# Verify IngressRoute created
kubectl get ingressroute test-session

# Cleanup
kubectl delete vdisession/test-session
kubectl wait vdisession/test-session --for=delete --timeout=30s
```

## Performance Testing

### Latency Measurement
```javascript
// WebRTC stats collection
const stats = await peerConnection.getStats();
stats.forEach(report => {
    if (report.type === 'inbound-rtp' && report.kind === 'video') {
        console.log('Jitter:', report.jitter);
        console.log('Packets Lost:', report.packetsLost);
        console.log('Frames Decoded:', report.framesDecoded);
    }
});
```

### Load Testing
```bash
# Concurrent session creation
for i in $(seq 1 8); do
  kubectl apply -f - <<EOF
apiVersion: vdi.kasm.io/v1alpha1
kind: VDISession
metadata:
  name: load-test-$i
spec:
  user: load-$i@test.com
  template: ubuntu-desktop
EOF
done

# Measure time to all Running
time kubectl wait vdisession -l test=load --for=jsonpath='{.status.phase}'=Running --timeout=120s
```

## Failure Scenario Tests

### GPU Unavailable
```bash
# Taint GPU node
kubectl taint nodes gpu-node nvidia.com/gpu=:NoSchedule

# Create session, expect Pending
kubectl apply -f session.yaml
kubectl wait vdisession/test --for=jsonpath='{.status.phase}'=Pending --timeout=10s

# Remove taint, expect Running
kubectl taint nodes gpu-node nvidia.com/gpu-
kubectl wait vdisession/test --for=jsonpath='{.status.phase}'=Running --timeout=60s
```

### Session Timeout
```bash
# Create session with 1m timeout
kubectl apply -f - <<EOF
apiVersion: vdi.kasm.io/v1alpha1
kind: VDISession
metadata:
  name: timeout-test
spec:
  user: test@example.com
  template: ubuntu-desktop
  timeout: "1m"
EOF

# Wait for auto-termination
sleep 90
kubectl get vdisession timeout-test || echo "Session correctly terminated"
```

## Acceptance Criteria Checklist
- [ ] Session creates Pod within 30s
- [ ] WebRTC connects with < 50ms latency
- [ ] 8 concurrent sessions on single GPU
- [ ] Graceful cleanup on session delete
- [ ] Timeout enforcement works
- [ ] TURN relay functions for NAT clients
- [ ] Dashboard displays real-time status

## Performance Targets
| Test | Threshold |
|------|-----------|
| Session startup | < 30s |
| Video latency | < 50ms |
| Concurrent sessions | 8 per GPU |
| Cleanup time | < 10s |
| Operator reconcile | < 100ms |