---
name: webrtc-engineer
description: WebRTC Streaming Engineer for Selkies-GStreamer VDI Platform
---



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