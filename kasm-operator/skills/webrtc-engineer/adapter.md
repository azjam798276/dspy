# WebRTC Streaming: Selkies-GStreamer and Low-Latency Video

## Core Principles
1. **Latency First:** Optimize for <50ms glass-to-glass latency over throughput.
2. **Hardware Encoding:** Always use NVENC when GPU available; fallback to software only as last resort.
3. **NAT Traversal:** Assume restrictive networks; TURN server is mandatory for production.
4. **Adaptive Bitrate:** Respond to network conditions with bitrate/resolution adjustments.

## Selkies-GStreamer Configuration
**Recommended Image:** `ghcr.io/selkies-project/selkies-gstreamer/gst-web:latest`

```yaml
# Critical environment variables
SELKIES_ENCODER: "nvh264enc"      # Use NVIDIA hardware encoder
SELKIES_ENABLE_RESIZE: "true"     # Allow client resolution changes
SELKIES_BASIC_AUTH_PASSWORD: ""   # MANDATORY: Generate random password per session
DISPLAY: ":0"                     # X11 display number
PULSE_SERVER: "/run/pulse/native" # Audio socket
```

## GStreamer Pipeline Architecture
```
X11 Display → ximagesrc → videoconvert → nvh264enc → rtph264pay → webrtcbin → UDP
                                              ↓
                                         nvenc params:
                                         - preset=low-latency-hq
                                         - rc-mode=cbr
                                         - bitrate=8000
```

## Encoder Settings for Low Latency
```bash
# NVENC optimal settings
gst-launch-1.0 ximagesrc ! nvh264enc \
    preset=low-latency-hq \
    rc-mode=cbr \
    bitrate=8000 \
    gop-size=30 \
    bframes=0 \
    ! rtph264pay ! webrtcbin
```

## TURN Server Configuration (Coturn)
```bash
# Required arguments
--external-ip=$(POD_IP)
--listening-port=3478
--min-port=49152
--max-port=65535
--realm=vdi.example.com
--user=vdi:$(TURN_SECRET)
--lt-cred-mech           # Long-term credentials
--fingerprint            # STUN fingerprint
```

## WebRTC Signaling
- Use WebSocket for signaling channel
- Exchange SDP offers/answers for codec negotiation
- ICE candidates gathered from STUN, relayed via TURN if direct fails
- Trickle ICE for faster connection establishment

## Pod Resource Requirements
```yaml
resources:
  limits:
    nvidia.com/gpu: "1"    # Time-slice allocation
    memory: "4Gi"          # Desktop + encoding overhead
  requests:
    cpu: "1"               # Minimum for smooth desktop
ports:
  - containerPort: 8080
    name: http
```

## Volume Mounts
```yaml
volumes:
  - name: shm
    emptyDir:
      medium: Memory       # Crucial for performance
      sizeLimit: "2Gi"     # Shared memory for X11/video
  - name: dri
    hostPath:
      path: /dev/dri       # GPU device access
```

## Debugging & Monitoring
- Check encoder: `GST_DEBUG=nvh264enc:5 gst-inspect-1.0 nvh264enc`
- WebRTC stats: `chrome://webrtc-internals/`
- Verify NVENC: `nvidia-smi` shows encoder utilization
- Network: monitor TURN allocations via Coturn logs

## Performance Targets
| Metric | Threshold |
|--------|-----------|
| Video latency | < 50ms |
| Frame rate | 60 FPS @ 1080p |
| Bitrate | 4-12 Mbps adaptive |
| TURN relay | 100% NAT success |

## Fallback Strategy
```
Try: nvh264enc (GPU)
 ├─ Success → Continue
 └─ Fail → Try: x264enc (CPU, preset=ultrafast)
           ├─ Success → Log warning, continue
           └─ Fail → Session Failed status
```

## Demonstrations

### Example 1
**Problem:**
---
id: "20260102_vdisession_crd"
difficulty: "medium"
tags: ["kubernetes", "crd", "openapi", "kubebuilder", "validation"]
tech_stack: "Go 1.21, kubebuilder, OpenAPI v3"
---

# User Story
As a platform engineer, I want a VDISession Custom Resource Definition with proper validation and printer columns, so users can create desktop sessions using kubectl.

# Context & Constraints
**CRD Specification:**
```yaml
apiVersion: vdi.kasm.io/v1alpha1
kind: VDISession
metadata:
  name: alice-desktop
spec:
  user: alice@example.com
  template: ubuntu-desktop
  resources:
    gpu: 1
    memory: "4Gi"
  timeout: "8h"
status:
  phase: Running
  url: https://alice.vdi.example.com
```

**Required Fields:**
| Field | Type | Validation |
|-------|------|------------|
| spec.user | string | Required, email pat

**Solution:**
{
  "session_id": "7211e0de-dfb3-4d24-9ee2-1cad98ebb5bd",
  "response": "Based on the User Story and TDD, I need to define the `VDISession` Custom Resource Definition (CRD) in Go using Kubebuilder markers.\n\n**Reasoning:**\n1.  **Directory Structure**: I will initialize the `operator` directory and create the `api/v1alpha1` package to house the API definitions, adhering to the standard Kubebuilder layout.\n2.  **API Registration (`groupversion_info.go`)**: I will create this file to register the `vdi.kasm.io` group and `v1alpha1` version with the `SchemeBuilder`, which is essential for the controller to recognize these types.\n3.  **CRD Definition (`vdisession_types.go`)**: I will define the `VDISession` struct and its sub-structs `VDISessionSpec` and `VDISessionStatus`.\n    *   **Validation**: I will apply `+kubebuilder:validation` markers. `User` will be required and validated with a regex pattern. `Resources.GPU` will have a minimum of 1.\n    *   **Defaults**: I will set default values for `Resources` (GPU: 1, Memory: \"4Gi\") and `Timeout` (\"8h\") using `+kubebuilder:default`.\n    *   **Status Enum**: The `Phase` field will be restricted to a specific set of states (Pending, Creating, Running, Terminating, Failed).\n    *   **Printer Columns**: I will add `+kubebuilder:printcolumn` markers to display `User`, `Phase`, and `URL` in `kubectl get vdisession` output.\n    *   **ShortName**: I will register `vdi` as the shortname.\n4.  **Module Initialization (`go.mod`)**: I will create a `go.mod` file to define the module `github.com/user/vdi-operator`, ensuring the Go tooling works correctly.\n\n```json\n{\n  \"reasoning\": \"I have designed the VDISession API to meet the strict validation and observability requirements. \\n\\n1. **Validation & Defaults**: I implemented the `VDISessionSpec` with `+kubebuilder:validation:Required` for the `User` and `Template` fields. I used a regex pattern `^\\\\S+@\\\\S+\\\\.\\\\S+$` for the `User` email to ensure data integrity. For `Resources`, I used a nested `ResourceSpec` struct with `+kubebuilder:default` values (GPU: 1, Memory: \\\"4Gi\\\") and a minimum constraint on GPU to prevent invalid configurations.\\n2. **Status Management**: The `VDISessionStatus` uses a strict Enum for `Phase` to guarantee the state machine's determinism. I also included `StartTime` and `URL` fields to support the required printer columns.\\n3. **Observability**: I added `+kubebuilder:printcolumn` markers to expose critical session info (User, Phase, URL) directly in `kubectl get` output, and registered the `vdi` shortname for CLI convenience.\\n4. **Structure**: I organized the code into the standard `api/v1alpha1` package structure with proper group registration.\",\n  \"code_changes\": {\n    \"operator/go.mod\": \"module github.com/user/vdi-operator\\n\\ngo 1.21\\n\",\n    \"operator/api/v1alpha1/groupversion_info.go\": \"/*\\nCopyright 2026 The Kasm Operator Authors.\\n*/\\n\\n// Package v1alpha1 contains API Schema de

---

### Example 2
**Problem:**
---
id: "20260102_gpu_time_slicing"
difficulty: "medium"
tags: ["gpu", "nvidia", "time-slicing", "device-plugin", "k8s"]
tech_stack: "NVIDIA GPU Operator, K3s, ConfigMap"
---

# User Story
As a GPU engineer, I want to configure NVIDIA time-slicing on K3s, so multiple VDI sessions can share a single GPU efficiently.

# Context & Constraints
**Time-Slicing Configuration:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: time-slicing-config
  namespace: gpu-operator
data:
  any: |-
    version: v1
    flags:
      migStrategy: none
    sharing:
      timeSlicing:
        renameByDefault: false
        failRequestsGreaterThanOne: false
        resources:
        - name: nvidia.com/gpu
          replicas: 8
```

**ClusterPolicy Patch:**
```bash
kubectl patch clusterpolicy/cluster-polic

**Solution:**
{
  "session_id": "0d18e13e-06c9-4336-8eb4-5165b303e2f8",
  "response": "Reasoning:\nTo enable NVIDIA GPU time-slicing for the Kasm Operator, we need to define a sharing configuration that splits a single physical GPU into multiple schedulable units (replicas). Based on the requirements, we target 8 replicas per GPU.\n\nThe implementation involves two key artifacts:\n1.  **`manifests/gpu-time-slicing.yaml`**: A Kubernetes `ConfigMap` that defines the time-slicing policy (8 replicas for `nvidia.com/gpu`). This file adheres to the schema expected by the NVIDIA GPU Operator.\n2.  **`scripts/configure_gpu_slicing.sh`**: A shell script to automate the deployment. It first applies the ConfigMap and then patches the `ClusterPolicy` of the GPU Operator to reference this new configuration. This ensures the changes are applied consistently and documents the necessary imperative commands.\n\nThis approach satisfies the acceptance criteria by creating the config, providing the patch mechanism, and setting up the system for the required density.\n\n```json\n[\n  {\n    \"action\": \"write\",\n    \"path\": \"manifests/gpu-time-slicing.yaml\",\n    \"content\": \"apiVersion: v1\\nkind: ConfigMap\\nmetadata:\\n  name: time-slicing-config\\n  namespace: gpu-operator\\ndata:\\n  any: |-\\n    version: v1\\n    flags:\\n      migStrategy: none\\n    sharing:\\n      timeSlicing:\\n        renameByDefault: false\\n        failRequestsGreaterThanOne: false\\n        resources:\\n        - name: nvidia.com/gpu\\n          replicas: 8\"\n  },\n  {\n    \"action\": \"write\",\n    \"path\": \"scripts/configure_gpu_slicing.sh\",\n    \"content\": \"#!/bin/bash\\nset -e\\n\\n# 1. Apply the Time-Slicing ConfigMap\\necho \\\"Applying time-slicing configuration...\\\"\\nkubectl apply -f manifests/gpu-time-slicing.yaml\\n\\n# 2. Patch the GPU Operator ClusterPolicy\\n# This instructs the Operator to use the config we just applied\\necho \\\"Patching GPU Operator ClusterPolicy...\\\"\\nkubectl patch clusterpolicy/cluster-policy \\\\\\n  -n gpu-operator --type merge \\\\\\n  -p '{\\\"spec\\\":{\\\"devicePlugin\\\":{\\\"config\\\":{\\\"name\\\":\\\"time-slicing-config\\\"}}}}'\\n\\n# 3. Verification Instructions\\necho \\\"Configuration applied successfully.\\\"\\necho \\\"To verify, run: kubectl describe node <node-name> | grep nvidia.com/gpu\\\"\\necho \\\"Expected output: nvidia.com/gpu: 8\\\"\"\n  }\n]\n```",
  "stats": {
    "models": {
      "gemini-2.5-flash-lite": {
        "api": {
          "totalRequests": 1,
          "totalErrors": 0,
          "totalLatencyMs": 2513
        },
        "tokens": {
          "input": 5781,
          "prompt": 5781,
          "candidates": 83,
          "total": 6234,
          "cached": 0,
          "thoughts": 370,
          "tool": 0
        }
      },
      "gemini-3-pro-preview": {
        "api": {
          "totalRequests": 5,
          "totalErrors": 0,
          "totalLatencyMs": 52309
        },
        "tokens": {

---

### Example 3
**Problem:**
---
id: "20260102_vditemplate_crd"
difficulty: "easy"
tags: ["kubernetes", "crd", "template", "kubebuilder"]
tech_stack: "Go 1.21, kubebuilder"
---

# User Story
As a platform admin, I want a VDITemplate CRD to define available desktop environments, so users can choose from pre-configured templates.

# Context & Constraints
**CRD Specification:**
```yaml
apiVersion: vdi.kasm.io/v1alpha1
kind: VDITemplate
metadata:
  name: ubuntu-desktop
spec:
  image: ghcr.io/selkies-project/selkies-gstreamer/gst-web:latest
  displayName: "Ubuntu 22.04 Desktop"
  description: "Full Ubuntu desktop with GPU acceleration"
  resources:
    defaultGPU: 1
    defaultMemory: "4Gi"
    defaultCPU: "2"
  env:
    - name: SELKIES_ENCODER
      value: "nvh264enc"
```

**Fields:**
| Field | Type | Description |
|-----

**Solution:**
{
  "session_id": "d9007d7c-be78-49fd-bc91-a41552fd85d0",
  "response": "Based on the requirements, I have designed the Go structs for the `VDITemplate` CRD. The implementation follows the Kubebuilder patterns, using markers for validation, defaults, and scope definition.\n\n```json\n{\n  \"reasoning\": \"Implemented the VDITemplate CRD by defining the Go structs in `vditemplate_types.go` and the group info in `groupversion_info.go`. \\n\\nKey design decisions:\\n1.  **Cluster Scope:** Used `//+kubebuilder:resource:scope=Cluster` marker as requested, since templates should be available globally.\\n2.  **Validation:** Enforced `Image` as a required field using `//+kubebuilder:validation:Required`.\\n3.  **Defaults:** Applied `//+kubebuilder:default` markers to resource fields (GPU: 1, Memory: 4Gi, CPU: 2) to simplify usage.\\n4.  **Structure:** Separated `Resources` into `VDITemplateResourceSpec` and `Env` into `EnvVar` structs for clarity and reusability.\",\n  \"changes\": [\n    {\n      \"path\": \"operator/api/v1alpha1/groupversion_info.go\",\n      \"content\": \"/*\\nCopyright 2026.\\n\\nLicensed under the Apache License, Version 2.0 (the \\\"License\\\");\\nyou may not use this file except in compliance with the License.\\nYou may obtain a copy of the License at\\n\\n    http://www.apache.org/licenses/LICENSE-2.0\\n\\nUnless required by applicable law or agreed to in writing, software\\ndistributed under the License is distributed on an \\\"AS IS\\\" BASIS,\\nWITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\\nSee the License for the specific language governing permissions and\\nlimitations under the License.\\n*/\\n\\n// Package v1alpha1 contains API Schema definitions for the vdi v1alpha1 API group\\n// +kubebuilder:object:generate=true\\n// +groupName=vdi.kasm.io\\npackage v1alpha1\\n\\nimport (\\n\\t\\\"k8s.io/apimachinery/pkg/runtime/schema\\\"\\n\\t\\\"sigs.k8s.io/controller-runtime/pkg/scheme\\\"\\n)\\n\\nvar (\\n\\t// GroupVersion is group version used to register these objects\\n\\tGroupVersion = schema.GroupVersion{Group: \\\"vdi.kasm.io\\\", Version: \\\"v1alpha1\\\"}\\n\\n\\t// SchemeBuilder is used to add go types to the GroupVersionKind scheme\\n\\tSchemeBuilder = &scheme.Builder{GroupVersion: GroupVersion}\\n\\n\\t// AddToScheme adds the types in this group-version to the given scheme.\\n\\tAddToScheme = SchemeBuilder.AddToScheme\\n)\\n\"\n    },\n    {\n      \"path\": \"operator/api/v1alpha1/vditemplate_types.go\",\n      \"content\": \"/*\\nCopyright 2026.\\n\\nLicensed under the Apache License, Version 2.0 (the \\\"License\\\");\\nyou may not use this file except in compliance with the License.\\nYou may obtain a copy of the License at\\n\\n    http://www.apache.org/licenses/LICENSE-2.0\\n\\nUnless required by applicable law or agreed to in writing, software\\ndistributed under the License is distributed on an \\\"AS IS\\\" BASIS,\\nWITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or im

---

### Example 4
**Problem:**
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
| Create VDISession | Pod, PVC, Service

**Solution:**
{
  "session_id": "12ddd292-1b40-453e-b942-a98bece2116f",
  "response": "```json\n{\n  \"reasoning\": \"The current environment is missing the `operator` directory, `go.mod`, and `package.json` required to run the requested integration tests. To satisfy the User Story and ensure `npm test` (via the adapter) can execute the Go tests, I will generate a comprehensive Git patch. This patch scaffolds the project structure, including: 1) A `package.json` bridge to invoke Go tests. 2) The `operator` module definition (`go.mod`). 3) The `VDISession` API type definitions and Scheme registration. 4) The `envtest` suite setup in `suite_test.go`. 5) The complete integration test suite in `vdisession_controller_test.go` covering all acceptance criteria. 6) The necessary CRD manifest for the test environment.\",\n  \"code_patch\": \"diff --git a/package.json b/package.json\\nnew file mode 100644\\nindex 0000000..e69de29\\n--- /dev/null\\n+++ b/package.json\\n@@ -0,0 +1,5 @@\\n+{\\n+  \\\"scripts\\\": {\\n+    \\\"test\\\": \\\"cd operator && go mod tidy && go test ./controllers/...\\\"\\n+  }\\n+}\\ndiff --git a/operator/go.mod b/operator/go.mod\\nnew file mode 100644\\nindex 0000000..e69de29\\n--- /dev/null\\n+++ b/operator/go.mod\\n@@ -0,0 +1,10 @@\\n+module github.com/kasm/kasm-operator/operator\\n+\\n+go 1.21\\n+\\n+require (\\n+    github.com/onsi/ginkgo/v2 v2.11.0\\n+    github.com/onsi/gomega v1.27.8\\n+    k8s.io/apimachinery v0.27.2\\n+    k8s.io/client-go v0.27.2\\n+    sigs.k8s.io/controller-runtime v0.15.0\\n+)\\ndiff --git a/operator/api/v1alpha1/groupversion_info.go b/operator/api/v1alpha1/groupversion_info.go\\nnew file mode 100644\\nindex 0000000..e69de29\\n--- /dev/null\\n+++ b/operator/api/v1alpha1/groupversion_info.go\\n@@ -0,0 +1,27 @@\\n+package v1alpha1\\n+\\n+import (\\n+\\t\\\"k8s.io/apimachinery/pkg/runtime/schema\\\"\\n+\\t\\\"sigs.k8s.io/controller-runtime/pkg/scheme\\\"\\n+)\\n+\\n+var (\\n+\\tGroupVersion = schema.GroupVersion{Group: \\\"vdi.kasm.io\\\", Version: \\\"v1alpha1\\\"}\\n+\\tSchemeBuilder = &scheme.Builder{GroupVersion: GroupVersion}\\n+\\tAddToScheme   = SchemeBuilder.AddToScheme\\n+)\\ndiff --git a/operator/api/v1alpha1/vdisession_types.go b/operator/api/v1alpha1/vdisession_types.go\\nnew file mode 100644\\nindex 0000000..e69de29\\n--- /dev/null\\n+++ b/operator/api/v1alpha1/vdisession_types.go\\n@@ -0,0 +1,45 @@\\n+package v1alpha1\\n+\\n+import (\\n+\\tmetav1 \\\"k8s.io/apimachinery/pkg/apis/meta/v1\\\"\\n+)\\n+\\n+type VDISessionSpec struct {\\n+\\tUser     string `json:\\\"user\\\"`\\n+\\tTemplate string `json:\\\"template\\\"`\\n+}\\n+\\n+type VDISessionStatus struct {\\n+\\tPhase   string `json:\\\"phase,omitempty\\\"`\\n+\\tURL     string `json:\\\"url,omitempty\\\"`\\n+\\tMessage string `json:\\\"message,omitempty\\\"`\\n+}\\n+\\n+//+kubebuilder:object:root=true\\n+//+kubebuilder:subresource:status\\n+\\n+type VDISession struct {\\n+\\tmetav1.TypeMeta   `json:\\\",inline\\\"`\\n+\\tmetav1.ObjectMeta `json:\\\"

---
