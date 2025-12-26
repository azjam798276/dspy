---
id: "20251226_logging_elk"
difficulty: "medium"
tags: ["devops", "logging", "elk", "observability"]
tech_stack: "Node.js, Winston, Filebeat, Elasticsearch, Kibana"
---

# User Story
As a DevOps engineer, I want to implement structured logging with centralized log aggregation.

# Context & Constraints
Set up ELK stack integration:

**Logging Requirements:**
- Structured JSON logs with Winston
- Request ID correlation across services
- Log levels (debug, info, warn, error)
- Sensitive data redaction

**Stack:**
- Winston for Node.js logging
- Filebeat for log shipping
- Elasticsearch for storage
- Kibana for visualization

**Technical Constraints:**
- Logs must be JSON formatted
- Include trace ID from headers
- Redact PII (emails, tokens, passwords)
- Index pattern per environment

# Acceptance Criteria
- [ ] Configure Winston with JSON formatter
- [ ] Implement request ID middleware
- [ ] Create PII redaction transform
- [ ] Set up Filebeat configuration
- [ ] Design Kibana index pattern and dashboard
