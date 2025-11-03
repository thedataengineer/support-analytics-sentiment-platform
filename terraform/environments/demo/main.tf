terraform {
  required_version = ">= 1.5.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# Shared network for all containers
resource "docker_network" "sentiment" {
  name = "${local.name_prefix}-net"
}

# PostgreSQL
resource "docker_volume" "postgres_data" {
  name = "${local.name_prefix}-postgres-data"
}

resource "docker_image" "postgres" {
  name         = var.postgres_image
  keep_locally = false
}

resource "docker_container" "postgres" {
  name  = "${local.name_prefix}-postgres"
  image = docker_image.postgres.image_id

  restart = "unless-stopped"

  networks_advanced {
    name = docker_network.sentiment.name
  }

  env = [
    "POSTGRES_DB=${var.postgres_db}",
    "POSTGRES_USER=${var.postgres_user}",
    "POSTGRES_PASSWORD=${var.postgres_password}",
  ]

  ports {
    internal = 5432
    external = var.postgres_port
  }

  volumes {
    volume_name    = docker_volume.postgres_data.name
    container_path = "/var/lib/postgresql/data"
  }

  healthcheck {
    test     = ["CMD-SHELL", "pg_isready -U ${var.postgres_user}"]
    interval = "10s"
    timeout  = "3s"
    retries  = 10
  }
}

# Redis
resource "docker_image" "redis" {
  name         = var.redis_image
  keep_locally = false
}

resource "docker_container" "redis" {
  name  = "${local.name_prefix}-redis"
  image = docker_image.redis.image_id

  restart = "unless-stopped"

  networks_advanced {
    name = docker_network.sentiment.name
  }

  ports {
    internal = 6379
    external = var.redis_port
  }
}

# ML service (Docker build from repo)
resource "docker_image" "ml_service" {
  name = "${local.name_prefix}-ml"
  build {
    context    = "${path.module}/../../../"
    dockerfile = "${path.module}/../../../ml/Dockerfile"
  }
  keep_locally = false
}

resource "docker_container" "ml_service" {
  name  = "${local.name_prefix}-ml"
  image = docker_image.ml_service.image_id

  restart = "unless-stopped"

  networks_advanced {
    name = docker_network.sentiment.name
  }

  ports {
    internal = 5001
    external = var.ml_port
  }
}

output "postgres_connection_string" {
  description = "Connection string for the PostgreSQL instance"
  value       = "postgresql://${var.postgres_user}:${var.postgres_password}@localhost:${var.postgres_port}/${var.postgres_db}"
  sensitive   = true
}

output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://localhost:${var.redis_port}/0"
}

output "ml_service_url" {
  description = "Base URL for the ML service"
  value       = "http://localhost:${var.ml_port}"
}
