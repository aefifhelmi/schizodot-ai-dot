# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SchizoDot Backend"
    ENV: str = "local"

    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "schizodot-backend-storage"
    DYNAMO_TABLE: str = "SchizodotUsers"
    DYNAMO_TABLE_JOBS: str = "SchizodotJobs"

    # AWS Bedrock
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_ENABLE: bool = False
    BEDROCK_MODEL_ID: str = "anthropic.claude-v2"

    # Redis & Celery
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000"

    # Internal Services
    AI_PIPELINE_URL: str = "http://ai-pipeline:8001"

    # pydantic v2 config:
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

settings = Settings()
