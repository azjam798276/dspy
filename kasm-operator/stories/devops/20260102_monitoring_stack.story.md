---
id: "20260102_monitoring_stack"
difficulty: "medium"
tags: ["devops", "prometheus", "grafana", "metrics", "monitoring"]
tech_stack: "Prometheus, Grafana, ServiceMonitor"
---

# User Story
As a DevOps engineer, I want Prometheus metrics and Grafana dashboards for the VDI platform, so I can monitor session health and GPU utilization.

# Context & Constraints
**Operator Metrics:**
```go
var (
    sessionsTotal = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "vdi_sessions_total",
            Help: "Total VDI sessions by phase",
        },
        []string{"phase"},
    )
    sessionDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "vdi_session_duration_seconds",
            Buckets: []float64{60, 300, 900, 1800, 3600},
        },
        []string{"template"},
    )
)
```

**ServiceMonitor:**
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

**Key Dashboards:**
| Panel | Query |
|-------|-------|
| Active Sessions | `sum(vdi_sessions_total{phase="Running"})` |
| Sessions by Template | `sum by (template) (vdi_sessions_total)` |
| GPU Utilization | `avg(DCGM_FI_DEV_GPU_UTIL{pod=~"vdi-.*"})` |
| Session P95 Duration | `histogram_quantile(0.95, vdi_session_duration_seconds_bucket)` |

# Acceptance Criteria
- [ ] **Metrics:** Export vdi_sessions_total and vdi_session_duration
- [ ] **ServiceMonitor:** Create for Prometheus Operator scraping
- [ ] **DCGM:** Integrate with NVIDIA DCGM exporter for GPU metrics
- [ ] **Dashboard:** Create Grafana dashboard JSON
- [ ] **Alerts:** Define alerting rules for session failures
