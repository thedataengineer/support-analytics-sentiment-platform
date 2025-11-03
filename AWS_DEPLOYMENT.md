# AWS Deployment Architecture - Support Analytics Sentiment Platform

**Repository:** https://github.com/thedataengineer/support-analytics-sentiment-platform

## 🎯 Architecture Overview

### Design Principles
1. **Low Cost**: Use serverless/managed services where possible, burstable instances, spot pricing
2. **High Performance**: CDN caching, connection pooling, optimized queries
3. **Scalability**: Auto-scaling for compute, managed services for data
4. **Security**: VPC isolation, IAM roles, secrets management

---

## 🏗️ AWS Architecture Diagram

```
Internet → CloudFront (CDN) → S3 (Static Frontend)
         ↓
      ALB (Application Load Balancer)
         ↓
    ECS Fargate Cluster (Backend API)
         ↓
    ┌────────────────────────────────────────┐
    │  RDS PostgreSQL (db.t4g.small)         │
    │  ElastiCache Redis (cache.t4g.micro)   │
    │  OpenSearch (t3.small.search)          │
    │  Bedrock (Claude 3 Haiku) for NLQ      │
    └────────────────────────────────────────┘
```

---

## 💰 Cost-Optimized Components

### 1. Frontend - S3 + CloudFront
**Service:** S3 + CloudFront CDN
**Estimated Cost:** ~$5-10/month
- S3: $0.023/GB storage + $0.09/GB transfer
- CloudFront: $0.085/GB (first 10TB)
- **Benefits:** Ultra-low latency, global distribution, 99.99% SLA

### 2. Backend API - ECS Fargate
**Service:** ECS Fargate (2 tasks @ 0.5 vCPU, 1GB RAM)
**Estimated Cost:** ~$20-30/month
- Fargate Pricing: $0.04048/vCPU/hour + $0.004445/GB/hour
- 2 tasks × 0.5 vCPU × 730 hours = $29.55
- Auto-scaling based on CPU/memory

### 3. Database - RDS PostgreSQL
**Service:** RDS PostgreSQL db.t4g.small (Graviton2)
**Estimated Cost:** ~$15-20/month
- Instance: $0.034/hour × 730 hours = $24.82
- Storage: 20GB SSD @ $0.115/GB = $2.30
- **Optimization:** Single-AZ for dev/demo, Multi-AZ for production

### 4. Cache - ElastiCache Redis
**Service:** ElastiCache Redis cache.t4g.micro
**Estimated Cost:** ~$12/month
- Instance: $0.017/hour × 730 hours = $12.41
- 1 node, 0.5GB memory
- **Benefits:** Sub-millisecond latency, connection pooling

### 5. Search - OpenSearch (Elasticsearch)
**Service:** OpenSearch t3.small.search (1 node)
**Estimated Cost:** ~$40/month
- Instance: $0.058/hour × 730 hours = $42.34
- 10GB EBS storage (included)
- **Optimization:** Single-node for demo, 3-node for production

### 6. ML Service - ECS Fargate
**Service:** ECS Fargate (1 task @ 1 vCPU, 2GB RAM)
**Estimated Cost:** ~$35/month
- 1 task × 1 vCPU × 730 hours = $29.55
- 2GB RAM × 730 hours = $6.49
- **Total:** ~$36

### 7. LLM/NLQ - AWS Bedrock (Claude 3 Haiku)
**Service:** Bedrock Claude 3 Haiku
**Estimated Cost:** ~$10-30/month (usage-based)
- Input: $0.25 per 1M tokens
- Output: $1.25 per 1M tokens
- **Alternative:** Self-hosted Llama on EC2 g5.xlarge (~$1.20/hour on-demand, $0.36/hour spot)
- **Recommendation:** Bedrock for demo (no infrastructure), EC2 spot for production

### 8. Message Queue - ElastiCache Redis (same instance)
**Service:** Shared with cache
**Estimated Cost:** Included above
- Celery uses Redis for both broker and backend

### 9. Load Balancer - ALB
**Service:** Application Load Balancer
**Estimated Cost:** ~$20/month
- $0.0225/hour × 730 hours = $16.43
- LCU charges minimal for demo

### 10. Networking - VPC, NAT
**Service:** VPC with NAT Gateway
**Estimated Cost:** ~$35/month
- NAT Gateway: $0.045/hour × 730 hours = $32.85
- Data processing: ~$0.045/GB
- **Optimization:** Use VPC Endpoints for S3/ECR to reduce NAT costs

---

## 📊 Total Estimated Monthly Cost

| Component | Monthly Cost |
|-----------|--------------|
| S3 + CloudFront | $10 |
| ECS Fargate (Backend) | $30 |
| ECS Fargate (ML) | $36 |
| RDS PostgreSQL | $27 |
| ElastiCache Redis | $12 |
| OpenSearch | $42 |
| AWS Bedrock (Haiku) | $20 |
| ALB | $20 |
| NAT Gateway | $35 |
| **Total** | **~$232/month** |

### Cost Optimization Strategies

**Immediate Savings (~$100/month):**
1. **Use Spot Instances for ECS:** Save 70% on compute (~$45 saved)
2. **RDS Reserved Instance (1 year):** Save 40% (~$10 saved)
3. **Reduce OpenSearch to dev tier:** t3.small.search → oss-dev (~$25 saved)
4. **Self-host LLM on EC2 Spot:** g5.xlarge spot (~$260/mo vs $20 Bedrock, net +$240 but unlimited queries)
5. **Use S3 Gateway Endpoint:** Eliminate NAT charges for S3 (~$10 saved)

**Production-Ready Cost (~$150-180/month):**
- Spot instances for non-critical workloads
- Reserved instances for RDS
- Bedrock for LLM (pay per use, no infra overhead)
- CloudFront caching (reduce origin requests)

---

## 🚀 Deployment Strategy

### Phase 1: Infrastructure Setup (Terraform)
1. Create VPC with public/private subnets
2. Set up RDS PostgreSQL with security groups
3. Create ElastiCache Redis cluster
4. Set up OpenSearch domain
5. Create ECS cluster and task definitions
6. Configure ALB with target groups
7. Set up S3 bucket for frontend with CloudFront

### Phase 2: Service Deployment
1. Push Docker images to ECR
2. Deploy backend/ML services to ECS
3. Upload React build to S3
4. Configure CloudFront distribution
5. Set up Route53 DNS (optional)

### Phase 3: Data Migration
1. Export PostgreSQL data from local
2. Import to RDS using pg_restore
3. Re-index Elasticsearch data from RDS
4. Verify data integrity

### Phase 4: Testing & Validation
1. Run E2E tests against AWS endpoints
2. Load testing with k6 or Locust
3. Verify RAG/NLQ with Bedrock
4. Monitor CloudWatch metrics

---

## 🔒 Security Best Practices

### Network Security
- Private subnets for RDS, Redis, OpenSearch
- Security groups with least privilege
- VPC endpoints for AWS services (S3, ECR, Secrets Manager)
- ALB with WAF for DDoS protection (optional, +$5/mo)

### Application Security
- Store secrets in AWS Secrets Manager
- Use IAM roles for ECS tasks (no hardcoded credentials)
- Enable CloudTrail for audit logging
- S3 bucket policies for CloudFront-only access

### Data Security
- RDS encryption at rest (KMS)
- ElastiCache encryption in transit
- OpenSearch encryption at rest + node-to-node TLS
- S3 bucket encryption (AES-256)

---

## 📈 Performance Optimizations

### Frontend
- CloudFront edge caching (TTL: 1 hour for static assets)
- Gzip compression enabled
- HTTP/2 and TLS 1.3
- Origin shield for high-traffic scenarios

### Backend
- ECS auto-scaling based on CPU (target: 70%)
- RDS connection pooling (SQLAlchemy pool_size=20)
- Redis for session/cache with TTL
- ALB sticky sessions for WebSocket support

### Database
- RDS Parameter Group tuning (shared_buffers, work_mem)
- Read replicas for analytics queries (optional, +$27/mo)
- Index optimization for common queries
- Vacuum/analyze scheduled maintenance

### Search
- OpenSearch index sharding (5 primary, 1 replica)
- Query caching enabled
- Field data cache optimization
- Bulk indexing for large datasets

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow
```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    - Build Docker image
    - Push to ECR
    - Update ECS service

  deploy-frontend:
    - Build React app
    - Upload to S3
    - Invalidate CloudFront cache

  run-migrations:
    - Run Alembic migrations on RDS
```

---

## 🎛️ Environment Variables (AWS Secrets Manager)

```
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/sentiment_db
REDIS_URL=redis://elasticache-endpoint:6379/0
ELASTICSEARCH_URL=https://opensearch-endpoint:443
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
ML_SERVICE_URL=http://ml-service.internal:5001
JWT_SECRET=<generated>
AWS_REGION=us-east-1
```

---

## 📝 Deployment Checklist

### Pre-Deployment
- [ ] AWS account with billing alerts set up
- [ ] IAM user with programmatic access
- [ ] Terraform installed locally
- [ ] AWS CLI configured
- [ ] Docker images tested locally

### Infrastructure
- [ ] VPC and subnets created
- [ ] RDS PostgreSQL provisioned
- [ ] ElastiCache Redis cluster running
- [ ] OpenSearch domain active
- [ ] ECS cluster created
- [ ] ALB configured with health checks
- [ ] S3 bucket for frontend created
- [ ] CloudFront distribution deployed

### Application
- [ ] Backend Docker image in ECR
- [ ] ML service Docker image in ECR
- [ ] ECS tasks running (2 backend, 1 ML)
- [ ] React app built and uploaded to S3
- [ ] CloudFront cache invalidated
- [ ] Environment variables in Secrets Manager

### Data
- [ ] Database schema migrated (Alembic)
- [ ] Sample data loaded
- [ ] Elasticsearch indices created
- [ ] Ticket data re-indexed

### Validation
- [ ] Frontend loads from CloudFront
- [ ] API health check passes
- [ ] Authentication works
- [ ] CSV upload and processing works
- [ ] NLQ returns intelligent responses
- [ ] Dashboards display data correctly

---

## 🎓 LLM Options Comparison

### Option 1: AWS Bedrock Claude 3 Haiku (Recommended for Demo)
**Pros:**
- No infrastructure management
- Pay-per-use pricing
- Instant availability
- Managed scaling
- High quality responses

**Cons:**
- Higher cost for high volume ($20-50/mo for demo, $200+ for production)
- API rate limits
- No model customization
- Data leaves your infrastructure

**Cost:** $0.25 per 1M input tokens, $1.25 per 1M output tokens

### Option 2: Self-Hosted Llama 2 70B on EC2 g5.xlarge Spot
**Pros:**
- Lower cost for high volume ($260/mo unlimited queries)
- Complete control and customization
- Data stays in your VPC
- No API rate limits

**Cons:**
- Requires GPU instance (g5.xlarge)
- Infrastructure management overhead
- Spot interruption risk (mitigate with Spot Fleet)
- Initial setup complexity

**Cost:** On-demand $1.20/hour (~$880/mo), Spot $0.36/hour (~$260/mo)

### Option 3: AWS SageMaker Jumpstart Llama 2
**Pros:**
- Managed MLOps platform
- Auto-scaling
- Model monitoring
- Easy deployment

**Cons:**
- Higher cost than EC2 spot
- Still requires ml.g5 instances
- More complex than Bedrock

**Cost:** Similar to EC2 but with SageMaker overhead (~$1.50/hour)

**Recommendation:**
- **Demo/POC:** Bedrock Claude 3 Haiku (fastest, simplest)
- **Production <1000 queries/day:** Bedrock Claude 3 Haiku
- **Production >1000 queries/day:** EC2 Spot g5.xlarge with Llama 2 70B

---

## 🔧 Alternative Architecture (Ultra Low-Cost)

For absolute minimal cost (~$50-80/month):

1. **Frontend:** S3 + CloudFront ($5)
2. **Backend:** EC2 t4g.small with Docker Compose ($10)
3. **Database:** RDS db.t4g.micro + GP2 storage ($15)
4. **Search:** OpenSearch OSS single-node dev ($0 if < 10GB, or $15/mo)
5. **LLM:** AWS Bedrock pay-per-use ($10-20)
6. **Total:** ~$50-65/month

**Trade-offs:**
- Single point of failure (EC2)
- Manual scaling
- No auto-recovery
- Suitable for demo/dev only

---

## 📚 Documentation & Support

### AWS Resources
- RDS: https://docs.aws.amazon.com/rds/
- ECS: https://docs.aws.amazon.com/ecs/
- OpenSearch: https://docs.aws.amazon.com/opensearch-service/
- Bedrock: https://docs.aws.amazon.com/bedrock/

### Monitoring
- CloudWatch Dashboards for all services
- CloudWatch Alarms for CPU, memory, disk
- CloudWatch Logs for application logs
- X-Ray for distributed tracing (optional)

### Estimated Setup Time
- Infrastructure (Terraform): 2-3 hours
- Application deployment: 1-2 hours
- Data migration: 1-2 hours
- Testing & validation: 2-3 hours
- **Total:** ~6-10 hours

---

## 🚀 Next Steps

1. Create Terraform modules for each component
2. Set up ECR repositories
3. Configure GitHub Actions for CI/CD
4. Deploy infrastructure
5. Migrate data
6. Run E2E tests on AWS
7. Set up monitoring and alerts

---

**Status:** Ready for AWS deployment! ✅

*Generated: 2025-11-03*
*Repository: https://github.com/thedataengineer/support-analytics-sentiment-platform*
