variable "project_name" {
  description = "Project name used for resource prefixes"
  type        = string
  default     = "sentiment-platform"
}

variable "environment" {
  description = "Environment label"
  type        = string
  default     = "local"
}

variable "postgres_user" {
  description = "PostgreSQL username"
  type        = string
  default     = "sentiment_user"
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "postgres_db" {
  description = "PostgreSQL database name"
  type        = string
  default     = "sentiment_db"
}

variable "postgres_port" {
  description = "Host port for PostgreSQL"
  type        = number
  default     = 5432
}

variable "postgres_image" {
  description = "Docker image for PostgreSQL"
  type        = string
  default     = "postgres:16"
}

variable "redis_port" {
  description = "Host port for Redis"
  type        = number
  default     = 6379
}

variable "redis_image" {
  description = "Docker image for Redis"
  type        = string
  default     = "redis:7"
}

variable "ml_port" {
  description = "Host port for ML service"
  type        = number
  default     = 5001
}
