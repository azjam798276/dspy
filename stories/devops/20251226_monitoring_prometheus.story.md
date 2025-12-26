---
id: "20251226_monitoring_prometheus"
difficulty: "medium"
tags: ["devops", "monitoring", "prometheus", "grafana"]
tech_stack: "Node.js, prom-client, Prometheus, Grafana"
---

# User Story
As a DevOps engineer, I want to implement application metrics and dashboards for observability.

# Context & Constraints
Add Prometheus metrics to Node.js application:

**Metrics to Collect:**
- HTTP request duration histogram
- Request count by endpoint and status
- Active connections gauge
- Business metrics (orders, users, etc.)

**Requirements:**
- /metrics endpoint for Prometheus scraping
- Custom histogram buckets for latency SLOs
- Labels for route, method, status
- Grafana dashboard template

**Technical Constraints:**
- Use prom-client library
- Follow Prometheus naming conventions
- Include Node.js runtime metrics
- Dashboard as code (JSON provisioning)

# Acceptance Criteria
- [ ] Implement /metrics endpoint with prom-client
- [ ] Add HTTP request duration histogram
- [ ] Create request counter with proper labels
- [ ] Export Grafana dashboard JSON
- [ ] Include SLO-based alerting rules
