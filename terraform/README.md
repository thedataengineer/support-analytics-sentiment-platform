# Terraform AWS Infrastructure

This directory contains Terraform configurations to deploy the Sentiment Analysis Platform to AWS.

## Architecture

- **VPC**: 2 public subnets, 2 private subnets across 2 AZs
- **RDS PostgreSQL**: db.t4g.small with 20GB storage
- **ElastiCache Redis**: cache.t4g.micro
- **OpenSearch**: t3.small.search single-node
- **ECS Fargate**: Backend (2 tasks), ML Service (1 task)
- **ALB**: Application Load Balancer for ECS services
- **S3 + CloudFront**: Frontend static hosting
- **ECR**: Docker image repositories

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured (`aws configure`)
3. Terraform installed (v1.5+)
4. Docker for building images

## Quick Start

```bash
# Navigate to demo environment
cd terraform/environments/demo

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Deploy infrastructure
terraform apply

# Get outputs
terraform output
```

## Cost Estimate

Estimated monthly cost: **~$150-230/month** depending on usage.

See AWS_DEPLOYMENT.md for detailed cost breakdown and optimization strategies.

## Deployment Order

1. **Phase 1**: VPC, Security Groups
2. **Phase 2**: RDS, ElastiCache, OpenSearch
3. **Phase 3**: ECR, ECS Cluster
4. **Phase 4**: Build & push Docker images to ECR
5. **Phase 5**: ECS Services, ALB
6. **Phase 6**: S3, CloudFront

## Environment Variables

Set these before deploying:

```bash
export TF_VAR_db_password="<strong-password>"
export TF_VAR_jwt_secret="<random-secret>"
export AWS_REGION="us-east-1"
```

## Cleanup

```bash
# Destroy all resources
terraform destroy
```

**Warning**: This will delete all data. Export database before destroying.

