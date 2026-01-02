---
id: "20260102_session_lifecycle_test"
difficulty: "hard"
tags: ["testing", "integration", "envtest", "controller", "ginkgo"]
tech_stack: "Go, envtest, Ginkgo, Gomega"
---

# User Story
As a QA engineer, I want integration tests for VDISession lifecycle, so I can verify the controller correctly creates and cleans up resources.

# Context & Constraints
**Test Setup:**
```go
var _ = BeforeSuite(func() {
    testEnv = &envtest.Environment{
        CRDDirectoryPaths: []string{"config/crd/bases"},
    }
    cfg, err := testEnv.Start()
    Expect(err).NotTo(HaveOccurred())
    
    k8sClient, err = client.New(cfg, client.Options{})
    Expect(err).NotTo(HaveOccurred())
})
```

**Test Cases:**
| Scenario | Expected Result |
|----------|-----------------|
| Create VDISession | Pod, PVC, Service, Ingress created |
| Session Running | Status.phase = Running, URL set |
| Delete VDISession | All owned resources cleaned up |
| Invalid Template | Status.phase = Failed, message set |
| Session Timeout | Auto-deleted after timeout |

**Assertions:**
```go
Eventually(func() string {
    k8sClient.Get(ctx, key, session)
    return session.Status.Phase
}, timeout).Should(Equal("Running"))
```

# Acceptance Criteria
- [ ] **Suite Setup:** Initialize envtest with CRDs
- [ ] **Create Test:** Verify Pod created with correct image
- [ ] **Status Test:** Verify status updated to Running
- [ ] **URL Test:** Verify status.url matches expected pattern
- [ ] **Delete Test:** Verify cleanup on session deletion
- [ ] **Finalizer Test:** Verify finalizer prevents immediate deletion
- [ ] **Template Error:** Verify Failed status on missing template
