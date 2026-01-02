---
id: "20260102_selkies_pod_template"
difficulty: "medium"
tags: ["webrtc", "selkies", "gstreamer", "nvenc", "pod"]
tech_stack: "GStreamer, NVENC, WebRTC, Kubernetes"
---

# User Story
As a streaming engineer, I want a Selkies-GStreamer pod template with optimal WebRTC settings, so users get low-latency GPU-accelerated desktop streaming.

# Context & Constraints
**Pod Configuration:**
```yaml
containers:
  - name: selkies
    image: ghcr.io/selkies-project/selkies-gstreamer/gst-web:latest
    env:
      - name: SELKIES_ENCODER
        value: "nvh264enc"
      - name: SELKIES_ENABLE_RESIZE
        value: "true"
      - name: DISPLAY
        value: ":0"
    resources:
      limits:
        nvidia.com/gpu: "1"
        memory: "4Gi"
    ports:
      - containerPort: 8080
        name: http
```

**Volume Mounts:**
| Mount | Path | Purpose |
|-------|------|---------|
| home | /home/user | User data (PVC) |
| shm | /dev/shm | Shared memory (emptyDir) |

**Environment Variables:**
| Variable | Value | Purpose |
|----------|-------|---------|
| SELKIES_ENCODER | nvh264enc | NVIDIA hardware encoding |
| SELKIES_ENABLE_RESIZE | true | Client resolution change |
| SELKIES_BASIC_AUTH_PASSWORD | (secret) | Session auth |
| DISPLAY | :0 | X11 display |

**Performance Targets:**
| Metric | Threshold |
|--------|-----------|
| Video latency | < 50ms |
| Frame rate | 60 FPS |
| Bitrate | 4-12 Mbps |

# Acceptance Criteria
- [ ] **Image:** Use Selkies-GStreamer image with NVENC support
- [ ] **GPU:** Request nvidia.com/gpu: 1 resource
- [ ] **Env:** Set SELKIES_ENCODER=nvh264enc for hardware encoding
- [ ] **Volumes:** Mount /dev/shm as emptyDir with Memory medium
- [ ] **Port:** Expose HTTP port 8080
- [ ] **Security:** Generate random password per session
- [ ] **Fallback:** Document CPU encoder fallback (x264enc)
