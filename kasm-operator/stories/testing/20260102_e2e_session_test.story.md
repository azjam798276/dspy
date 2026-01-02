---
id: "20260102_e2e_session_test"
difficulty: "hard"
tags: ["testing", "e2e", "kubectl", "webrtc", "browser"]
tech_stack: "Bash, kubectl, Playwright, WebRTC"
---

# User Story
As a QA engineer, I want end-to-end tests that verify complete session flow from creation to WebRTC streaming, so I can validate the entire platform works.

# Context & Constraints
**E2E Test Flow:**
```
1. Create VDISession via kubectl
2. Wait for Running status
3. Extract session URL
4. Connect browser to URL
5. Verify WebRTC stream
6. Terminate session
7. Verify cleanup
```

**Test Script:**
```bash
#!/bin/bash
# Create session
kubectl apply -f - <<EOF
apiVersion: vdi.kasm.io/v1alpha1
kind: VDISession
metadata:
  name: e2e-test-session
spec:
  user: e2e@test.com
  template: ubuntu-desktop
EOF

# Wait for Running
kubectl wait vdisession/e2e-test-session \
  --for=jsonpath='{.status.phase}'=Running \
  --timeout=60s

# Get URL
URL=$(kubectl get vdisession e2e-test-session -o jsonpath='{.status.url}')

# Browser test with Playwright
npx playwright test --config=e2e/playwright.config.ts
```

**WebRTC Validation:**
```typescript
test('WebRTC stream connects', async ({ page }) => {
  await page.goto(sessionUrl);
  await page.fill('#password', sessionPassword);
  await page.click('#connect');
  
  // Wait for video element
  const video = await page.waitForSelector('video', { state: 'visible' });
  expect(await video.getAttribute('srcObject')).toBeTruthy();
});
```

# Acceptance Criteria
- [ ] **Create:** kubectl creates VDISession successfully
- [ ] **Wait:** Session reaches Running within 60s
- [ ] **URL:** status.url is accessible HTTPS endpoint
- [ ] **Auth:** Basic auth login works
- [ ] **Stream:** WebRTC video element receives frames
- [ ] **Latency:** Measure and log stream latency
- [ ] **Cleanup:** Session resources deleted after test
