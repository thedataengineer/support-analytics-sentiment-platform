"""
Database and application configuration
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://sentiment_user:sentiment_pass@localhost:5432/sentiment_db")

    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Elasticsearch settings
    elasticsearch_url: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

    # ML Service settings
    ml_service_url: str = os.getenv("ML_SERVICE_URL", "http://localhost:5001")

    # Ollama settings (use host.docker.internal for Docker containers)
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")

    # JWT settings
    secret_key: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Application settings
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Performance settings
    max_db_connections: int = int(os.getenv("MAX_DB_CONNECTIONS", "20"))
    db_connection_timeout: int = int(os.getenv("DB_CONNECTION_TIMEOUT", "30"))
    redis_cache_ttl: int = int(os.getenv("REDIS_CACHE_TTL", "3600"))  # 1 hour

    # File upload settings
    max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", "524288000"))  # 500MB
    allowed_extensions: set = {".csv"}

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
