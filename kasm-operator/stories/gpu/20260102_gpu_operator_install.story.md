---
id: "20260102_gpu_operator_install"
difficulty: "easy"
tags: ["gpu", "nvidia", "helm", "k3s", "operator"]
tech_stack: "NVIDIA GPU Operator, Helm, K3s"
---

# User Story
As a DevOps engineer, I want to install the NVIDIA GPU Operator on K3s, so the cluster can schedule GPU workloads.

# Context & Constraints
**Prerequisites:**
- NVIDIA driver installed on GPU nodes
- containerd runtime with nvidia-container-runtime
- K3s cluster running

**Installation:**
```bash
# Add NVIDIA Helm repo
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# Install GPU Operator
helm install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator --create-namespace \
  --set driver.enabled=false \
  --set toolkit.enabled=true \
  --set devicePlugin.config.name=time-slicing-config
```

**Verification:**
```bash
# Check GPU Operator pods
kubectl get pods -n gpu-operator

# Verify device plugin
kubectl logs -n gpu-operator -l app=nvidia-device-plugin-daemonset

# Check node capacity
kubectl get nodes -o custom-columns=NAME:.metadata.name,GPU:.status.capacity.nvidia\\.com/gpu
```

# Acceptance Criteria
- [ ] **Helm:** Add NVIDIA Helm repository
- [ ] **Install:** Deploy GPU Operator with driver.enabled=false
- [ ] **DaemonSet:** Verify device-plugin DaemonSet running
- [ ] **Capacity:** Node shows nvidia.com/gpu capacity
- [ ] **Test Pod:** Run nvidia-smi test pod successfully
