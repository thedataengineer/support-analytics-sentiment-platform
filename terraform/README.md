# Terraform Local Infrastructure

This directory now contains Terraform configurations that provision the sentiment platform dependencies locally using Docker. It replaces the previous AWS-centric stack with a lightweight environment that mirrors the services expected by the backend.

## Provisioned Services

- **PostgreSQL (Docker)** – primary data store for authentication and sentiment entities
- **Redis (Docker)** – cache and Celery broker
- **ML Service (Docker)** – builds the `ml` worker image from this repository

All containers share a dedicated Docker network and expose their standard ports on the host for local development.

## Prerequisites

1. Terraform v1.5 or newer
2. Docker Engine running locally
3. Adequate disk space for Docker images and PostgreSQL volume

## Quick Start

```bash
# 1. Export secrets (at minimum the database password)
export TF_VAR_postgres_password="ChangeMe123!"

# 2. Navigate to the demo environment
cd terraform/environments/demo

# 3. Initialise providers
terraform init

# 4. Review the plan
terraform plan

# 5. Apply changes
terraform apply

# 6. Inspect connection info
terraform output
```

Outputs include the PostgreSQL connection string, Redis URL, and ML service base URL. Point the backend `.env` at these values.

## Cleanup

```bash
terraform destroy
```

This stops and removes the containers and deletes the PostgreSQL Docker volume. Back up any data you wish to keep before destroying the environment.
