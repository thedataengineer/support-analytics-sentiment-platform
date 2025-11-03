# Terraform Setup Guide (Local Docker Stack)

This guide walks through provisioning the sentiment platform dependencies locally using Terraform and Docker. The configuration replaces the former AWS deployment and is optimised for development workstations.

---

## 1. Prerequisites

| Requirement | Notes |
|-------------|-------|
| Terraform ≥ 1.5 | `brew install terraform` (macOS) or download from HashiCorp |
| Docker Engine | Docker Desktop or equivalent CLI installation |
| Python tooling | Optional – only required if you intend to run the backend immediately after provisioning |

Ensure Docker is running before applying the Terraform plan.

---

## 2. Configure Secrets

Only the PostgreSQL password is required. Export it as an environment variable so Terraform can read it:

```bash
export TF_VAR_postgres_password="ChangeMe123!"
```

You can optionally override other variables (ports, usernames, database name) via environment variables or a custom `terraform.tfvars`.

---

## 3. Initialise and Plan

```bash
cd terraform/environments/demo

# Download the Docker provider
terraform init

# Review the execution plan
terraform plan
```

The plan should show creation of:

- Docker network (`*-net`)
- PostgreSQL container and volume
- Redis container
- ML service image build and container

---

## 4. Apply the Stack

```bash
terraform apply
```

Terraform builds the ML service image from the repository, starts the containers, and exposes:

- PostgreSQL: `localhost:${var.postgres_port}` (default 5432)
- Redis: `localhost:${var.redis_port}` (default 6379)
- ML service: `http://localhost:${var.ml_port}` (default 5001)

Grab the exact URLs via:

```bash
terraform output
```

Use the `postgres_connection_string`, `redis_url`, and `ml_service_url` outputs in your backend `.env`.

---

## 5. Verifying the Environment

After `terraform apply` completes:

```bash
# Check running containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Validate PostgreSQL
psql "$(terraform output -raw postgres_connection_string)" -c '\dt'

# Validate Redis
redis-cli -h 127.0.0.1 -p $(terraform output -raw redis_url | sed 's|redis://localhost:||;s|/0||') ping

# Validate ML service
curl "$(terraform output -raw ml_service_url)/health"
```

---

## 6. Integrating with the Backend

1. Copy the connection details into `backend/.env` (or export them directly).
2. Run the database initialisation script if needed:
   ```bash
   export DATABASE_URL="$(terraform output -raw postgres_connection_string)"
   python backend/scripts/run_sql_init.py
   ```
3. Start the backend (e.g. `uvicorn backend.main:app --reload` inside the virtualenv).

---

## 7. Updating & Destroying

- Apply configuration changes (e.g. port tweaks) by editing the variables and running `terraform apply` again.
- To stop everything and remove the containers/volume:

  ```bash
  terraform destroy
  ```

  **Note:** Destroying the stack deletes the PostgreSQL Docker volume. Back up data before running this command.

---

## 8. Troubleshooting

- **Port already in use**: Adjust `postgres_port`, `redis_port`, or `ml_port` in `terraform.tfvars`.
- **Docker build failures**: Ensure the repository root is accessible to Docker and that the `ml` service dependencies can be downloaded.
- **Provider errors**: Re-run `terraform init` after upgrading Terraform.

This local Terraform stack keeps the infrastructure aligned with the current data model without relying on AWS services.
