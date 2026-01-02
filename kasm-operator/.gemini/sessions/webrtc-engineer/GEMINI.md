# WebRTC Streaming: Selkies-GStreamer and Low-Latency Video

## Core Principles
1. **Latency Over Bandwidth:** Prioritize <50ms glass-to-glass latency. Enforce `preset=low-latency-hq` and `bframes=0` in GStreamer pipelines.
2. **Hardware-First Strategy:** Mandate `nvh264enc`. Only fallback to `x264enc` if `nvidia-smi` reports no available devices or drivers.
3. **Resilient Connectivity:** Mandatory TURN (UDP 3478) for all production sessions to ensure 100% NAT traversal success.
4. **Security Protocol:** Non-root execution (UID 1000). Generate unique `SELKIES_BASIC_AUTH_PASSWORD` per `VDISession` and inject via Kubernetes Secrets.

## Selkies-GStreamer Configuration
**Recommended Image:** `ghcr.io/selkies-project/selkies-gstreamer/gst-web:latest`

```yaml
# Mandatory Environment Variables
SELKIES_ENCODER: "nvh264enc"
SELKIES_ENABLE_RESIZE: "true"
SELKIES_BASIC_AUTH_PASSWORD: "${GENERATED_PASSWORD}"
DISPLAY: ":0"
PULSE_SERVER: "/run/pulse/native"
```

## Pod Specification Constraints
- **Labels:** Must include `vdi.kasm.io/session-type: desktop` for `NetworkPolicy` compatibility.
- **Resource Parity:** `limits.nvidia.com/gpu` MUST match `requests.nvidia.com/gpu` (default: 1) for deterministic time-slice scheduling.
- **Shared Memory:** Mount `emptyDir` with `medium: Memory` to `/dev/shm` (Size: 2Gi) for frame buffer performance.
- **Direct Hardware Access:** HostPath mount `/dev/dri` to `/dev/dri` is mandatory for NVENC hardware acceleration.
- **Persistence:** User home directory must be mounted to `/home/user` from a managed `PersistentVolumeClaim`.

## GStreamer Low-Latency Pipeline
```bash
# Reference for implementation in VDITemplate or Pod Specs
gst-launch-1.0 ximagesrc show-pointer=true ! videoconvert ! \
    nvh264enc \
        preset=low-latency-hq \
        rc-mode=cbr \
        bitrate=8000 \
        gop-size=30 \
        bframes=0 \
        aud=false ! \
    rtph264pay config-interval=1 pt=96 ! \
    webrtcbin name=sendrecv bundle-policy=max-bundle
```

## Networking & Traefik Ingress
- **IngressRoute:** Match `HostRegexp` `{user:[a-z0-9-]+}.vdi.example.com` on the `websecure` entryPoint.
- **WebSocket:** Explicitly support `Upgrade: websocket` for the signaling channel on port 8080.
- **TURN:** Configure `webrtcbin` with Coturn: `stun://vdi.example.com:3478` and `turn://vdi:<secret>@vdi.example.com:3478`.

## Validation & Verification (Reflective Loop)
- **Check 1 (GPU Availability):** Execute `nvidia-smi` inside the pod. If it fails, log "GPU_INIT_ERROR" and transition session to `Failed`.
- **Check 2 (Encoder Presence):** `gst-inspect-1.0 nvh264enc` must return status 0.
- **Check 3 (Streaming Stats):** Monitor `chrome://webrtc-internals` for `framesDecoded > 0` and `jitter < 20ms`.
- **Check 4 (Latency SLO):** Target glass-to-glass latency is 50ms. If >100ms, reduce resolution or bitrate dynamically.

## Fallback Logic
1. Attempt `nvh264enc` (Hardware GPU).
2. If hardware init fails, attempt `x264enc` with `preset=ultrafast` and `tune=zerolatency`.
3. If CPU usage exceeds 80% on the host, throttle session frame rate to 30 FPS.