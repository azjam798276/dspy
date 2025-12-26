---
id: "20251226_ci_pipeline_docker"
difficulty: "medium"
tags: ["devops", "ci-cd", "docker", "github-actions"]
tech_stack: "Docker, GitHub Actions, Node.js, npm"
---

# User Story
As a DevOps engineer, I want to implement a CI pipeline that builds, tests, and publishes Docker images on every push.

# Context & Constraints
Implement GitHub Actions workflow:

**Pipeline Stages:**
1. Install dependencies and cache
2. Run linting and unit tests
3. Build Docker image with multi-stage
4. Push to container registry
5. Deploy to staging (on main branch)

**Requirements:**
- Multi-stage Dockerfile for minimal image size
- Cache npm dependencies between runs
- Run tests in parallel where possible
- Tag images with commit SHA and branch name

**Technical Constraints:**
- Image size < 200MB
- Build time < 5 minutes
- Use GitHub Container Registry (ghcr.io)
- Secrets from GitHub Actions secrets

# Acceptance Criteria
- [ ] Create multi-stage Dockerfile optimized for size
- [ ] Implement GitHub Actions workflow with caching
- [ ] Add parallel test execution
- [ ] Configure registry push with proper tagging
- [ ] Add staging deployment step for main branch
