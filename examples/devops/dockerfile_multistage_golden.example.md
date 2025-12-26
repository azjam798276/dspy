---
id: "dockerfile_multistage_golden"
tags: ["devops", "docker", "ci-cd"]
---

## Problem
Create optimized multi-stage Dockerfile for Node.js application.
- Minimize image size (< 200MB)
- Separate build and runtime stages
- Cache npm dependencies

## Solution
```dockerfile
# path: Dockerfile
# Stage 1: Build
FROM node:18-alpine AS builder
WORKDIR /app

# Copy package files first for caching
COPY package*.json ./
RUN npm ci --only=production

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Runtime
FROM node:18-alpine AS runtime
WORKDIR /app

# Security: Run as non-root
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Copy only production files
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/package.json ./

USER nodejs
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "dist/index.js"]
```

## Key Techniques
- Multi-stage build (builder → runtime)
- Alpine base for minimal size
- Non-root user for security
- Layer caching (package.json first)
- Built-in health check
