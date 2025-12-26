---
id: "20251226_terraform_infra"
difficulty: "hard"
tags: ["devops", "terraform", "iac", "aws"]
tech_stack: "Terraform, AWS, VPC, RDS, ECS"
---

# User Story
As a DevOps engineer, I want to define our AWS infrastructure as code using Terraform modules.

# Context & Constraints
Create Terraform configuration for:

**Infrastructure:**
- VPC with public/private subnets
- RDS PostgreSQL with encryption
- ECS Fargate cluster
- Application Load Balancer
- S3 bucket for assets

**Requirements:**
- Modular structure (one module per component)
- Remote state in S3 with DynamoDB locking
- Workspace support for environments
- Proper tagging for cost allocation

**Technical Constraints:**
- Use AWS provider v5+
- All resources must have tags
- Encrypt all data at rest
- No hardcoded values (use variables)

# Acceptance Criteria
- [ ] Create VPC module with proper CIDR allocation
- [ ] Implement RDS module with encryption and backups
- [ ] Configure ECS Fargate with task definitions
- [ ] Set up ALB with health checks
- [ ] Add remote backend configuration
