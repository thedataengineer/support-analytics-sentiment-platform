# Terraform Infrastructure Setup Guide

## 🎯 Quick Summary

**Comprehensive Terraform infrastructure is being created for AWS deployment.**

### What's Included

1. **Complete Infrastructure as Code**
   - VPC with public/private subnets
   - RDS PostgreSQL database
   - ElastiCache Redis cluster
   - OpenSearch (Elasticsearch) domain
   - ECS Fargate cluster
   - Application Load Balancer
   - S3 + CloudFront for frontend
   - ECR repositories for Docker images

2. **Cost-Optimized Configuration**
   - Graviton2 instances (ARM) for RDS/ElastiCache
   - Burstable instances (t4g, t3)
   - Single-AZ for demo (Multi-AZ option available)
   - Estimated cost: $150-230/month

3. **Security Best Practices**
   - Private subnets for databases
   - Security groups with least privilege
   - IAM roles for ECS tasks
   - Secrets Manager for sensitive data
   - VPC endpoints to reduce NAT costs

## 📋 Deployment Steps

### Step 1: Prerequisites Setup

```bash
# Install Terraform (if not already installed)
brew install terraform  # macOS
# or
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform

# Verify installation
terraform version

# Configure AWS CLI
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region name: us-east-1
# Default output format: json
```

### Step 2: Set Environment Variables

```bash
# Required secrets
export TF_VAR_db_password="ChangeThisToStrongPassword123!"
export TF_VAR_jwt_secret=$(openssl rand -base64 32)
export AWS_REGION="us-east-1"

# Optional: Project naming
export TF_VAR_project_name="sentiment-platform"
export TF_VAR_environment="demo"
```

### Step 3: Initialize Terraform

```bash
cd terraform/environments/demo

# Initialize (download providers and modules)
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive
```

### Step 4: Review Infrastructure Plan

```bash
# Generate execution plan
terraform plan -out=tfplan

# Review the plan output carefully
# Verify resource counts and configurations
```

Expected resources to be created:
- VPC, Subnets, Route Tables, Internet Gateway, NAT Gateway
- Security Groups (5-7 groups)
- RDS PostgreSQL instance + subnet group
- ElastiCache Redis cluster + subnet group
- OpenSearch domain
- ECS Cluster, Task Definitions (2), Services (2)
- ALB, Target Groups, Listeners
- S3 Bucket, CloudFront Distribution
- ECR Repositories (2)
- IAM Roles, Policies
- Secrets Manager secrets

**Total resources: ~50-60 resources**

### Step 5: Deploy Infrastructure

```bash
# Apply the plan
terraform apply tfplan

# Or apply directly (will prompt for confirmation)
terraform apply

# Wait for completion (typically 15-20 minutes)
# OpenSearch takes the longest (~15 min)
```

### Step 6: Retrieve Outputs

```bash
# Get all outputs
terraform output

# Specific outputs
terraform output alb_dns_name
terraform output rds_endpoint
terraform output ecr_backend_repository_url
terraform output frontend_cloudfront_url
```

### Step 7: Build and Push Docker Images

```bash
# Get ECR login command
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(terraform output -raw ecr_backend_repository_url | cut -d'/' -f1)

# Build and push backend
cd ../../../backend
docker build -t sentiment-backend .
docker tag sentiment-backend:latest $(terraform output -raw ecr_backend_repository_url):latest
docker push $(terraform output -raw ecr_backend_repository_url):latest

# Build and push ML service
cd ../ml
docker build -t sentiment-ml .
docker tag sentiment-ml:latest $(terraform output -raw ecr_ml_repository_url):latest
docker push $(terraform output -raw ecr_ml_repository_url):latest
```

### Step 8: Deploy React Frontend

```bash
# Build React app
cd ../client
npm install
npm run build

# Sync to S3
aws s3 sync build/ s3://$(terraform output -raw frontend_bucket_name)/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

### Step 9: Run Database Migrations

```bash
# Get RDS endpoint
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)

# Update DATABASE_URL in ECS task definition or run migrations from local
export DATABASE_URL="postgresql://sentiment_user:$TF_VAR_db_password@$RDS_ENDPOINT:5432/sentiment_db"

# Run Alembic migrations
cd ../backend
alembic upgrade head
```

### Step 10: Verify Deployment

```bash
# Get ALB DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)

# Test health check
curl http://$ALB_DNS/health

# Test authentication
curl -X POST http://$ALB_DNS/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@example.com", "password": "password"}'

# Access frontend
echo "Frontend URL: https://$(terraform output -raw frontend_cloudfront_url)"
```

## 🔄 Update Deployment

To update infrastructure or application:

```bash
# Update Terraform code
terraform plan
terraform apply

# Update Docker images
# Rebuild and push as in Step 7
# ECS will automatically deploy new task definitions

# Update frontend
# Rebuild and sync to S3 as in Step 8
```

## 🧹 Cleanup

```bash
# Destroy all resources
terraform destroy

# Confirm by typing 'yes'
```

**Warning**: This will permanently delete:
- All data in RDS PostgreSQL
- All data in ElastiCache Redis
- All data in OpenSearch
- All files in S3
- All Docker images in ECR

**Recommendation**: Export/backup data before destroying.

## 📊 Monitoring

After deployment, set up monitoring:

```bash
# CloudWatch Dashboard (created automatically by Terraform)
echo "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=sentiment-platform-demo"

# View logs
aws logs tail /ecs/sentiment-backend --follow
aws logs tail /ecs/sentiment-ml --follow
```

## 🐛 Troubleshooting

### Issue: Terraform apply fails with "InsufficientCapacityException"
**Solution**: Change instance type or try different AZ

```hcl
# In variables.tf
variable "availability_zones" {
  default = ["us-east-1a", "us-east-1b"]  # Try different AZs
}
```

### Issue: ECS tasks not starting
**Check**:
1. ECR images exist and are accessible
2. IAM roles have correct permissions
3. Security groups allow outbound internet access
4. VPC has NAT gateway for private subnets

```bash
# Check ECS service events
aws ecs describe-services \
  --cluster sentiment-platform-demo \
  --services sentiment-backend \
  --query 'services[0].events[:5]'
```

### Issue: RDS connection timeout
**Check**:
1. Security group allows port 5432 from ECS security group
2. RDS is in correct subnets (private)
3. DATABASE_URL is correct in ECS task definition

### Issue: OpenSearch provisioning takes too long
**Note**: OpenSearch typically takes 15-20 minutes to provision. This is normal.

```bash
# Check status
aws opensearch describe-domain --domain-name sentiment-platform-demo
```

## 💡 Cost Optimization Tips

After deployment, to reduce costs:

1. **Stop ECS services when not in use**
   ```bash
   aws ecs update-service --cluster sentiment-platform-demo --service sentiment-backend --desired-count 0
   aws ecs update-service --cluster sentiment-platform-demo --service sentiment-ml --desired-count 0
   ```

2. **Use RDS scheduled start/stop** (manual via console)

3. **Enable CloudFront caching** (already configured with 1-hour TTL)

4. **Use S3 lifecycle policies** for old logs

5. **Set billing alerts**
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name billing-alert \
     --alarm-description "Alert when estimated charges exceed $200" \
     --metric-name EstimatedCharges \
     --namespace AWS/Billing \
     --statistic Maximum \
     --period 21600 \
     --threshold 200 \
     --comparison-operator GreaterThanThreshold
   ```

## 🔐 Security Checklist

- [ ] Rotate database password regularly
- [ ] Use AWS Secrets Manager for all secrets
- [ ] Enable CloudTrail for audit logging
- [ ] Set up AWS Config for compliance
- [ ] Enable VPC Flow Logs
- [ ] Use AWS WAF for ALB (optional, +$5/mo)
- [ ] Enable RDS automated backups
- [ ] Set up backup retention policies
- [ ] Use least-privilege IAM policies
- [ ] Enable MFA for AWS root account

## 📚 Next Steps

1. **Set up CI/CD** with GitHub Actions
2. **Configure custom domain** with Route53
3. **Enable SSL/TLS** with ACM certificates
4. **Set up monitoring** with CloudWatch/Datadog
5. **Configure auto-scaling** policies
6. **Enable backups** for RDS and OpenSearch
7. **Set up disaster recovery** plan

---

**Status**: Infrastructure code ready for deployment ✅

**Estimated deployment time**: 20-30 minutes

**Estimated cost**: $150-230/month

*For detailed architecture, see AWS_DEPLOYMENT.md*
