"""
Database and application configuration
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings (SQLite for user authentication only)
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./users.db")

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

    # Local storage settings
    data_root: str = os.getenv("DATA_ROOT", os.path.join(os.getcwd(), "data"))
    upload_dir: str = os.getenv("UPLOAD_DIR", os.path.join(os.getcwd(), "uploads"))
    duckdb_path: str = os.getenv("DUCKDB_PATH", os.path.join(data_root, "sentiment_platform.duckdb"))
    redis_cache_ttl: int = int(os.getenv("REDIS_CACHE_TTL", "3600"))  # 1 hour

    # File upload settings
    max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", "524288000"))  # 500MB
    allowed_extensions: set = {".csv", ".parquet"}

    # Email / reporting settings
    smtp_host: str | None = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str | None = os.getenv("SMTP_USERNAME")
    smtp_password: str | None = os.getenv("SMTP_PASSWORD")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    reports_from_email: str | None = os.getenv("REPORTS_FROM_EMAIL")
    reports_daily_hour: int = int(os.getenv("REPORTS_DAILY_HOUR", "8"))
    reports_daily_minute: int = int(os.getenv("REPORTS_DAILY_MINUTE", "0"))
    reports_weekly_day_of_week: str = os.getenv("REPORTS_WEEKLY_DAY_OF_WEEK", "mon")
    reports_weekly_hour: int = int(os.getenv("REPORTS_WEEKLY_HOUR", "8"))
    reports_weekly_minute: int = int(os.getenv("REPORTS_WEEKLY_MINUTE", "0"))

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
