---
id: "pod_security_context_nonroot"
source: "https://github.com/Bokomoko/vscodetunnelpod"
tags: ["security", "pod-security", "non-root", "securityContext", "hardening"]
---

## Problem
Configure a Kasm Workspaces deployment with hardened security context: non-root execution, read-only root filesystem, dropped capabilities, and seccomp profile. The configuration must mount emptyDir volumes for required writable paths (/tmp, /var/run, /.cache) to allow the application to function while maintaining immutability.

## Solution
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kasm-workspace
  namespace: kasm
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kasm-workspace
  template:
    metadata:
      labels:
        app: kasm-workspace
        tier: application
    spec:
      # Pod-level security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000    # Kasm user UID
        runAsGroup: 1000   # Kasm group GID
        fsGroup: 1000      # File system group
        seccompProfile:
          type: RuntimeDefault
      
      containers:
      - name: kasm-workspace
        image: kasmweb/desktop:1.14.0
        
        # Container-level security context
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true  # CRITICAL: Immutable container
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
              - ALL              # Drop all capabilities
            add:
              - NET_BIND_SERVICE # Only if binding to port <1024
        
        ports:
        - containerPort: 6901
          name: vnc
          protocol: TCP
        - containerPort: 8443
          name: https
          protocol: TCP
        
        # Required volume mounts for readOnlyRootFilesystem
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: var-run
          mountPath: /var/run
        - name: kasm-data
          mountPath: /home/kasm
        - name: cache
          mountPath: /.cache
        - name: config
          mountPath: /.config
        
        env:
        - name: VNC_PW
          valueFrom:
            secretKeyRef:
              name: kasm-secrets
              key: vnc-password
        
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      
      # Volumes for writable paths (readOnlyRootFilesystem requirement)
      volumes:
      - name: tmp
        emptyDir:
          sizeLimit: 500Mi
      - name: var-run
        emptyDir:
          sizeLimit: 100Mi
      - name: cache
        emptyDir:
          sizeLimit: 200Mi
      - name: config
        emptyDir:
          sizeLimit: 100Mi
      - name: kasm-data
        persistentVolumeClaim:
          claimName: kasm-workspace-pvc
```

## Key Techniques
- runAsNonRoot prevents container escape vulnerabilities
- readOnlyRootFilesystem blocks runtime tampering and malware persistence
- capabilities.drop ALL removes all Linux capabilities by default
- seccompProfile RuntimeDefault restricts dangerous syscalls
- emptyDir volumes with sizeLimit for /tmp, /var/run, /.cache
- fsGroup ensures shared volume access for non-root user
