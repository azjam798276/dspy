# Technical Design Document (TDD)

## VDI Operator Implementation Details

**Version**: 1.0.0 | **Date**: 2026-01-02 | **Status**: Draft

---

## 1. Overview

This document provides implementation details for the VDI Operator, covering API specifications, controller logic, and integration patterns.

## 2. API Specifications

### 2.1 VDISession CRD Schema

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: vdisessions.vdi.kasm.io
spec:
  group: vdi.kasm.io
  versions:
    - name: v1alpha1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required: [user, template]
              properties:
                user:
                  type: string
                  description: User email or ID
                template:
                  type: string
                  description: Reference to VDITemplate
                resources:
                  type: object
                  properties:
                    gpu:
                      type: integer
                      default: 1
                    memory:
                      type: string
                      default: "4Gi"
                    cpu:
                      type: string
                      default: "2"
                persistence:
                  type: object
                  properties:
                    enabled:
                      type: boolean
                      default: true
                    size:
                      type: string
                      default: "10Gi"
                timeout:
                  type: string
                  default: "8h"
            status:
              type: object
              properties:
                phase:
                  type: string
                  enum: [Pending, Creating, Running, Terminating, Failed]
                podName:
                  type: string
                url:
                  type: string
                startTime:
                  type: string
                  format: date-time
                message:
                  type: string
      additionalPrinterColumns:
        - name: User
          type: string
          jsonPath: .spec.user
        - name: Phase
          type: string
          jsonPath: .status.phase
        - name: URL
          type: string
          jsonPath: .status.url
  scope: Namespaced
  names:
    plural: vdisessions
    singular: vdisession
    kind: VDISession
    shortNames: [vdi]
```

### 2.2 VDITemplate CRD Schema

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: vditemplates.vdi.kasm.io
spec:
  group: vdi.kasm.io
  versions:
    - name: v1alpha1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required: [image]
              properties:
                image:
                  type: string
                displayName:
                  type: string
                description:
                  type: string
                resources:
                  type: object
                  properties:
                    defaultGPU:
                      type: integer
                      default: 1
                    defaultMemory:
                      type: string
                      default: "4Gi"
                    defaultCPU:
                      type: string
                      default: "2"
                env:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                      value:
                        type: string
  scope: Cluster
  names:
    plural: vditemplates
    singular: vditemplate
    kind: VDITemplate
```

## 3. Controller Implementation

### 3.1 VDISession Controller

```go
package controllers

import (
    "context"
    "fmt"
    "time"

    corev1 "k8s.io/api/core/v1"
    "k8s.io/apimachinery/pkg/api/errors"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/apimachinery/pkg/runtime"
    ctrl "sigs.k8s.io/controller-runtime"
    "sigs.k8s.io/controller-runtime/pkg/client"
    "sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

    vdiv1alpha1 "github.com/user/vdi-operator/api/v1alpha1"
)

const (
    sessionFinalizer = "vdi.kasm.io/session-cleanup"
    reconcileInterval = 30 * time.Second
)

type VDISessionReconciler struct {
    client.Client
    Scheme *runtime.Scheme
}

func (r *VDISessionReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    log := ctrl.LoggerFrom(ctx)

    // 1. Fetch the VDISession
    session := &vdiv1alpha1.VDISession{}
    if err := r.Get(ctx, req.NamespacedName, session); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    // 2. Handle deletion
    if !session.DeletionTimestamp.IsZero() {
        return r.handleDeletion(ctx, session)
    }

    // 3. Add finalizer if not present
    if !controllerutil.ContainsFinalizer(session, sessionFinalizer) {
        controllerutil.AddFinalizer(session, sessionFinalizer)
        if err := r.Update(ctx, session); err != nil {
            return ctrl.Result{}, err
        }
    }

    // 4. Fetch template
    template := &vdiv1alpha1.VDITemplate{}
    if err := r.Get(ctx, client.ObjectKey{Name: session.Spec.Template}, template); err != nil {
        session.Status.Phase = "Failed"
        session.Status.Message = fmt.Sprintf("Template not found: %s", session.Spec.Template)
        r.Status().Update(ctx, session)
        return ctrl.Result{}, err
    }

    // 5. Reconcile resources
    if err := r.reconcilePVC(ctx, session); err != nil {
        return ctrl.Result{}, err
    }
    if err := r.reconcilePod(ctx, session, template); err != nil {
        return ctrl.Result{}, err
    }
    if err := r.reconcileService(ctx, session); err != nil {
        return ctrl.Result{}, err
    }
    if err := r.reconcileIngress(ctx, session); err != nil {
        return ctrl.Result{}, err
    }

    // 6. Update status
    r.updateStatus(ctx, session)

    // 7. Check timeout
    if r.isExpired(session) {
        log.Info("Session expired, deleting", "session", session.Name)
        return ctrl.Result{}, r.Delete(ctx, session)
    }

    return ctrl.Result{RequeueAfter: reconcileInterval}, nil
}
```

### 3.2 Pod Template Generation

```go
func (r *VDISessionReconciler) buildPod(session *vdiv1alpha1.VDISession, 
    template *vdiv1alpha1.VDITemplate) *corev1.Pod {
    
    labels := map[string]string{
        "app.kubernetes.io/name":       "vdi-session",
        "app.kubernetes.io/instance":   session.Name,
        "vdi.kasm.io/user":             session.Spec.User,
    }

    return &corev1.Pod{
        ObjectMeta: metav1.ObjectMeta{
            Name:      session.Name,
            Namespace: session.Namespace,
            Labels:    labels,
        },
        Spec: corev1.PodSpec{
            Containers: []corev1.Container{{
                Name:  "selkies",
                Image: template.Spec.Image,
                Env: []corev1.EnvVar{
                    {Name: "SELKIES_ENCODER", Value: "nvh264enc"},
                    {Name: "SELKIES_BASIC_AUTH_PASSWORD", Value: generatePassword()},
                    {Name: "DISPLAY", Value: ":0"},
                },
                Resources: corev1.ResourceRequirements{
                    Limits: corev1.ResourceList{
                        "nvidia.com/gpu":       resource.MustParse(fmt.Sprintf("%d", session.Spec.Resources.GPU)),
                        corev1.ResourceMemory:  resource.MustParse(session.Spec.Resources.Memory),
                        corev1.ResourceCPU:     resource.MustParse(session.Spec.Resources.CPU),
                    },
                },
                Ports: []corev1.ContainerPort{
                    {Name: "http", ContainerPort: 8080},
                },
                VolumeMounts: []corev1.VolumeMount{
                    {Name: "home", MountPath: "/home/user"},
                    {Name: "shm", MountPath: "/dev/shm"},
                },
            }},
            Volumes: []corev1.Volume{
                {
                    Name: "home",
                    VolumeSource: corev1.VolumeSource{
                        PersistentVolumeClaim: &corev1.PersistentVolumeClaimVolumeSource{
                            ClaimName: fmt.Sprintf("vdi-data-%s", session.Name),
                        },
                    },
                },
                {
                    Name: "shm",
                    VolumeSource: corev1.VolumeSource{
                        EmptyDir: &corev1.EmptyDirVolumeSource{
                            Medium: corev1.StorageMediumMemory,
                        },
                    },
                },
            },
        },
    }
}
```

## 4. Traefik IngressRoute Generation

```go
func (r *VDISessionReconciler) buildIngressRoute(session *vdiv1alpha1.VDISession) *unstructured.Unstructured {
    username := sanitizeUsername(session.Spec.User)
    host := fmt.Sprintf("%s.vdi.example.com", username)

    return &unstructured.Unstructured{
        Object: map[string]interface{}{
            "apiVersion": "traefik.io/v1alpha1",
            "kind":       "IngressRoute",
            "metadata": map[string]interface{}{
                "name":      session.Name,
                "namespace": session.Namespace,
            },
            "spec": map[string]interface{}{
                "entryPoints": []string{"websecure"},
                "routes": []map[string]interface{}{
                    {
                        "match": fmt.Sprintf("Host(`%s`)", host),
                        "kind":  "Rule",
                        "services": []map[string]interface{}{
                            {
                                "name": session.Name,
                                "port": 8080,
                            },
                        },
                    },
                },
                "tls": map[string]interface{}{
                    "certResolver": "letsencrypt",
                },
            },
        },
    }
}
```

## 5. GPU Time-Slicing Configuration

### 5.1 ConfigMap

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

### 5.2 ClusterPolicy Patch

```bash
kubectl patch clusterpolicy/cluster-policy \
  -n gpu-operator --type merge \
  -p '{"spec":{"devicePlugin":{"config":{"name":"time-slicing-config"}}}}'
```

## 6. Coturn TURN Server

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coturn
  namespace: vdi-operator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: coturn
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
          - --user=vdi:secret
        env:
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.hostIP
```

## 7. Monitoring & Metrics

### 7.1 Prometheus Metrics

```go
var (
    sessionsTotal = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "vdi_sessions_total",
            Help: "Total number of VDI sessions by phase",
        },
        []string{"phase"},
    )
    
    sessionDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "vdi_session_duration_seconds",
            Help:    "Duration of VDI sessions",
            Buckets: []float64{60, 300, 900, 1800, 3600, 7200, 14400},
        },
        []string{"template"},
    )
)
```

### 7.2 ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: vdi-operator
spec:
  selector:
    matchLabels:
      app: vdi-operator
  endpoints:
  - port: metrics
    interval: 30s
```

## 8. Testing Strategy

### 8.1 Unit Tests

```go
func TestBuildPod(t *testing.T) {
    r := &VDISessionReconciler{}
    session := &vdiv1alpha1.VDISession{
        Spec: vdiv1alpha1.VDISessionSpec{
            User:     "alice@example.com",
            Template: "ubuntu-desktop",
            Resources: vdiv1alpha1.ResourceSpec{
                GPU:    1,
                Memory: "4Gi",
            },
        },
    }
    template := &vdiv1alpha1.VDITemplate{
        Spec: vdiv1alpha1.VDITemplateSpec{
            Image: "selkies:latest",
        },
    }

    pod := r.buildPod(session, template)

    assert.Equal(t, session.Name, pod.Name)
    assert.Equal(t, "selkies:latest", pod.Spec.Containers[0].Image)
    assert.Equal(t, "1", pod.Spec.Containers[0].Resources.Limits["nvidia.com/gpu"])
}
```

### 8.2 Integration Tests

```go
func TestSessionLifecycle(t *testing.T) {
    ctx := context.Background()
    
    // Create session
    session := &vdiv1alpha1.VDISession{...}
    Expect(k8sClient.Create(ctx, session)).To(Succeed())

    // Wait for Running
    Eventually(func() string {
        k8sClient.Get(ctx, client.ObjectKeyFromObject(session), session)
        return session.Status.Phase
    }, timeout).Should(Equal("Running"))

    // Verify Pod exists
    pod := &corev1.Pod{}
    Expect(k8sClient.Get(ctx, client.ObjectKey{
        Name:      session.Name,
        Namespace: session.Namespace,
    }, pod)).To(Succeed())

    // Delete session
    Expect(k8sClient.Delete(ctx, session)).To(Succeed())

    // Verify cleanup
    Eventually(func() bool {
        err := k8sClient.Get(ctx, client.ObjectKeyFromObject(pod), pod)
        return errors.IsNotFound(err)
    }, timeout).Should(BeTrue())
}
```

## 9. Directory Structure

```
vdi-operator/
├── api/
│   └── v1alpha1/
│       ├── vdisession_types.go
│       ├── vditemplate_types.go
│       └── groupversion_info.go
├── controllers/
│   ├── vdisession_controller.go
│   ├── vdisession_controller_test.go
│   └── suite_test.go
├── config/
│   ├── crd/
│   │   └── bases/
│   ├── rbac/
│   └── manager/
├── charts/
│   └── vdi-operator/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── Dockerfile
├── Makefile
└── main.go
```

## 10. Build & Deploy

```bash
# Generate CRDs
make manifests

# Build image
make docker-build IMG=vdi-operator:v0.1.0

# Deploy to cluster
make deploy IMG=vdi-operator:v0.1.0

# Run locally for dev
make run
```
